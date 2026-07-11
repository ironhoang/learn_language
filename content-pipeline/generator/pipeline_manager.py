"""Orchestrates the 7 pipeline stages in order.

This is the ONLY module allowed to import more than one stage — every stage
module (generator/<stage>/generate.py) reads its inputs from a file path handed
to it here and writes its own output file; stages never import each other.

Each stage exposes run(config, artifacts) -> Path. `artifacts` maps stage name
to its output file path so later stages can read whatever prior artifacts they
need without the manager hardcoding per-stage argument lists.
"""

from datetime import datetime
from pathlib import Path
from typing import Callable

from generator.logging_setup import get_logger
from generator.story import generate as story_stage
from generator.chunks import generate as chunks_stage
from generator.audio import generate as audio_stage
from generator.subtitle import generate as subtitle_stage
from generator.video import generate as video_stage
from generator.metadata import generate as metadata_stage
from generator.upload import run as upload_stage_module

logger = get_logger("pipeline")

StageRunner = Callable[[dict, dict], Path]

STAGES: list[tuple[str, StageRunner]] = [
    ("story", story_stage.run),
    ("chunks", chunks_stage.run),
    ("audio", audio_stage.run),
    ("subtitle", subtitle_stage.run),
    ("video", video_stage.run),
    ("metadata", metadata_stage.run),
    ("upload", upload_stage_module.run),
]

STAGE_NAMES = [name for name, _ in STAGES]

OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "output"

# Where each stage's artifact lands on disk, by convention — lets a standalone
# CLI subcommand (e.g. `python main.py audio`) find story.json from a
# previous run without needing to re-run Story first (full resume-from-any-
# point support lands in Phase 10; this is the minimal piece Phase 9 needs).
# story/chunks/audio/subtitle are intermediate, pipeline-internal artifacts —
# fixed filenames, overwritten each run, content-addressed caching already
# gives them stable identity. video/metadata (+ thumbnail, generated inside
# the upload stage) are the final publish-facing deliverables and carry a
# per-run timestamp in their filename instead, so multiple generated videos
# accumulate in output/ rather than overwriting each other.
KNOWN_OUTPUTS: dict[str, Path] = {
    "story": OUTPUT_ROOT / "json" / "story.json",
    "chunks": OUTPUT_ROOT / "json" / "chunks.json",
    "audio": OUTPUT_ROOT / "audio" / "audio.mp3",
    "audio_word_boundaries": OUTPUT_ROOT / "audio" / "word_boundaries.json",
    "subtitle": OUTPUT_ROOT / "json" / "subtitle.json",
}

# (glob pattern relative to OUTPUT_ROOT) for the timestamped deliverables —
# discovery picks the most recently modified match.
TIMESTAMPED_OUTPUTS: dict[str, str] = {
    "video": "videos/video_*.mp4",
    "metadata": "metadata_*.txt",
}


def _latest_match(pattern: str) -> Path | None:
    matches = list(OUTPUT_ROOT.glob(pattern))
    return max(matches, key=lambda p: p.stat().st_mtime) if matches else None


def discover_existing_artifacts() -> dict[str, Path]:
    found = {name: path for name, path in KNOWN_OUTPUTS.items() if path.exists()}
    for name, pattern in TIMESTAMPED_OUTPUTS.items():
        match = _latest_match(pattern)
        if match:
            found[name] = match
    return found


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class PipelineManager:
    def __init__(self, config: dict):
        # Shared per-run identifier so video.mp4/metadata.txt/thumbnail.png
        # from the SAME generate() call carry the same timestamp suffix —
        # stages read it back via config["_run_id"] rather than threading an
        # extra parameter through every run(config, artifacts) signature.
        config = dict(config)
        config.setdefault("_run_id", new_run_id())
        self.config = config
        self.artifacts: dict[str, Path] = {}

    def run_stage(self, name: str) -> Path:
        runner = dict(STAGES)[name]
        logger.info("=== stage: %s ===", name)
        path = runner(self.config, self.artifacts)
        self.artifacts[name] = path
        return path

    def run_all(self, stop_after: str | None = None) -> dict[str, Path]:
        for name, _ in STAGES:
            self.run_stage(name)
            if stop_after and name == stop_after:
                break
        return self.artifacts
