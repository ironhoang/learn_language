"""Shared cache helper used by every stage — one hashing/lookup implementation,
not reinvented per stage. Cache key should include everything that determines
the output (e.g. story: language+level+topic+duration+prompt hash; audio:
text+voice+provider) so an unchanged input reuses the cached artifact instead
of calling an API again.
"""

import hashlib
import json
from pathlib import Path

CACHE_ROOT = Path(__file__).resolve().parent.parent / "cache"


def cache_key(*parts: object) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _cache_path(stage: str, key: str, suffix: str) -> Path:
    return CACHE_ROOT / stage / f"{key}{suffix}"


def get_cached(stage: str, key: str, suffix: str = ".json") -> Path | None:
    path = _cache_path(stage, key, suffix)
    return path if path.exists() else None


def save_cache(stage: str, key: str, data: str | bytes | dict | list, suffix: str = ".json") -> Path:
    path = _cache_path(stage, key, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (bytes, bytearray)):
        path.write_bytes(data)
    elif isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
