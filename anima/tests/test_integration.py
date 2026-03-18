"""
Integration test: verify the full pipeline works end-to-end.
Uses mock adapter (no real Xiaomi devices needed).
"""
import pytest
from unittest.mock import AsyncMock, patch

from core.events.bus import EventBus
from core.discovery import DiscoveryOrchestrator
from core.rules.engine import RulesEngine
from core.memory.store import MemoryStore
from core.brain.skill_loader import SkillLoader
from core.brain.engine import Brain
from core.models import Device, Sensor, Capability, Event, EventType, ActionResult
from adapters.base import BaseAdapter


class FakeHumidifierAdapter(BaseAdapter):
    name = "fake"

    def __init__(self):
        self.executed_commands = []

    async def discover(self):
        return [Device(
            device_id="fake_hum_01",
            name="Test Humidifier",
            adapter="fake",
            type="humidifier",
            capabilities=[
                Capability(name="set_humidity", params={"min": 30, "max": 80}),
                Capability(name="turn_on"),
                Capability(name="turn_off"),
            ],
            sensors=[
                Sensor(name="humidity", unit="%", value=25.0),
                Sensor(name="water_level", unit="%", value=80.0),
            ],
        )]

    async def subscribe(self, device):
        pass

    async def execute(self, device_id, action, params):
        self.executed_commands.append({"device_id": device_id, "action": action, "params": params})
        return ActionResult(device_id=device_id, action=action, success=True)


class TestIntegrationPipeline:
    async def test_rules_trigger_on_low_humidity(self, tmp_path):
        """Rules engine should auto-trigger when humidity < 20%."""
        bus = EventBus()
        adapter = FakeHumidifierAdapter()
        discovery = DiscoveryOrchestrator(bus=bus, adapters=[adapter])
        rules = RulesEngine()
        rules.load_defaults()

        # Discover devices
        await discovery.scan()
        assert len(discovery.devices) == 1

        # Simulate sensor update with emergency low humidity
        device = discovery.get_device("fake_hum_01")
        sensor_data = {"humidity": 15.0}

        # Rules should trigger
        commands = await rules.evaluate(device.type, sensor_data, device.device_id)
        assert len(commands) == 1
        assert commands[0].action == "turn_on"

        # Execute command
        result = await discovery.execute_command(
            commands[0].device_id, commands[0].action, commands[0].params,
        )
        assert result.success is True
        assert len(adapter.executed_commands) == 1

    async def test_skill_loader_finds_skills(self):
        """Verify all default skills are discoverable."""
        loader = SkillLoader(skills_dir="skills")
        skills = loader.discover()
        names = {s.meta.name for s in skills}
        assert "humidifier" in names
        assert "air_conditioner" in names
        assert "light" in names
        assert "coordinator" in names

    async def test_memory_round_trip(self, tmp_path):
        """Memory can write and read preferences + history."""
        store = MemoryStore(base_dir=str(tmp_path / "memory"))

        await store.update_preferences("default", "comfort.temperature", "24°C")
        prefs = await store.get_preferences("default")
        assert "24°C" in prefs

        await store.append_history("default", {
            "device_id": "test_01", "action": "turn_on", "reason": "test",
        })
        history = await store.get_history("default")
        assert len(history) == 1

    async def test_brain_parse_and_decide(self, tmp_path):
        """Brain can parse LLM responses and generate commands."""
        bus = EventBus()
        loader = SkillLoader(skills_dir="skills")
        loader.discover()
        memory = MemoryStore(base_dir=str(tmp_path / "memory"))

        brain = Brain(bus=bus, skill_loader=loader, memory=memory)

        # Test JSON parsing
        cmd = brain._parse_llm_response(
            '{"action": "set_humidity", "params": {"value": 55}, "reason": "too dry"}',
            "test_device",
        )
        assert cmd is not None
        assert cmd.action == "set_humidity"
        assert cmd.params["value"] == 55

    async def test_full_pipeline_with_mock_llm(self, tmp_path):
        """Full pipeline: discovery → sensor update → brain decision → execute."""
        bus = EventBus()
        adapter = FakeHumidifierAdapter()
        discovery = DiscoveryOrchestrator(bus=bus, adapters=[adapter])
        loader = SkillLoader(skills_dir="skills")
        loader.discover()
        memory = MemoryStore(base_dir=str(tmp_path / "memory"))
        rules = RulesEngine()
        rules.load_defaults()

        brain = Brain(bus=bus, skill_loader=loader, memory=memory)

        # Discover
        await discovery.scan()

        # Mock LLM — replace brain._llm with a mock object
        mock_llm = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = '{"action": "set_humidity", "params": {"value": 55}, "reason": "humidity 35% is below comfort zone"}'
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        brain._llm = mock_llm

        device = discovery.get_device("fake_hum_01")
        sensor_data = {"humidity": 35.0}

        # Rules won't trigger (35% > 20% threshold)
        rule_cmds = await rules.evaluate(device.type, sensor_data, device.device_id)
        assert len(rule_cmds) == 0

        # Brain should decide
        cmd = await brain.decide(device, sensor_data)
        assert cmd is not None
        assert cmd.action == "set_humidity"
        assert cmd.params["value"] == 55

        # Execute
        result = await discovery.execute_command(cmd.device_id, cmd.action, cmd.params)
        assert result.success is True

        # Verify history recorded
        history = await memory.get_history("default")
        assert len(history) == 1
        assert history[0]["action"] == "set_humidity"
