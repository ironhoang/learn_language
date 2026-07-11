"""Abstract TTS provider interface.

TTSResult carries word_boundaries when a provider exposes native per-word
timestamps (e.g. edge-tts's SubMaker, wired in Phase 4) — Phase 5 (subtitle
timeline) prefers this over falling back to sentence-level estimates.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WordBoundary:
    word: str
    start: float  # seconds
    end: float  # seconds


@dataclass
class TTSResult:
    audio_path: Path
    word_boundaries: list[WordBoundary] = field(default_factory=list)


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, voice: str, out_path: Path, rate: str = "+0%") -> TTSResult:
        ...


class MockTTSProvider(TTSProvider):
    """Writes an empty placeholder file — used to verify pipeline wiring before real providers exist."""

    def synthesize(self, text: str, voice: str, out_path: Path, rate: str = "+0%") -> TTSResult:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"")
        return TTSResult(audio_path=out_path, word_boundaries=[])


_PROVIDERS: dict[str, type[TTSProvider]] = {
    "mock": MockTTSProvider,
}


def _register_edge_provider() -> None:
    # Lazy import to avoid a circular import (tts_edge.py imports from this
    # module) — mirrors the lazy `from google import genai` pattern in llm.py.
    if "edge" not in _PROVIDERS:
        from generator.providers.tts_edge import EdgeTTSProvider

        _PROVIDERS["edge"] = EdgeTTSProvider


def _register_gemini_provider() -> None:
    if "gemini" not in _PROVIDERS:
        from generator.providers.tts_gemini import GeminiTTSProvider

        _PROVIDERS["gemini"] = GeminiTTSProvider


def get_tts_provider(name: str) -> TTSProvider:
    _register_edge_provider()
    _register_gemini_provider()
    try:
        cls = _PROVIDERS[name]
    except KeyError:
        raise ValueError(f"Unknown TTS provider: {name!r}. Available: {list(_PROVIDERS)}")
    return cls()
