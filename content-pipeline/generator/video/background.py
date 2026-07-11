"""Background source builder for Step 5 (Render Video).

config.video.background is one of:
  - a plain color name/hex (e.g. "black", "#101020") -> solid ffmpeg lavfi source
  - "gradient" -> a vertical gradient PNG generated once with Pillow, then looped
  - a path to an existing image file -> scaled + center-cropped to the target
    resolution, then looped

Returns the ffmpeg input args to place before the audio -i in the command.
"""

from pathlib import Path

from PIL import Image

GRADIENT_TOP = (18, 50, 100)  # deep blue
GRADIENT_BOTTOM = (16, 95, 80)  # teal green


def _is_image_path(background: str) -> bool:
    suffix = Path(background).suffix.lower()
    return suffix in {".png", ".jpg", ".jpeg", ".webp"} and Path(background).exists()


def _write_vertical_gradient(out_path: Path, width: int, height: int) -> None:
    # Render a 1px-wide column, then let Pillow's resize stretch it across the
    # full width — avoids an O(width*height) pure-Python pixel loop.
    column = Image.new("RGB", (1, height))
    pixels = column.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        pixels[0, y] = tuple(
            int(GRADIENT_TOP[c] + (GRADIENT_BOTTOM[c] - GRADIENT_TOP[c]) * t) for c in range(3)
        )
    column.resize((width, height)).save(out_path)


def _write_scaled_image(src_path: Path, out_path: Path, width: int, height: int) -> None:
    img = Image.open(src_path).convert("RGB")
    src_ratio = img.width / img.height
    target_ratio = width / height

    if src_ratio > target_ratio:
        new_height = height
        new_width = round(height * src_ratio)
    else:
        new_width = width
        new_height = round(width / src_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - width) // 2
    top = (new_height - height) // 2
    img.crop((left, top, left + width, top + height)).save(out_path)


def build_background_input(background: str, width: int, height: int, duration: float, work_dir: Path) -> list[str]:
    work_dir.mkdir(parents=True, exist_ok=True)

    if background == "gradient":
        gradient_path = work_dir / "background_gradient.png"
        _write_vertical_gradient(gradient_path, width, height)
        return ["-loop", "1", "-t", f"{duration}", "-i", str(gradient_path)]

    if _is_image_path(background):
        scaled_path = work_dir / "background_image.png"
        _write_scaled_image(Path(background), scaled_path, width, height)
        return ["-loop", "1", "-t", f"{duration}", "-i", str(scaled_path)]

    color = background or "black"
    return ["-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:d={duration}"]
