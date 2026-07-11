#!/usr/bin/env python3
"""Compare edge-tts vs Gemini TTS on a single Vietnamese sentence.

Standalone tool — Vietnamese isn't wired into the full story pipeline
(no languages/vietnamese/levels.yaml), so this skips PipelineManager
entirely and calls both TTS providers directly for a quick side-by-side
listen. See docs/tts-compare-vietnamese.md for usage.
"""

from pathlib import Path

import typer

from generator.providers.tts import get_tts_provider
from generator.providers.tts_edge import resolve_voice as resolve_edge_voice
from generator.providers.tts_gemini import resolve_voice as resolve_gemini_voice

app = typer.Typer(add_completion=False, help="Compare edge-tts vs Gemini TTS on one Vietnamese sentence.")

OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "tts_compare"


@app.command()
def main(
    text: str = typer.Argument(..., help="Vietnamese sentence to synthesize"),
    voice: str = typer.Option("female", "--voice", help="male or female"),
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    edge_path = OUTPUT_DIR / "edge.mp3"
    edge = get_tts_provider("edge")
    edge.synthesize(text, resolve_edge_voice("vietnamese", voice), edge_path)
    typer.echo(f"edge-tts:   {edge_path}")

    gemini_path = OUTPUT_DIR / "gemini.wav"
    gemini = get_tts_provider("gemini")
    gemini.synthesize(text, resolve_gemini_voice(voice), gemini_path)
    typer.echo(f"Gemini TTS: {gemini_path}")


if __name__ == "__main__":
    app()
