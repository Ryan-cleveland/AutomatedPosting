"""
Turn ElevenLabs' character-level alignment into short, timed caption lines,
then write them out as an .ass subtitle file ffmpeg can burn in directly.

Style: static bold white caps, no per-word highlight/animation - matches the
channel's established look.
"""

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Anton,84,&H00FFFFFF,&H00000000,&H00000000,1,0,1,5,0,2,80,80,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def chars_to_words(alignment):
    """Group character-level timings into (word, start, end) tuples."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words = []
    word, w_start, w_end = "", None, None
    for ch, s, e in zip(chars, starts, ends):
        if ch.strip() == "":
            if word:
                words.append((word, w_start, w_end))
                word, w_start, w_end = "", None, None
            continue
        if w_start is None:
            w_start = s
        word += ch
        w_end = e
    if word:
        words.append((word, w_start, w_end))
    return words


def group_into_lines(words, max_chars=28, max_words=6):
    """Chunk words into short caption lines timed to the narration."""
    lines = []
    cur, cur_chars, line_start, line_end = [], 0, None, None

    for word, s, e in words:
        if line_start is None:
            line_start = s
        projected = cur_chars + len(word) + (1 if cur else 0)
        if cur and (projected > max_chars or len(cur) >= max_words):
            lines.append((" ".join(cur), line_start, line_end))
            cur, cur_chars, line_start = [], 0, s
        cur.append(word)
        cur_chars += len(word) + (1 if len(cur) > 1 else 0)
        line_end = e

    if cur:
        lines.append((" ".join(cur), line_start, line_end))
    return lines


def _ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def build_ass(lines, out_path="captions.ass"):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for text, start, end in lines:
            escaped = text.upper().replace("\\", "").replace("{", "").replace("}", "")
            f.write(
                f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Caption,,0,0,0,,{escaped}\n"
            )
    return out_path
