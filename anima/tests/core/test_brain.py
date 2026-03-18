import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from core.brain.engine import Brain
from core.brain.skill_loader import SkillLoader
from core.memory.store import MemoryStore
from core.models import Device, Sensor, DeviceCommand


class TestBrain:
    def test_build_context(self):
        brain = Brain.__new__(Brain)
        brain._skill_loader = SkillLoader(skills_dir="skills")
        brain._skill_loader.discover()

        device = Device(
            device_id="hum_01", name="Humidifier", adapter="miot",
            type="humidifier",
            sensors=[Sensor(name="humidity", unit="%", value=35)],
        )

        skill = brain._skill_loader.get_skill_for_device("humidifier")
        context = brain._build_prompt_context(
            skill=skill,
            device=device,
            user_memory={"preferences": "likes 55%", "history": [], "learned": ""},
        )
        assert "humidity" in context.lower()
        assert "35" in context

    def test_parse_llm_response_valid_json(self):
        brain = Brain.__new__(Brain)
        response = '{"action": "set_humidity", "params": {"value": 55}, "reason": "too dry"}'
        result = brain._parse_llm_response(response, "hum_01")
        assert result is not None
        assert result.action == "set_humidity"
        assert result.params["value"] == 55

    def test_parse_llm_response_with_markdown_fence(self):
        brain = Brain.__new__(Brain)
        response = '```json\n{"action": "turn_on", "params": {}, "reason": "test"}\n```'
        result = brain._parse_llm_response(response, "hum_01")
        assert result is not None
        assert result.action == "turn_on"

    def test_parse_llm_response_none_action(self):
        brain = Brain.__new__(Brain)
        response = '{"action": "none", "params": {}, "reason": "all good"}'
        result = brain._parse_llm_response(response, "hum_01")
        assert result is None

    def test_parse_llm_response_invalid(self):
        brain = Brain.__new__(Brain)
        result = brain._parse_llm_response("I don't know what to do", "hum_01")
        assert result is None
