"""FFmpeg-based VideoRenderer — burns in ASS subtitles (full-transcript
constant-speed scroll) over a generated background. Per audio-tecnical-flow.md:
"FFmpeg should perform the final rendering for performance."

Optional overlays (progress bar + topic/level label, per spec Step 5's
"Optional: Progress bar, Lesson title, Language level, Topic") are gated
behind video_config["show_overlay"] — off by default to keep output clean,
matching config.yaml's current minimal example.
"""

import json
import subprocess
from pathlib import Path

from generator.media_utils import probe_duration
from generator.providers.renderer import VideoRenderer
from generator.video import background as background_module
from generator.video import subtitle_ass


class FFmpegRenderer(VideoRenderer):
    def render(self, audio_path: Path, subtitle_path: Path, video_config: dict, out_path: Path) -> Path:
        width = video_config.get("width", 1080)
        height = video_config.get("height", 1920)
        fps = video_config.get("fps", 30)
        background = video_config.get("background", "black")

        duration = probe_duration(audio_path) or 1.0

        work_dir = out_path.parent / "_render_tmp"
        bg_args = background_module.build_background_input(background, width, height, duration, work_dir)

        subtitle_data = json.loads(subtitle_path.read_text(encoding="utf-8"))
        ass_path = work_dir / "subtitle.ass"
        subtitle_ass.write_ass(subtitle_data, {"video": video_config}, duration, ass_path)

        vf_chain = [f"ass={ass_path}"]
        if video_config.get("show_overlay"):
            vf_chain.append(_overlay_filter(video_config, width, duration, work_dir))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            *bg_args,
            "-i", str(audio_path),
            "-vf", ",".join(vf_chain),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-r", str(fps),
            "-s", f"{width}x{height}",
            "-shortest",
            str(out_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg render failed:\n{e.stderr}") from e

        return out_path


def _overlay_filter(video_config: dict, width: int, duration: float, work_dir: Path) -> str:
    topic = video_config.get("topic", "")
    level = video_config.get("level", "")
    label = f"{topic} - {level}".strip(" -")
    label_escaped = label.replace(":", r"\:").replace("'", r"\'")

    drawtext = (
        f"drawtext=text='{label_escaped}':fontcolor=white:fontsize=32:"
        f"x=(w-text_w)/2:y=60:box=1:boxcolor=black@0.4:boxborderw=10"
    )

    # drawbox's `w` option has no built-in time variable (empirically confirmed —
    # `t`/`n` either silently collide with drawbox's own `t`=thickness option or
    # raise "Undefined constant"; a static box was rendered instead of growing).
    # A time-driven progress bar needs `sendcmd` to push explicit `w` updates to
    # a named `drawbox@bar` instance — verified this produces a bar whose pixel
    # width tracks elapsed time proportionally.
    cmds_path = _write_progress_commands(work_dir, width, duration)
    return f"{drawtext},sendcmd=f={cmds_path},drawbox@bar=x=0:y=ih-12:w=0:h=12:color=yellow@0.9:t=fill"


def _write_progress_commands(work_dir: Path, width: int, duration: float, step: float = 0.5) -> Path:
    path = work_dir / "progress_cmds.txt"
    lines = []
    t = 0.0
    while t < duration:
        w = round(width * (t / duration)) if duration > 0 else 0
        lines.append(f"{t:.3f} drawbox@bar w '{w}';")
        t += step
    lines.append(f"{duration:.3f} drawbox@bar w '{width}';")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
