"""Step 7 — Upload (optional).

If a platform is enabled in config.upload AND its API key env var is set,
attempt to upload. Otherwise — the common case for local dev — just leave
video.mp4 + metadata.txt + thumbnail.png for the user to upload manually, per
spec: "If upload credentials exist: upload automatically. Otherwise: generate
files, user uploads manually."

Per spec: "If Upload fails → Keep generated files locally" — an upload
attempt failing (or a platform's Uploader still being NotImplementedError,
see Phase 8.4) is logged, never raised, and never deletes/moves the local
files this stage's exit status doesn't depend on the network call succeeding.
"""

import json
from datetime import datetime
from os import environ
from pathlib import Path

from generator.logging_setup import get_logger, stage_timer
from generator.metadata.thumbnail import generate_thumbnail
from generator.providers.uploader import get_uploader

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"

_CREDENTIAL_ENV = {
    "tiktok": "TIKTOK_API_KEY",
    "youtube": "YOUTUBE_API_KEY",
    "facebook": "FACEBOOK_API_KEY",
}

logger = get_logger("upload")


def _derive_run_id(video_path: Path, config: dict) -> str:
    # Prefer the run_id embedded in the video's own filename (video_<id>.mp4)
    # so the thumbnail pairs with whichever video was actually used — matters
    # for a standalone `python main.py upload` picking up an older video via
    # discover_existing_artifacts() rather than one just rendered this run.
    stem = video_path.stem
    if stem.startswith("video_"):
        return stem[len("video_"):]
    return config.get("_run_id") or datetime.now().strftime("%Y%m%d_%H%M%S")


def _attempt_upload(platform: str, video_path: Path, metadata_path: Path) -> None:
    env_var = _CREDENTIAL_ENV[platform]
    if not environ.get(env_var):
        logger.info("%s enabled but %s not set — skipping, upload manually", platform, env_var)
        return

    try:
        uploader = get_uploader(platform)
        uploader.upload(video_path, metadata_path)
        logger.info("%s upload succeeded", platform)
    except Exception as e:  # network/API/NotImplementedError — never fatal for this stage
        logger.warning("%s upload failed, files kept locally for manual upload: %s", platform, e)


def run(config: dict, artifacts: dict) -> Path:
    video_path: Path = artifacts["video"]
    metadata_path: Path = artifacts["metadata"]

    with stage_timer("upload") as ctx:
        upload_cfg = config.get("upload", {})
        for platform in _CREDENTIAL_ENV:
            if upload_cfg.get(platform):
                _attempt_upload(platform, video_path, metadata_path)

        output_files = [video_path, metadata_path]
        run_id = _derive_run_id(video_path, config)
        thumbnail_path = OUTPUT_DIR / f"thumbnail_{run_id}.png"
        try:
            story = json.loads(artifacts["story"].read_text(encoding="utf-8"))
            generate_thumbnail(video_path, story["title"], thumbnail_path)
            output_files.append(thumbnail_path)
        except Exception as e:
            logger.warning("Thumbnail generation failed, continuing without it: %s", e)

        ctx.output_files = output_files

    return video_path
