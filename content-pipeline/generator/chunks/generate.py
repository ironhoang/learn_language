"""Step 2 — Generate Learning Chunks.

Input: story.json (from Pipeline Manager's artifacts, per spec "No stage
should call another stage directly" — we read the file, not Story's in-memory
data). Output: output/json/chunks.json.

Note: unlike Story (spec: stop pipeline) or Audio (spec: retry), the spec has
no documented failure policy for this stage — chunks.json is a supplementary
content asset (keywords/patterns/phrase-breakdown), not an input any later
stage depends on. So an LLM chunk-boundary mistake degrades gracefully (falls
back to a simple word-count split for just the offending sentence) instead of
stopping the whole pipeline.
"""

import json
from pathlib import Path

import jsonschema

from generator.cache import cache_key, get_cached, save_cache
from generator.llm_json import parse_llm_json
from generator.logging_setup import get_logger, stage_timer
from generator.providers.llm import get_llm_provider
from generator.text_utils import split_sentences

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "chunks.md"
SCHEMA_PATH = Path(__file__).resolve().parent / "chunks.schema.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

logger = get_logger("chunks")


def _normalize(text: str) -> str:
    # Strip ALL whitespace (not just collapse it) — joining parts with " " to
    # compare against the source sentence must still match for scripts with
    # no inter-word spacing (Chinese), where a space-collapsed compare would
    # always mismatch even on a perfectly correct split.
    return "".join(text.split())


def _contains_cjk(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text)  # CJK Unified Ideographs


def _fallback_parts(sentence: str, group_size: int = 3) -> list[str]:
    if _contains_cjk(sentence):
        chars = list(sentence)
        return ["".join(chars[i:i + group_size]) for i in range(0, len(chars), group_size)] or [sentence]
    words = sentence.split()
    return [" ".join(words[i:i + group_size]) for i in range(0, len(words), group_size)] or [sentence]


def build_prompt(sentences: list[str], config: dict) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))
    return template.format(sentences=numbered, language=config["language"], level=config["level"])


def _reconcile_chunks(sentences: list[str], data: dict) -> None:
    """Mutates data['chunks'] in place: any entry whose parts don't reconstruct
    its sentence exactly (or whose sentence went missing) falls back to a
    naive word-count split, instead of failing the whole stage."""
    by_sentence = {_normalize(c["sentence"]): c for c in data["chunks"]}

    reconciled = []
    for sentence in sentences:
        entry = by_sentence.get(_normalize(sentence))
        if entry and _normalize(" ".join(entry["parts"])) == _normalize(sentence):
            reconciled.append({"sentence": sentence, "parts": entry["parts"]})
        else:
            logger.warning("Chunk mismatch for sentence, falling back to word-count split: %r", sentence)
            reconciled.append({"sentence": sentence, "parts": _fallback_parts(sentence)})

    data["chunks"] = reconciled


def run(config: dict, artifacts: dict) -> Path:
    story_path: Path = artifacts["story"]
    story = json.loads(story_path.read_text(encoding="utf-8"))
    sentences = split_sentences(story["paragraphs"])

    provider_name = config.get("llm", "mock")
    template_hash = cache_key(PROMPT_PATH.read_text(encoding="utf-8"))
    key = cache_key(story_path.read_text(encoding="utf-8"), template_hash)

    with stage_timer("chunks", provider=provider_name) as ctx:
        cached = get_cached("chunks", key)
        if cached:
            ctx.cache_hit = True
            data = json.loads(cached.read_text(encoding="utf-8"))
        else:
            prompt = build_prompt(sentences, config)
            llm = get_llm_provider(provider_name)
            raw = llm.generate(prompt, json_mode=True)
            try:
                data = parse_llm_json(raw)
                jsonschema.validate(data, _SCHEMA)
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                logger.error("Chunks generation failed — invalid output: %s\nRaw response:\n%s", e, raw)
                raise

            _reconcile_chunks(sentences, data)
            save_cache("chunks", key, data)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "chunks.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        ctx.output_files = [out_path]

    return out_path
