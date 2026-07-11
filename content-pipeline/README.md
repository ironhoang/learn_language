# Content Generation Pipeline

Generates a complete short-form language-learning video (story → chunks → audio → subtitle → video → metadata → optional upload) from a single CLI command. See `spec/audio.md` and `spec/audio-tecnical-flow.md` for the full design, and `spec/todo-audio-pipeline.md` for implementation notes.

## Setup (one-time)

```bash
cd content-pipeline
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in DEEPSEEK_API_KEY (edge-tts needs no key)
```

## Run

```bash
cd content-pipeline
./.venv/bin/python main.py generate --language english --level A2 --topic "Daily Standup" --duration 120
```

Chinese example (subtitles automatically show pinyin under each line):

```bash
./.venv/bin/python main.py generate --language chinese --level HSK2 --topic "Ordering Food" --duration 60
```

`--language` / `--level` / `--topic` / `--duration` override whatever's in `config/config.yaml`; omit any flag to use the config file's value.

Output lands in `output/`:
- `output/videos/video_<timestamp>.mp4`
- `output/metadata_<timestamp>.txt`
- `output/thumbnail_<timestamp>.png`

Each `generate` run gets its own timestamp, so multiple videos accumulate instead of overwriting each other. Upload to TikTok/YouTube stays manual unless you set `upload.tiktok`/`upload.youtube: true` in `config.yaml` **and** the matching API key in `.env` — with no credentials, the pipeline just leaves the files above for you to upload by hand.

### Re-render only part of the pipeline

Every stage caches by content, so rerunning is cheap and only redoes what actually changed:

```bash
./.venv/bin/python main.py video      # re-render video only (e.g. after tweaking config.yaml's video: section)
./.venv/bin/python main.py metadata   # regenerate title/description/hashtags only
./.venv/bin/python main.py story      # regenerate just the story
```

A standalone subcommand reuses whatever's already in `output/` (e.g. `video` reuses the existing `audio.mp3`/`subtitle.json` without needing to rerun `story`/`audio` first).

## Generate video for an existing workflow lesson

`workflow_video.py` renders videos from an existing `workflows/<id>/lesson.json` (the
"English Workflow for AI Engineers" module) instead of the story-generation path above —
reusing the same ffmpeg/ASS rendering machinery. Invoke it via the root wrapper:

```bash
python3 scripts/generate_workflow_video.py <workflow-id>
python3 scripts/generate_workflow_video.py <workflow-id> --only chunks
```

See `docs/workflow-lesson-video.md` for the full step-by-step pipeline (catalog → DeepSeek
lesson generation → audio → video).

## Compare TTS voices for a single Vietnamese sentence

```bash
./.venv/bin/python compare_tts.py "Xin chào, hôm nay bạn có khỏe không?"
```

Generates `output/tts_compare/edge.mp3` (edge-tts) and `output/tts_compare/gemini.wav`
(Gemini TTS) side by side. See `docs/tts-compare-vietnamese.md` for details.

## Key config options (`config/config.yaml`)

```yaml
llm: deepseek    # story/chunks/metadata generation (also: gemini)
tts: edge        # free, no API key — audio generation
voice: male      # or female

tts_rate:
  chinese: "-25%"  # 0.75x speed — edge-tts rate is a relative %, negative = slower

video:
  background: gradient       # "gradient" | "black" (or any ffmpeg color) | path to an image
  subtitle_mode: static       # "scroll" (constant-speed, from center) | "static" (fixed, no animation)
  font_size: 60
  show_overlay: false         # true adds a topic/level title + progress bar

upload:
  tiktok: false
  youtube: false
```
