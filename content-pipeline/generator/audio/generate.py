"""Step 3 — Generate Audio.

Input: story.json (per spec, not chunks.json). Output: output/audio/audio.mp3
+ output/audio/word_boundaries.json (per-word timestamps when the provider
supports them — consumed by Phase 5's subtitle stage via the artifacts dict,
same file-based contract as every other artifact).

Per spec: "If Audio generation fails → Retry" (unlike Story's stop-the-pipeline
policy) — retries a few times with the same 0.5-2.0s randomized delay this
project already uses between TTS calls elsewhere (scripts/generate_audio.py),
then lets the error surface if still failing after the last attempt.
"""

import json
import random
import time
from dataclasses import asdict
from pathlib import Path

from generator.cache import cache_key, get_cached, save_cache
from generator.logging_setup import get_logger, stage_timer
from generator.providers.tts import get_tts_provider

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "audio"

MAX_RETRIES = 3
DELAY_RANGE = (0.5, 2.0)

logger = get_logger("audio")


def _resolve_voice(provider_name: str, language: str, voice: str) -> str:
    if provider_name == "edge":
        from generator.providers.tts_edge import resolve_voice

        return resolve_voice(language, voice)
    return voice  # mock / future providers: pass through as-is


def _resolve_rate(config: dict) -> str:
    # Per-language playback rate override — e.g. Chinese speech from edge-tts
    # reads noticeably faster than the same neural voice in English, so the
    # default here slows it to 0.75x (edge-tts rate is a relative %, negative
    # = slower) unless config.yaml's tts_rate overrides it.
    return config.get("tts_rate", {}).get(config["language"].lower(), "+0%")


def _story_text(story: dict) -> str:
    return " ".join(story["paragraphs"])


def _synthesize_with_retry(tts, text: str, voice_code: str, out_path: Path, rate: str):
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return tts.synthesize(text, voice_code, out_path, rate)
        except Exception as e:  # network/provider errors — worth retrying
            last_exc = e
            logger.warning("TTS attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(random.uniform(*DELAY_RANGE))
    logger.error("TTS failed after %d attempts: %s", MAX_RETRIES, last_exc)
    raise last_exc


def run(config: dict, artifacts: dict) -> Path:
    story_path: Path = artifacts["story"]
    story = json.loads(story_path.read_text(encoding="utf-8"))
    text = _story_text(story)

    provider_name = config.get("tts", "mock")
    voice_code = _resolve_voice(provider_name, config["language"], config.get("voice", "female"))
    rate = _resolve_rate(config)
    key = cache_key(text, voice_code, provider_name, rate)

    with stage_timer("audio", provider=provider_name) as ctx:
        cached_audio = get_cached("audio", key, suffix=".mp3")
        cached_wb = get_cached("audio", key, suffix=".wb.json")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "audio.mp3"

        if cached_audio:
            ctx.cache_hit = True
            out_path.write_bytes(cached_audio.read_bytes())
            wb_data = json.loads(cached_wb.read_text(encoding="utf-8")) if cached_wb else []
        else:
            tts = get_tts_provider(provider_name)
            result = _synthesize_with_retry(tts, text, voice_code, out_path, rate)
            wb_data = [asdict(wb) for wb in result.word_boundaries]
            save_cache("audio", key, out_path.read_bytes(), suffix=".mp3")
            save_cache("audio", key, json.dumps(wb_data), suffix=".wb.json")

        wb_path = OUTPUT_DIR / "word_boundaries.json"
        wb_path.write_text(json.dumps(wb_data, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts["audio_word_boundaries"] = wb_path
        ctx.output_files = [out_path, wb_path]

    return out_path
