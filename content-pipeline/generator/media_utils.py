"""Shared media probing helper (ffprobe wrapper) — used by both the Subtitle
stage (fallback duration estimate) and the FFmpeg renderer. Kept outside any
stage package for the same reason as text_utils.py: it's a plain utility, not
stage business logic, so importing it from two stages doesn't violate "no
stage should call another stage directly".
"""

import subprocess
from pathlib import Path


def probe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None
