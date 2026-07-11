"""Shared helper for languages/<language>/levels.yaml — grounds the Story
prompt with what a level code actually means (vocabulary size, grammar scope)
instead of handing the LLM a bare code like "HSK2" with no context. Lives
outside any stage package since it's a plain data lookup, not stage logic.
"""

from pathlib import Path

import yaml

LANGUAGES_DIR = Path(__file__).resolve().parent.parent / "languages"


def get_level_description(language: str, level: str) -> str | None:
    levels_path = LANGUAGES_DIR / language.lower() / "levels.yaml"
    if not levels_path.exists():
        return None

    levels = yaml.safe_load(levels_path.read_text(encoding="utf-8")) or {}
    entry = levels.get(level)
    if not entry:
        return None
    return entry.get("description")
