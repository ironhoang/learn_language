"""Step 5 — Render Video.

Input: audio.mp3, subtitle.json (per spec — not story.json/chunks.json).
Output: output/videos/video_<run_id>.mp4 — timestamped per run (unlike the
intermediate story/chunks/audio/subtitle artifacts) so multiple generated
videos accumulate in output/ instead of overwriting each other.

Cache key covers only audio + subtitle + video-config, so changing subtitle
style (e.g. font_size) re-renders the video without touching story/audio —
per spec: "Changing only subtitle style should not regenerate story or audio."
Note: the underlying render is still content-addressed in cache/video/ — a
repeat run with identical inputs just copies the cached bytes into a freshly
timestamped output filename rather than re-rendering.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from generator.cache import cache_key, get_cached, save_cache
from generator.logging_setup import stage_timer
from generator.providers.renderer import get_renderer

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "videos"


def run(config: dict, artifacts: dict) -> Path:
    audio_path: Path = artifacts["audio"]
    subtitle_path: Path = artifacts["subtitle"]

    video_config = dict(config.get("video", {}))
    video_config["show_overlay"] = video_config.get("show_overlay", False)
    video_config["topic"] = config.get("topic", "")
    video_config["level"] = config.get("level", "")
    video_config["language"] = config.get("language", "")

    renderer_name = config.get("renderer", "ffmpeg")

    audio_hash = hashlib.md5(audio_path.read_bytes()).hexdigest()
    subtitle_hash = hashlib.md5(subtitle_path.read_bytes()).hexdigest()
    config_hash = cache_key(json.dumps(video_config, sort_keys=True))
    key = cache_key(audio_hash, subtitle_hash, config_hash, renderer_name)

    with stage_timer("video", provider=renderer_name) as ctx:
        cached = get_cached("video", key, suffix=".mp4")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_id = config.get("_run_id") or datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / f"video_{run_id}.mp4"

        if cached:
            ctx.cache_hit = True
            out_path.write_bytes(cached.read_bytes())
        else:
            renderer = get_renderer(renderer_name)
            renderer.render(audio_path, subtitle_path, video_config, out_path)
            save_cache("video", key, out_path.read_bytes(), suffix=".mp4")

        ctx.output_files = [out_path]

    return out_path
