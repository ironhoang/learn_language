"""Shared LLM-JSON-response parsing — used by every stage that asks an LLM
for a JSON object (story/chunks/metadata). Lives outside any stage package
for the same reason as text_utils.py/media_utils.py: it's a plain utility,
not stage-specific business logic.
"""

import json
import re

_CODE_FENCE_LEADING = re.compile(r"^```(?:json)?\n?")
_CODE_FENCE_TRAILING = re.compile(r"```$")

_SMART_QUOTES = str.maketrans({
    "“": '"',  # “
    "”": '"',  # ”
    "‘": "'",  # ‘
    "’": "'",  # ’
})


def strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    text = text.split("\n", 1)[1] if "\n" in text else ""
    text = _CODE_FENCE_TRAILING.sub("", text)
    return text.strip()


def parse_llm_json(raw: str) -> dict:
    """Strips a stray ```json code fence, then parses a JSON object out of an
    LLM response — tolerating "smart"/curly quotes used as string delimiters
    instead of straight ones.

    Real failure this handles: a DeepSeek response (Chinese-language story)
    closed one string with ” instead of " — invalid JSON, since that left the
    parser scanning past the intended end of the string into the next line's
    literal newline ("Invalid control character"). Retries once against a
    version with curly quotes normalized to straight ones; if that's STILL
    broken, lets the original JSONDecodeError surface so the caller's
    existing "log raw response + stop" handling still applies.
    """
    text = strip_code_fence(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text.translate(_SMART_QUOTES))
