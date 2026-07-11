"""edge-tts implementation of TTSProvider — free, no API key required.

Requests boundary="WordBoundary" so we get real per-word timestamps for free;
Phase 5 (subtitle timeline) prefers these over falling back to sentence-level
estimates.
"""

import asyncio
from pathlib import Path

import edge_tts

from generator.providers.tts import TTSProvider, TTSResult, WordBoundary

_VOICE_MAP = {
    ("english", "male"): "en-US-GuyNeural",
    ("english", "female"): "en-US-AriaNeural",
    ("chinese", "male"): "zh-CN-YunxiNeural",
    ("chinese", "female"): "zh-CN-XiaoxiaoNeural",
    ("vietnamese", "male"): "vi-VN-NamMinhNeural",
    ("vietnamese", "female"): "vi-VN-HoaiMyNeural",
}


def resolve_voice(language: str, voice: str) -> str:
    key = (language.lower(), voice.lower())
    try:
        return _VOICE_MAP[key]
    except KeyError:
        raise ValueError(
            f"No edge-tts voice mapped for language={language!r} voice={voice!r}. "
            f"Available: {list(_VOICE_MAP)}"
        )


async def _synthesize_async(text: str, voice_code: str, out_path: Path, rate: str = "+0%") -> list[WordBoundary]:
    communicate = edge_tts.Communicate(text, voice_code, rate=rate, boundary="WordBoundary")
    boundaries: list[WordBoundary] = []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                end = (chunk["offset"] + chunk["duration"]) / 10_000_000
                boundaries.append(WordBoundary(word=chunk["text"], start=start, end=end))
    return boundaries


class EdgeTTSProvider(TTSProvider):
    """`voice` must already be a concrete edge-tts voice code — resolve it
    with resolve_voice(language, "male"/"female") before calling synthesize()."""

    def synthesize(self, text: str, voice: str, out_path: Path, rate: str = "+0%") -> TTSResult:
        boundaries = asyncio.run(_synthesize_async(text, voice, out_path, rate))
        return TTSResult(audio_path=out_path, word_boundaries=boundaries)
