#!/usr/bin/env python3
"""CLI entrypoint — thin wrapper around Pipeline Manager.

Every subcommand loads config.yaml, applies CLI overrides, discovers any
already-generated artifacts on disk (so `python main.py audio` works without
re-running `story` first if story.json already exists), then runs the
requested stage(s) through Pipeline Manager. No pipeline business logic lives
in this file — see generator/pipeline_manager.py and generator/<stage>/.

Per spec, there is no standalone `chunks` subcommand: chunks.json is a
supplementary asset no later stage depends on, so it only ever runs as part
of `generate`.
"""

from pathlib import Path
from typing import Optional

import typer
import yaml

from generator.pipeline_manager import PipelineManager, discover_existing_artifacts

app = typer.Typer(add_completion=False, help="Content Generation Pipeline — shorts video factory.")

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "config.yaml"

LanguageOpt = typer.Option(None, "--language", help="Override config.yaml language")
LevelOpt = typer.Option(None, "--level", help="Override config.yaml level")
TopicOpt = typer.Option(None, "--topic", help="Override config.yaml topic")
DurationOpt = typer.Option(None, "--duration", help="Override config.yaml duration (seconds)")


def _load_config(
    language: Optional[str], level: Optional[str], topic: Optional[str], duration: Optional[int]
) -> dict:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    if language is not None:
        config["language"] = language
    if level is not None:
        config["level"] = level
    if topic is not None:
        config["topic"] = topic
    if duration is not None:
        config["duration"] = duration
    return config


def _make_manager(config: dict) -> PipelineManager:
    pm = PipelineManager(config)
    pm.artifacts.update(discover_existing_artifacts())
    return pm


def _echo_artifacts(artifacts: dict) -> None:
    for name, path in artifacts.items():
        typer.echo(f"  {name}: {path}")


@app.command()
def generate(
    language: Optional[str] = LanguageOpt,
    level: Optional[str] = LevelOpt,
    topic: Optional[str] = TopicOpt,
    duration: Optional[int] = DurationOpt,
):
    """Run the entire pipeline: story -> chunks -> audio -> subtitle -> video -> metadata -> upload."""
    config = _load_config(language, level, topic, duration)
    pm = _make_manager(config)
    artifacts = pm.run_all()
    typer.echo("Done:")
    _echo_artifacts(artifacts)


def _stage_command(stage_name: str):
    def command(
        language: Optional[str] = LanguageOpt,
        level: Optional[str] = LevelOpt,
        topic: Optional[str] = TopicOpt,
        duration: Optional[int] = DurationOpt,
    ):
        config = _load_config(language, level, topic, duration)
        pm = _make_manager(config)
        path = pm.run_stage(stage_name)
        typer.echo(f"{stage_name}: {path}")

    command.__doc__ = f"Generate only {stage_name}."
    return command


for _name in ("story", "audio", "subtitle", "video", "metadata", "upload"):
    app.command(name=_name)(_stage_command(_name))


if __name__ == "__main__":
    app()
