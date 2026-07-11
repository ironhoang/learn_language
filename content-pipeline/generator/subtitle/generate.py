"""Step 4 — Generate Subtitle Timeline.

Preferred: real word-level timestamps, read from word_boundaries.json
(populated by Phase 4's TTS provider when it exposes native per-word timing,
e.g. edge-tts). Fallback: sentence-level timestamps, estimated by allocating
the audio's duration across story.json's sentences proportional to their
length — used whenever the provider returned no word boundaries at all
(MockTTSProvider, or a future provider without per-word timing).
"""

import hashlib
import json
import re
from pathlib import Path

import jsonschema

from generator.cache import cache_key, get_cached, save_cache
from generator.logging_setup import get_logger, stage_timer
from generator.media_utils import probe_duration
from generator.text_utils import split_sentences

SCHEMA_PATH = Path(__file__).resolve().parent / "subtitle.schema.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "json"

_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
logger = get_logger("subtitle")

WORDS_PER_SECOND = 2.5  # same spoken-pace assumption used in prompts/story.md


_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)


def _comparable(text: str) -> str:
    # edge-tts word tokens carry NO punctuation at all (not just no trailing
    # sentence-ender — commas, etc. are stripped too), so comparing against a
    # sentence that still has ANY punctuation can never exact-match. First
    # attempt only stripped trailing .!? and still drifted on sentences with
    # an internal comma ("On Saturday, I will go..." — "Saturday," in the
    # source never matches token "Saturday"). Stripping every non-word
    # character on both sides is what actually made every comparison exact.
    return _NON_WORD.sub("", text).lower()


def _mark_sentence_ends(word_boundaries: list[dict], sentences: list[str]) -> list[dict]:
    """Flags the word ending each sentence with sentence_end=True, so the
    renderer can append a period there. Matches by accumulated word content
    against each sentence's text rather than by word COUNT, since a naive
    count can drift if tokenization doesn't split 1:1 with a whitespace split
    (already seen with Chinese in Phase 3's chunking). If content overshoots
    a sentence's length without an exact match (misalignment), the boundary
    is still forced at that word so one glitch doesn't desync every sentence
    after it — worst case is a missing/misplaced period, not a crash.
    """
    result = [dict(wb) for wb in word_boundaries]
    if not sentences:
        return result

    sentence_idx = 0
    accumulated = ""
    for wb in result:
        accumulated += wb["word"]
        target = _comparable(sentences[sentence_idx])
        acc_comparable = _comparable(accumulated)
        if acc_comparable == target or len(acc_comparable) >= len(target):
            wb["sentence_end"] = True
            sentence_idx += 1
            accumulated = ""
            if sentence_idx >= len(sentences):
                break
    return result


def fallback_sentence_timestamps(sentences: list[str], total_duration: float) -> list[dict]:
    weights = [len(s) for s in sentences] or [1]
    total_weight = sum(weights) or 1
    items = []
    t = 0.0
    for sentence, weight in zip(sentences, weights):
        dur = total_duration * (weight / total_weight)
        items.append({"sentence": sentence, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    return items


def run(config: dict, artifacts: dict) -> Path:
    audio_path: Path = artifacts["audio"]
    wb_path: Path | None = artifacts.get("audio_word_boundaries")
    audio_hash = hashlib.md5(audio_path.read_bytes()).hexdigest()
    key = cache_key(audio_hash)

    with stage_timer("subtitle") as ctx:
        cached = get_cached("subtitle", key)
        if cached:
            ctx.cache_hit = True
            data = json.loads(cached.read_text(encoding="utf-8"))
        else:
            word_boundaries = (
                json.loads(wb_path.read_text(encoding="utf-8")) if wb_path and wb_path.exists() else []
            )
            story = json.loads(artifacts["story"].read_text(encoding="utf-8"))
            sentences = split_sentences(story["paragraphs"])

            if word_boundaries:
                word_boundaries = _mark_sentence_ends(word_boundaries, sentences)
                data = [
                    {"word": wb["word"], "start": wb["start"], "end": wb["end"], **(
                        {"sentence_end": True} if wb.get("sentence_end") else {}
                    )}
                    for wb in word_boundaries
                ]
            else:
                logger.warning("No word-level boundaries available — falling back to sentence-level timestamps")
                duration = probe_duration(audio_path)
                if duration is None:
                    logger.warning("ffprobe could not read duration of %s", audio_path)
                    total_words = sum(len(s.split()) for s in sentences) or 1
                    duration = total_words / WORDS_PER_SECOND
                data = fallback_sentence_timestamps(sentences, duration)

            jsonschema.validate(data, _SCHEMA)
            save_cache("subtitle", key, data)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "subtitle.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        ctx.output_files = [out_path]

    return out_path
