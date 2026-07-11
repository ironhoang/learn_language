"""Abstract video renderer interface. FFmpegRenderer is the real implementation
per audio-tecnical-flow.md's "FFmpeg should perform the final rendering"."""

from abc import ABC, abstractmethod
from pathlib import Path


class VideoRenderer(ABC):
    @abstractmethod
    def render(self, audio_path: Path, subtitle_path: Path, video_config: dict, out_path: Path) -> Path:
        ...


class MockVideoRenderer(VideoRenderer):
    """Writes an empty placeholder file — used to verify pipeline wiring before FFmpegRenderer exists."""

    def render(self, audio_path: Path, subtitle_path: Path, video_config: dict, out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"")
        return out_path


_RENDERERS: dict[str, type[VideoRenderer]] = {
    "mock": MockVideoRenderer,
}


def _register_ffmpeg_renderer() -> None:
    # Lazy import to avoid a circular import (renderer_ffmpeg.py imports from
    # this module) — same pattern as tts.py's lazy edge-tts registration.
    if "ffmpeg" not in _RENDERERS:
        from generator.providers.renderer_ffmpeg import FFmpegRenderer

        _RENDERERS["ffmpeg"] = FFmpegRenderer


def get_renderer(name: str = "mock") -> VideoRenderer:
    _register_ffmpeg_renderer()
    try:
        cls = _RENDERERS[name]
    except KeyError:
        raise ValueError(f"Unknown renderer: {name!r}. Available: {list(_RENDERERS)}")
    return cls()
