"""Step 6 — Generate Metadata.

Input: story.json (title/language/level) + topic/level from config.
Output: output/metadata_<run_id>.txt (title, description, topic, level,
hashtags) — timestamped like video.mp4 so it stays paired with the video from
the same run instead of being overwritten by the next one.

Two prompt template files per audio-tecnical-flow.md's example structure
(prompts/metadata.md for title+description, prompts/hashtags.md for hashtags),
but combined into a single LLM call — same "don't call the LLM twice for one
step" reasoning as Phase 3's chunks+keywords call.
"""

import json
from datetime import datetime
from pathlib import Path

import jsonschema

from generator.cache import cache_key, get_cached, save_cache
from generator.llm_json import parse_llm_json
from generator.logging_setup import get_logger, stage_timer
from generator.providers.llm import get_llm_provider

METADATA_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "metadata.md"
HASHTAGS_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "hashtags.md"
SCHEMA_PATH = Path(__file__).resolve().parent / "metadata.schema.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"

_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
logger = get_logger("metadata")


def build_prompt(story: dict, config: dict) -> str:
    metadata_template = METADATA_PROMPT_PATH.read_text(encoding="utf-8")
    hashtags_template = HASHTAGS_PROMPT_PATH.read_text(encoding="utf-8")
    metadata_part = metadata_template.format(
        story_title=story["title"],
        language=config["language"],
        level=config["level"],
        topic=config["topic"],
    )
    return metadata_part + "\n" + hashtags_template


def format_metadata_txt(data: dict, config: dict) -> str:
    hashtags = "\n".join(data["hashtags"])
    return (
        f"Title\n\n{data['title']}\n\n"
        f"Description\n\n{data['description']}\n\n"
        f"Topic\n\n{config['topic']}\n\n"
        f"Level\n\n{config['level']}\n\n"
        f"Hashtags\n\n{hashtags}\n"
    )


def run(config: dict, artifacts: dict) -> Path:
    story_path: Path = artifacts["story"]
    story = json.loads(story_path.read_text(encoding="utf-8"))

    provider_name = config.get("llm", "mock")
    template_hash = cache_key(
        METADATA_PROMPT_PATH.read_text(encoding="utf-8"), HASHTAGS_PROMPT_PATH.read_text(encoding="utf-8")
    )
    key = cache_key(story_path.read_text(encoding="utf-8"), config["topic"], config["level"], template_hash)

    with stage_timer("metadata", provider=provider_name) as ctx:
        cached = get_cached("metadata", key)
        if cached:
            ctx.cache_hit = True
            data = json.loads(cached.read_text(encoding="utf-8"))
        else:
            prompt = build_prompt(story, config)
            llm = get_llm_provider(provider_name)
            raw = llm.generate(prompt, json_mode=True)
            try:
                data = parse_llm_json(raw)
                jsonschema.validate(data, _SCHEMA)
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                logger.error("Metadata generation failed — invalid output: %s\nRaw response:\n%s", e, raw)
                raise
            save_cache("metadata", key, data)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_id = config.get("_run_id") or datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / f"metadata_{run_id}.txt"
        out_path.write_text(format_metadata_txt(data, config), encoding="utf-8")
        ctx.output_files = [out_path]

    return out_path
