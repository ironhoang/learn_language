"""Thumbnail generation for Step 7 (Upload).

Per spec: even with no upload credentials, the pipeline should still produce
video.mp4 + metadata.txt + thumbnail.png so the user can upload manually.
Simplest approach that needs no extra renderer: grab one frame from the
already-rendered video via ffmpeg, then overlay the title with Pillow.
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generator.media_utils import probe_duration

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _load_font(size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _extract_frame(video_path: Path, out_path: Path, timestamp: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{timestamp}",
            "-i", str(video_path),
            "-frames:v", "1",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def generate_thumbnail(video_path: Path, title: str, out_path: Path) -> Path:
    duration = probe_duration(video_path) or 1.0
    timestamp = min(1.0, duration * 0.1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _extract_frame(video_path, out_path, timestamp)

    img = Image.open(out_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _load_font(size=max(28, img.width // 18))

    label = title.split("\n")[0]  # headline line only — thumbnail has no room for 2 lines
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (img.width - text_w) / 2
    y = img.height * 0.08
    padding = 16

    draw.rectangle([x - padding, y - padding, x + text_w + padding, y + text_h + padding], fill=(0, 0, 0))
    draw.text((x, y), label, font=font, fill=(255, 255, 255))

    img.save(out_path)
    return out_path
