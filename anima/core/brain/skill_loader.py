from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.models import SkillMeta

logger = logging.getLogger(__name__)


@dataclass
class LoadedSkill:
    meta: SkillMeta
    knowledge: str
    decide_prompt: str | None
    learn_prompt: str | None
    actions_module_path: Path | None
    path: Path

    @property
    def orchestrate_prompt(self) -> str | None:
        p = self.path / "prompts" / "orchestrate.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None


class SkillLoader:
    def __init__(self, skills_dir: str = "skills") -> None:
        self._dir = Path(skills_dir)
        self._cache: dict[str, LoadedSkill] = {}

    def discover(self) -> list[LoadedSkill]:
        skills = []
        if not self._dir.exists():
            logger.warning("Skills directory not found: %s", self._dir)
            return skills

        for skill_dir in sorted(self._dir.iterdir()):
            yaml_path = skill_dir / "skill.yaml"
            if not yaml_path.exists():
                continue

            try:
                skill = self._load_skill(skill_dir)
                skills.append(skill)
                for dt in skill.meta.device_types:
                    self._cache[dt] = skill
            except Exception:
                logger.exception("Failed to load skill from %s", skill_dir)

        logger.info("Loaded %d skills: %s", len(skills), [s.meta.name for s in skills])
        return skills

    def _load_skill(self, skill_dir: Path) -> LoadedSkill:
        # Load metadata
        with open(skill_dir / "skill.yaml", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        meta = SkillMeta(**raw)

        # Load knowledge
        knowledge_path = skill_dir / "knowledge.md"
        knowledge = knowledge_path.read_text(encoding="utf-8") if knowledge_path.exists() else ""

        # Load prompts
        decide_path = skill_dir / "prompts" / "decide.md"
        decide_prompt = decide_path.read_text(encoding="utf-8") if decide_path.exists() else None

        learn_path = skill_dir / "prompts" / "learn.md"
        learn_prompt = learn_path.read_text(encoding="utf-8") if learn_path.exists() else None

        # Actions module
        actions_path = skill_dir / "actions.py"

        return LoadedSkill(
            meta=meta,
            knowledge=knowledge,
            decide_prompt=decide_prompt,
            learn_prompt=learn_prompt,
            actions_module_path=actions_path if actions_path.exists() else None,
            path=skill_dir,
        )

    def get_skill_for_device(self, device_type: str) -> LoadedSkill | None:
        if not self._cache:
            self.discover()
        return self._cache.get(device_type)
