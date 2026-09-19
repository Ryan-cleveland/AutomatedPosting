"""Split a narration script into caption chunks and estimate per-chunk timing
proportionally by character count over the known narration duration, then
emit an .ass subtitle file with a persistent title bar, dynamic caption
lines, and an outro card.

This is a proportional estimate, not word-level ASR alignment (no such API
was available when this was built) -- good enough for readable static
caption lines synced at roughly the sentence/line level.
"""
import re

ABBREVIATIONS = {"mrs.", "mr.", "ms.", "dr.", "jr.", "sr.", "st.", "vs."}
MAX_WORDS_PER_CAPTION = 8


def split_into_sentences(paragraph):
    words = paragraph.strip().split(" ")
    sentences = []
    buf = []
    for w in words:
        buf.append(w)
        stripped = w.strip('"').lower()
        if re.search(r'[.!?]"?$', w) and stripped not in ABBREVIATIONS:
            sentences.append(" ".join(buf))
            buf = []
    if buf:
        sentences.append(" ".join(buf))
    return [s for s in sentences if s]


def build_chunks(text, max_words=MAX_WORDS_PER_CAPTION):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for para in paragraphs:
        sentences = split_into_sentences(para)
        buf_words = []
        for sent in sentences:
            words = sent.split()
            if len(words) > max_words:
                if buf_words:
                    chunks.append(" ".join(buf_words))
                    buf_words = []
                for i in range(0, len(words), max_words):
                    sub = words[i:i + max_words]
                    if len(sub) < 3 and chunks:
                        chunks[-1] = chunks[-1] + " " + " ".join(sub)
                    else:
                        chunks.append(" ".join(sub))
            elif len(buf_words) + len(words) <= max_words:
                buf_words.extend(words)
            else:
                chunks.append(" ".join(buf_words))
                buf_words = words
        if buf_words:
            chunks.append(" ".join(buf_words))

    merged = []
    for c in chunks:
        if merged and len(c.split()) < 3 and len(merged[-1].split()) <= max_words:
            merged[-1] = merged[-1] + " " + c
        else:
            merged.append(c)
    return merged


def build_cues(text, narration_duration, max_words=MAX_WORDS_PER_CAPTION):
    chunks = build_chunks(text, max_words)
    char_counts = [len(c) for c in chunks]
    total_chars = sum(char_counts) or 1
    cues = []
    t = 0.0
    for c, chars in zip(chunks, char_counts):
        dur = (chars / total_chars) * narration_duration
        cues.append({"start": round(t, 3), "end": round(t + dur, 3), "text": c})
        t += dur
    if cues:
        cues[-1]["end"] = narration_duration
    return cues


def ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    cs = int(round((s - int(s)) * 100))
    return f"{h:d}:{m:02d}:{int(s):02d}.{cs:02d}"


def build_ass(
    path,
    cues,
    hook_line,
    subreddit_tag,
    narration_duration,
    outro_duration,
    outro_main_text,
    outro_handle_text,
    play_res_x=1080,
    play_res_y=1920,
):
    total_duration = narration_duration + outro_duration
    header = f"""[Script Info]
Title: KarmaClockIn Caption Overlay
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,DejaVu Sans,58,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,560,1
Style: SubredditTag,DejaVu Sans,30,&H00CCCCCC,&H000000FF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,1,2,0,8,60,60,90,1
Style: TitleText,DejaVu Sans,44,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,8,80,80,150,1
Style: OutroMain,DejaVu Sans,56,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,5,80,80,0,1
Style: OutroHandle,DejaVu Sans,40,&H00FFD24C,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,5,80,80,-120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    lines.append(
        f"Dialogue: 0,{ass_time(0)},{ass_time(narration_duration)},SubredditTag,,0,0,0,,{subreddit_tag}\n"
    )
    lines.append(
        f"Dialogue: 0,{ass_time(0)},{ass_time(narration_duration)},TitleText,,0,0,0,,{hook_line}\n"
    )
    for c in cues:
        text = c["text"].replace("\n", " ")
        lines.append(
            f"Dialogue: 1,{ass_time(c['start'])},{ass_time(c['end'])},Caption,,0,0,0,,{text}\n"
        )
    lines.append(
        f"Dialogue: 2,{ass_time(narration_duration)},{ass_time(total_duration)},OutroMain,,0,0,0,,{outro_main_text}\n"
    )
    lines.append(
        f"Dialogue: 2,{ass_time(narration_duration)},{ass_time(total_duration)},OutroHandle,,0,0,0,,{outro_handle_text}\n"
    )
    with open(path, "w") as f:
        f.writelines(lines)
    return total_duration
