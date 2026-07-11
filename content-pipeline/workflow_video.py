#!/usr/bin/env python3
"""Generate short vertical videos from an EXISTING workflows/<id>/lesson.json
(the English Workflow for AI Engineers system), instead of content-pipeline's
own story-generation path. Reuses the same rendering machinery (ASS subtitle
scroll/static, gradient background, ffmpeg) since a workflow's chunks/recall/
conversation turns already have real spoken audio + text — no LLM/TTS call
needed for those, just download + concatenate + render.

Invoked via ../scripts/generate_workflow_video.py (a thin wrapper that runs
this under content-pipeline's venv, since this needs edge-tts/pypinyin/ffmpeg
that scripts/'s environment doesn't have installed).

Kinds of video per workflow:
  - nodes: workflow graph step labels — no source audio in the schema, so
    fresh TTS is synthesized for each label (the only kind that isn't reusing
    real recorded audio).
  - chunks: every chunk's example sentence, in order.
  - recall: every recall prompt, in order.
  - conversation-<n>: every turn's text in one conversation, in order.

Output: workflows/<id>/video/<kind>.mp4
"""

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

from generator.media_utils import probe_duration
from generator.providers.renderer import get_renderer
from generator.providers.tts_edge import EdgeTTSProvider, resolve_voice

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT / "workflows"
CACHE_DIR = Path(__file__).resolve().parent / "cache" / "workflow_video"
CONFIG_PATH = Path(__file__).resolve().parent / "config" / "config.yaml"


def _load_video_style() -> dict:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return config.get("video", {})


def _download(url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
    out_path = CACHE_DIR / f"{key}.mp3"
    if not out_path.exists():
        # R2's CDN returns 403 for urllib's default User-Agent string
        # (verified: curl gets 200, plain urlretrieve gets 403) — a real
        # bot-blocking rule, not a code bug, so just look like a normal client.
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request) as response:  # noqa: S310 - trusted R2 URLs from our own lesson.json
            out_path.write_bytes(response.read())
    return out_path


def _segments_for_kind(lesson: dict, kind: str) -> list[tuple[str, str | None]]:
    """Returns (text, audio_url_or_None) pairs — None means "needs fresh TTS"."""
    if kind == "nodes":
        return [(n["label"], None) for n in lesson["nodes"]]
    if kind == "chunks":
        return [(c["example"], c["audio"]) for c in lesson["chunks"]]
    if kind == "recall":
        return [(r["prompt"], r["prompt_audio"]) for r in lesson["recall"]]
    if kind.startswith("conversation-"):
        idx = int(kind.split("-", 1)[1]) - 1
        convo = lesson["conversations"][idx]
        return [(t["text"], t["audio"]) for t in convo["turns"]]
    raise ValueError(f"Unknown kind: {kind!r}")


def _build_segment_audio(
    text: str, audio_url: str | None, tts: EdgeTTSProvider, voice: str, work_dir: Path, index: int
) -> Path:
    if audio_url:
        return _download(audio_url)
    out_path = work_dir / f"node_{index}.mp3"
    tts.synthesize(text, voice, out_path)
    return out_path


def _concat_audio(segment_paths: list[Path], out_path: Path) -> None:
    # Re-encode (rather than stream-copy) so segments from different sources
    # (R2-hosted mp3s + freshly synthesized ones) concatenate reliably even
    # if their codec parameters don't match exactly.
    list_file = out_path.parent / f"{out_path.stem}_concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in segment_paths), encoding="utf-8"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(out_path),
        ],
        check=True,
    )


def _all_kinds(lesson: dict) -> list[str]:
    kinds = ["nodes", "chunks", "recall"]
    kinds += [f"conversation-{i + 1}" for i in range(len(lesson.get("conversations", [])))]
    return kinds


def generate_video(workflow_id: str, kind: str) -> Path:
    lesson_path = WORKFLOWS_DIR / workflow_id / "lesson.json"
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    segments = _segments_for_kind(lesson, kind)
    if not segments:
        raise ValueError(f"No content for kind={kind!r} in {workflow_id}")

    work_dir = CACHE_DIR / workflow_id / kind
    work_dir.mkdir(parents=True, exist_ok=True)

    tts = EdgeTTSProvider()
    voice = resolve_voice("english", "male")

    segment_paths: list[Path] = []
    subtitle_data: list[dict] = []
    cursor = 0.0
    for i, (text, url) in enumerate(segments):
        path = _build_segment_audio(text, url, tts, voice, work_dir, i)
        duration = probe_duration(path) or 0.0
        subtitle_data.append({"sentence": text, "start": round(cursor, 3), "end": round(cursor + duration, 3)})
        segment_paths.append(path)
        cursor += duration

    combined_audio = work_dir / "combined.mp3"
    _concat_audio(segment_paths, combined_audio)

    video_config = dict(_load_video_style())
    video_config["language"] = "english"
    video_config["topic"] = lesson["meta"].get("title", workflow_id)
    video_config["level"] = lesson["meta"].get("difficulty", "")

    out_dir = WORKFLOWS_DIR / workflow_id / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{kind}.mp4"

    subtitle_path = work_dir / "subtitle.json"
    subtitle_path.write_text(json.dumps(subtitle_data, ensure_ascii=False, indent=2), encoding="utf-8")

    renderer = get_renderer("ffmpeg")
    renderer.render(combined_audio, subtitle_path, video_config, out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate videos from a workflows/<id>/lesson.json")
    parser.add_argument("workflow_id")
    parser.add_argument("--only", help="Generate just one kind: nodes|chunks|recall|conversation-<n>")
    args = parser.parse_args()

    lesson_path = WORKFLOWS_DIR / args.workflow_id / "lesson.json"
    if not lesson_path.exists():
        print(f"No such workflow: {args.workflow_id} (missing {lesson_path})")
        sys.exit(1)
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))

    kinds = [args.only] if args.only else _all_kinds(lesson)

    for kind in kinds:
        print(f"Generating {kind}...")
        path = generate_video(args.workflow_id, kind)
        print(f"  -> {path}")


if __name__ == "__main__":
    main()
