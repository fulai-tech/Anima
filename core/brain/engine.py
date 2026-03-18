from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_openai import ChatOpenAI

from core.brain.skill_loader import SkillLoader, LoadedSkill
from core.config import settings
from core.events.bus import EventBus
from core.memory.store import MemoryStore
from core.models import Device, DeviceCommand, Event, EventType

logger = logging.getLogger(__name__)


class Brain:
    def __init__(
        self,
        bus: EventBus,
        skill_loader: SkillLoader,
        memory: MemoryStore,
    ) -> None:
        self._bus = bus
        self._skill_loader = skill_loader
        self._memory = memory
        self._llm = ChatOpenAI(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url or None,
            temperature=0.3,
            max_tokens=1024,
        )

    async def decide(self, device: Device, sensor_data: dict[str, Any]) -> DeviceCommand | None:
        skill = self._skill_loader.get_skill_for_device(device.type)
        if not skill or not skill.decide_prompt:
            logger.debug("No skill found for device type: %s", device.type)
            return None

        try:
            user_memory = await self._memory.get_full_context()
            prompt = self._build_prompt_context(skill, device, user_memory)

            response = await self._llm.ainvoke(prompt)
            content = response.content

            command = self._parse_llm_response(content, device.device_id)
            if command:
                logger.info(
                    "Brain decision: %s → %s (reason: %s)",
                    device.device_id, command.action, command.reason,
                )
                # Record to history
                await self._memory.append_history("default", {
                    "device_id": device.device_id,
                    "device_type": device.type,
                    "sensor_data": sensor_data,
                    "action": command.action,
                    "params": command.params,
                    "reason": command.reason,
                })
            return command

        except Exception:
            logger.exception("Brain decision failed for %s", device.device_id)
            return None

    async def coordinate(self, devices: list[Device], environment: dict) -> list[DeviceCommand]:
        skill = self._skill_loader.get_skill_for_device("coordinator")
        if not skill or not skill.orchestrate_prompt:
            return []

        try:
            user_memory = await self._memory.get_full_context()
            prompt = skill.orchestrate_prompt.format(
                devices=json.dumps([d.model_dump() for d in devices], default=str, indent=2),
                environment=json.dumps(environment, indent=2),
                recent_actions=json.dumps(user_memory.get("history", [])[-10:], indent=2),
                user_preferences=user_memory.get("preferences", ""),
                knowledge=skill.knowledge,
            )

            response = await self._llm.ainvoke(prompt)
            content = response.content

            # Parse array of actions
            json_str = self._extract_json(content)
            if not json_str:
                return []
            actions = json.loads(json_str)
            if not isinstance(actions, list):
                return []

            commands = []
            for a in actions:
                cmd = DeviceCommand(
                    device_id=a["device_id"],
                    action=a["action"],
                    params=a.get("params", {}),
                    source="brain",
                    reason=a.get("reason", "coordinator"),
                )
                commands.append(cmd)
            return commands

        except Exception:
            logger.exception("Coordination failed")
            return []

    async def learn_preferences(self, user_id: str = "default") -> None:
        """Periodic learning: review history and update user profile."""
        skill_types = ["humidifier", "air_conditioner", "light"]

        for skill_type in skill_types:
            skill = self._skill_loader.get_skill_for_device(skill_type)
            if not skill or not skill.learn_prompt:
                continue

            try:
                history = await self._memory.get_history(user_id, limit=100)
                relevant = [h for h in history if h.get("device_type") == skill_type]
                if len(relevant) < 5:
                    continue

                current_profile = await self._memory.get_learned(user_id)
                prompt = skill.learn_prompt.format(
                    history=json.dumps(relevant[-50:], indent=2),
                    current_profile=current_profile or "(no profile yet)",
                )
                response = await self._llm.ainvoke(prompt)
                await self._memory.update_learned(user_id, response.content)
                logger.info("Updated learned profile for %s/%s", user_id, skill_type)

            except Exception:
                logger.exception("Learning failed for skill %s", skill_type)

    def _build_prompt_context(
        self,
        skill: LoadedSkill,
        device: Device,
        user_memory: dict[str, Any],
    ) -> str:
        sensor_summary = {s.name: f"{s.value} {s.unit}" for s in device.sensors if s.value is not None}
        caps_summary = [
            {"name": c.name, **c.params} for c in device.capabilities
        ]

        return skill.decide_prompt.format(
            current_data=json.dumps(sensor_summary, indent=2),
            capabilities=json.dumps(caps_summary, indent=2),
            user_preferences=user_memory.get("preferences", ""),
            recent_history=json.dumps(user_memory.get("history", [])[-5:], indent=2),
            knowledge=skill.knowledge,
        )

    def _parse_llm_response(self, content: str, device_id: str) -> DeviceCommand | None:
        json_str = self._extract_json(content)
        if not json_str:
            logger.warning("Could not extract JSON from LLM response")
            return None

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in LLM response: %s", json_str[:200])
            return None

        action = data.get("action", "none")
        if action == "none":
            return None

        return DeviceCommand(
            device_id=device_id,
            action=action,
            params=data.get("params", {}),
            source="brain",
            reason=data.get("reason", ""),
        )

    @staticmethod
    def _extract_json(text: str) -> str | None:
        # Try to find JSON in markdown code fence
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try to find raw JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)

        # Try to find raw JSON array
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return match.group(0)

        return None
