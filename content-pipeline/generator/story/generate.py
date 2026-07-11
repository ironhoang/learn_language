"""Step 1 — Generate Story.

Input: language, level, topic, duration (from config).
Output: output/json/story.json — {title, language, level, paragraphs[]}.

Per spec: if this stage fails, the pipeline must stop — we deliberately let
JSON/schema errors propagate (after logging a clear message) instead of
swallowing them, so Pipeline Manager halts before Chunks/Audio/etc. run.
"""

import json
from pathlib import Path

import jsonschema

from generator.cache import cache_key, get_cached, save_cache
from generator.languages import get_level_description
from generator.llm_json import parse_llm_json
from generator.logging_setup import get_logger, stage_timer
from generator.providers.llm import get_llm_provider

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "story.md"
SCHEMA_PATH = Path(__file__).resolve().parent / "story.schema.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
logger = get_logger("story")


def build_prompt(config: dict) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    description = get_level_description(config["language"], config["level"])
    return template.format(
        language=config["language"],
        level=config["level"],
        level_description=f" ({description})" if description else "",
        topic=config["topic"],
        duration=config["duration"],
    )


def run(config: dict, artifacts: dict) -> Path:
    provider_name = config.get("llm", "mock")
    # Key off the fully-built prompt text itself (template + level description
    # + config values all folded in) rather than enumerating each input
    # separately — a levels.yaml edit or template change busts the cache the
    # same way a --topic change would, with no risk of forgetting a component.
    prompt = build_prompt(config)
    key = cache_key(prompt)

    with stage_timer("story", provider=provider_name) as ctx:
        cached = get_cached("story", key)
        if cached:
            ctx.cache_hit = True
            data = json.loads(cached.read_text(encoding="utf-8"))
        else:
            llm = get_llm_provider(provider_name)
            raw = llm.generate(prompt, json_mode=True)
            try:
                data = parse_llm_json(raw)
                jsonschema.validate(data, _SCHEMA)
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                logger.error("Story generation failed — invalid output: %s\nRaw response:\n%s", e, raw)
                raise
            save_cache("story", key, data)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "story.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        ctx.output_files = [out_path]

    return out_path
