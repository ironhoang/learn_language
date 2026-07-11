"""Converts subtitle.json into an .ass file for ffmpeg/libass to burn in.

Renders the full transcript as ONE text block, with the currently-spoken
word/sentence spotlighted in an accent color as playback reaches it (each
word lights up then reverts to white once its own timing window passes —
not the cumulative "already sung stays highlighted" look of native ASS \\k
karaoke, since that reads wrong for a language-learning teleprompter where
you want to see what's CURRENTLY being said, not a running tally). Two
display modes, chosen via config.video.subtitle_mode:
  - "scroll" (default): constant-speed scroll starting at screen-center and
    moving up — accepts that uneven speech pace can drift the reading
    position out of exact sync with the audio over a long story. Needed
    whenever the transcript is too tall to fit one screen, since "static"
    simply cuts off anything past the top/bottom edge.
  - "static": the block sits fixed at screen-center, no animation. Content
    taller than one screen simply extends past the top/bottom edges (not
    visible) for the whole video — a deliberate tradeoff of "nothing moves",
    fine only for short transcripts that fit in one screen.

Technique: the whole wrapped transcript is a single Dialogue event spanning
the entire video. Scroll mode positions it with ASS's `\\move(x1,y1,x2,y2)`
tag — libass linearly interpolates the block's position over the event's
full duration, giving smooth constant-speed scrolling in one line, no
per-line event splitting needed. Static mode just uses `\\pos`. Word
highlighting is layered independently on top via per-word `\\t(t1,t2,\\1c&H..&)`
color transforms scoped to that word's own text run — each word gets its own
override block, so its color change never bleeds into neighboring words.
"""

from pathlib import Path

try:
    from pypinyin import Style as _PinyinStyle
    from pypinyin import pinyin as _pinyin_convert
except ImportError:  # pypinyin is in requirements.txt, but degrade gracefully rather than crash
    _pinyin_convert = None

MAX_CHARS_PER_LINE = 24
MAX_CHARS_PER_LINE_CHINESE = 12  # Chinese glyphs render ~2x wider than Latin ones
LINE_HEIGHT_FACTOR = 1.05  # empirically measured from a real render — libass's
# actual \N line spacing for this style turned out much tighter than a typical
# 1.4 "line-height" CSS-style assumption (measured ~59.5px per line at
# fontsize=60, i.e. ~0.99x, not 1.4x); this fed directly into the static
# mode's centering math and the scroll distance, so getting it right matters
# for both, not just cosmetics.
PINYIN_FONTSIZE_FACTOR = 0.55

TEXT_COLOR = "&H00FFFFFF"  # white
HIGHLIGHT_COLOR_ASS = "1673F9"  # BGR hex for #f97316 (orange) — matches the
# .chunk-card.highlight accent already used in workflows/shared/lesson.css,
# so the video's "currently spoken" color matches the web lesson's UI accent.
FLASH_MS = 80  # duration of each highlight-in / highlight-out color transform


ASS_HEADER_TEMPLATE = """[Script Info]
Title: content-pipeline subtitle
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {width}
PlayResY: {height}
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},{primary},{primary},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,8,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t - h * 3600 - m * 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    # Curly braces start/end ASS override blocks — a stray one in spoken text
    # would corrupt the whole event, so neutralize it.
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


def _highlight_span(text: str, start: float, end: float) -> str:
    """Wraps `text` in override tags that spotlight it in the accent color
    for [start, end] (seconds, relative to the Dialogue event's own Start=0)
    and revert to white afterward. Scoped to just this run — the next
    token's own override block resets color independently, so highlights
    never bleed into neighboring words."""
    start_ms = max(0, round(start * 1000))
    end_ms = max(start_ms + 1, round(end * 1000))
    in1, in2 = start_ms, start_ms + FLASH_MS
    out1, out2 = end_ms, end_ms + FLASH_MS
    # The leading static \1c reset is load-bearing, not decorative: without it
    # a \t() transform inherits whatever color value was still mid-flight from
    # the PREVIOUS word's transform (they share the same PrimaryColour
    # animation channel for the whole event), which was empirically observed
    # to make words light up before their own transform had even started.
    # Pinning back to white first makes each word's transform deterministic
    # regardless of neighboring words' timing.
    return (
        f"{{\\1c&HFFFFFF&"
        f"\\t({in1},{in2},\\1c&H{HIGHLIGHT_COLOR_ASS}&)"
        f"\\t({out1},{out2},\\1c&HFFFFFF&)}}{_escape(text)}"
    )


def _extract_tokens(subtitle_data: list[dict]) -> list[tuple[str, float, float, bool]]:
    """Returns (token_text, start, end, is_sentence_end) tuples — start/end
    drive per-word highlight timing, and is_sentence_end forces a line break
    in _wrap_lines()/_wrap_lines_with_pinyin() so one sentence never runs
    into the next on the same line, regardless of max_chars."""
    if subtitle_data and "word" in subtitle_data[0]:
        # edge-tts word tokens carry no punctuation of their own — append a
        # period wherever Subtitle stage flagged a sentence boundary
        # (generator/subtitle/generate.py's _mark_sentence_ends) so the
        # scrolling transcript doesn't read as one giant run-on sentence.
        return [
            (
                item["word"] + ("." if item.get("sentence_end") else ""),
                item["start"],
                item["end"],
                bool(item.get("sentence_end")),
            )
            for item in subtitle_data
        ]
    # fallback: each item is already 1 full sentence — highlight the whole
    # sentence as one unit since no finer-grained timing exists
    return [(item["sentence"], item["start"], item["end"], True) for item in subtitle_data]


def _wrap_lines(
    tokens: list[tuple[str, float, float, bool]], max_chars: int = MAX_CHARS_PER_LINE
) -> list[list[tuple[str, float, float]]]:
    """Greedy-wraps tokens into lines, each line kept as a list of
    (text, start, end) so the caller can render per-word highlight spans."""
    lines: list[list[tuple[str, float, float]]] = []
    current: list[tuple[str, float, float]] = []
    current_len = 0
    for tok, start, end, is_end in tokens:
        added_len = len(tok) + (1 if current else 0)
        if current and current_len + added_len > max_chars:
            lines.append(current)
            current = []
            current_len = 0
        current.append((tok, start, end))
        current_len += len(tok) + (1 if len(current) > 1 else 0)
        if is_end:
            lines.append(current)
            current = []
            current_len = 0
    if current:
        lines.append(current)
    return lines


def _token_to_pinyin(token: str) -> str:
    # Strip a trailing sentence-end period before conversion (added by
    # _extract_tokens) — pypinyin doesn't need it to produce syllables — then
    # re-append it so the pinyin line ends its sentence in the same place as
    # the hanzi line above it, instead of silently dropping the period.
    has_period = token.endswith(".")
    stripped = token.rstrip(".")
    segments = _pinyin_convert(stripped, style=_PinyinStyle.TONE, errors="default")
    result = " ".join(seg[0] for seg in segments)
    return result + "." if has_period else result


def _wrap_lines_with_pinyin(
    tokens: list[tuple[str, float, float, bool]], max_chars: int
) -> list[tuple[list[tuple[str, float, float]], str]]:
    """Same greedy wrap as _wrap_lines (including the forced sentence-end
    break), but also groups the matching pinyin per token into the same line
    breaks, returning (hanzi_tokens, pinyin_line) pairs. Only the hanzi line
    is highlighted per-word — the pinyin line stays a plain static caption to
    keep the render simple."""
    lines: list[tuple[list[tuple[str, float, float]], str]] = []
    current_tokens: list[tuple[str, float, float]] = []
    current_pinyin: list[str] = []
    current_len = 0
    for tok, start, end, is_end in tokens:
        added_len = len(tok) + (1 if current_tokens else 0)
        if current_tokens and current_len + added_len > max_chars:
            lines.append((current_tokens, " ".join(current_pinyin)))
            current_tokens, current_pinyin, current_len = [], [], 0
        current_tokens.append((tok, start, end))
        current_pinyin.append(_token_to_pinyin(tok))
        current_len += len(tok) + (1 if len(current_tokens) > 1 else 0)
        if is_end:
            lines.append((current_tokens, " ".join(current_pinyin)))
            current_tokens, current_pinyin, current_len = [], [], 0
    if current_tokens:
        lines.append((current_tokens, " ".join(current_pinyin)))
    return lines


def build_ass(subtitle_data: list[dict], config: dict, duration: float) -> str:
    video_cfg = config.get("video", {})
    width = video_cfg.get("width", 1080)
    height = video_cfg.get("height", 1920)
    fontsize = video_cfg.get("font_size", 60)
    font = video_cfg.get("font", "Arial")
    mode = video_cfg.get("subtitle_mode", "scroll")

    header = ASS_HEADER_TEMPLATE.format(
        width=width, height=height, font=font, fontsize=fontsize, primary=TEXT_COLOR
    )

    tokens = _extract_tokens(subtitle_data)
    is_chinese = video_cfg.get("language", "").lower() == "chinese" and _pinyin_convert is not None

    if is_chinese:
        line_pairs = _wrap_lines_with_pinyin(tokens, MAX_CHARS_PER_LINE_CHINESE)
        if not line_pairs:
            return header
        pinyin_fontsize = max(1, round(fontsize * PINYIN_FONTSIZE_FACTOR))
        line_height = round(fontsize * LINE_HEIGHT_FACTOR) + round(pinyin_fontsize * LINE_HEIGHT_FACTOR)
        block_height = len(line_pairs) * line_height
        text_block = "\\N".join(
            f"{' '.join(_highlight_span(t, s, e) for t, s, e in hanzi_tokens)}"
            f"\\N{{\\fs{pinyin_fontsize}}}{_escape(py)}{{\\fs{fontsize}}}"
            for hanzi_tokens, py in line_pairs
        )
    else:
        lines = _wrap_lines(tokens)
        if not lines:
            return header
        line_height = round(fontsize * LINE_HEIGHT_FACTOR)
        block_height = len(lines) * line_height
        text_block = "\\N".join(
            " ".join(_highlight_span(t, s, e) for t, s, e in line) for line in lines
        )

    center_y = height // 2
    x = width // 2

    if mode == "static":
        # \an8 anchors the TOP of the block at (x,y) — using center_y directly
        # (as an earlier version did) only centered the first line, leaving
        # the rest of the block hanging below screen-center instead of the
        # whole block being centered. Offset by half the block's height so
        # its vertical midpoint lands on center_y.
        anchor_y = center_y - block_height // 2
        pos_tag = f"{{\\an8\\pos({x},{anchor_y})}}"
    else:
        # Scroll up starting from screen-center: the block enters already
        # visible (no "walk-up" delay off-screen) and scrolls until it has
        # fully passed above the top of frame by the end of the video.
        end_y = center_y - block_height
        pos_tag = f"{{\\an8\\move({x},{center_y},{x},{end_y})}}"

    event = f"Dialogue: 0,{_fmt_time(0)},{_fmt_time(duration)},Default,,0,0,0,,{pos_tag}{text_block}"

    return header + event + "\n"


def write_ass(subtitle_data: list[dict], config: dict, duration: float, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_ass(subtitle_data, config, duration), encoding="utf-8")
    return out_path
