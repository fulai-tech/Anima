from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn

from core.api.routes import create_app
from core.brain.engine import Brain
from core.brain.skill_loader import SkillLoader
from core.cli import interactive_cli
from core.config import settings
from core.discovery import DiscoveryOrchestrator
from core.events.bus import EventBus
from core.memory.store import MemoryStore
from core.mqtt import MQTTClient
from core.rules.engine import RulesEngine
from core.scheduler.scheduler import Scheduler
from core.models import Event, EventType

# Adapters
from adapters.miot.adapter import MIoTAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("anima")


class Anima:
    def __init__(self) -> None:
        # Core modules
        self.bus = EventBus()
        self.mqtt = MQTTClient()
        self.memory = MemoryStore(base_dir=f"{settings.data_dir}/memory")
        self.rules = RulesEngine()
        self.skill_loader = SkillLoader(skills_dir=settings.skills_dir)
        self.brain = Brain(bus=self.bus, skill_loader=self.skill_loader, memory=self.memory)
        self.scheduler = Scheduler()

        # Adapters
        adapters = [MIoTAdapter()]
        self.discovery = DiscoveryOrchestrator(bus=self.bus, adapters=adapters)

    async def start(self, mode: str = "full") -> None:
        logger.info("Starting Anima v0.1 — Make Every Hardware Intelligent")

        # Load skills
        self.skill_loader.discover()

        # Load default rules
        self.rules.load_defaults()

        # Wire up event handlers
        self.bus.subscribe(EventType.SENSOR_UPDATED, self._on_sensor_update)

        # Initial device scan
        logger.info("Scanning for devices...")
        await self.discovery.scan()
        logger.info("Found %d device(s)", len(self.discovery.devices))

        # Setup scheduled jobs
        self.scheduler.add_job("device_scan", self.discovery.scan, interval_seconds=300)
        self.scheduler.add_job(
            "learn_preferences",
            lambda: self.brain.learn_preferences(),
            interval_seconds=86400,  # daily
        )

        if mode == "cli":
            # Run CLI mode
            scheduler_task = asyncio.create_task(self.scheduler.start())
            await interactive_cli(self.discovery, self.brain)
            self.scheduler.stop()
            scheduler_task.cancel()

        elif mode == "full":
            # Run API server + scheduler
            app_state = {
                "discovery": self.discovery,
                "brain": self.brain,
                "memory": self.memory,
                "bus": self.bus,
            }
            app = create_app(app_state)

            config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
            server = uvicorn.Server(config)

            await asyncio.gather(
                server.serve(),
                self.scheduler.start(),
            )

    async def _on_sensor_update(self, event: Event) -> None:
        device_id = event.device_id
        if not device_id:
            return

        device = self.discovery.get_device(device_id)
        if not device:
            return

        sensor_data = event.data

        # Update cached sensor values
        self.discovery.update_device_sensors(device_id, sensor_data)

        # Fast path: rules engine
        rule_commands = await self.rules.evaluate(device.type, sensor_data, device_id)
        for cmd in rule_commands:
            await self.discovery.execute_command(cmd.device_id, cmd.action, cmd.params)

        # Slow path: LLM brain (only if rules didn't handle it)
        if not rule_commands:
            command = await self.brain.decide(device, sensor_data)
            if command:
                await self.discovery.execute_command(command.device_id, command.action, command.params)


def cli_entry():
    import argparse
    parser = argparse.ArgumentParser(description="Anima — Make Every Hardware Intelligent")
    parser.add_argument("--mode", choices=["full", "cli"], default="full",
                        help="Run mode: 'full' (API + scheduler) or 'cli' (interactive)")
    args = parser.parse_args()

    anima = Anima()
    try:
        asyncio.run(anima.start(mode=args.mode))
    except KeyboardInterrupt:
        logger.info("Anima stopped.")


if __name__ == "__main__":
    cli_entry()
