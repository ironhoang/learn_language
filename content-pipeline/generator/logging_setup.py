"""Structured logging shared by every pipeline stage."""

import logging
import time
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def get_logger(stage: str) -> logging.Logger:
    return logging.getLogger(stage)


@contextmanager
def stage_timer(stage: str, provider: str | None = None):
    """Logs cache hit/miss + execution time + output files for one pipeline stage.

    Usage:
        with stage_timer("story", provider="gemini") as ctx:
            ctx.cache_hit = False
            ...
            ctx.output_files = [story_path]
    """
    logger = get_logger(stage)
    start = time.monotonic()

    class Ctx:
        cache_hit: bool = False
        output_files: list = []

    ctx = Ctx()
    try:
        yield ctx
    finally:
        elapsed = time.monotonic() - start
        logger.info(
            "provider=%s cache_hit=%s elapsed=%.2fs files=%s",
            provider or "-",
            ctx.cache_hit,
            elapsed,
            [str(f) for f in ctx.output_files],
        )
