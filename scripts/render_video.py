"""Render a finished KarmaClockIn video: narration + looping free-licensed
background + burned-in captions + outro card.

Usage (also used as a library from publish_short.py / publish_long.py):
    python render_video.py --hook-line "..." --script-file script.txt \
        --output out.mp4 --orientation vertical
"""
import argparse
import glob
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from captions import build_cues, build_ass  # noqa: E402
from generate_narration import generate_narration  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKGROUNDS_DIR = os.path.join(REPO_ROOT, "assets", "backgrounds")
SUBREDDIT_TAG_TEMPLATE = "r/MaliciousCompliance  •  Posted by u/throwaway_teacher"
OUTRO_MAIN_TEXT = "Follow for more workplace karma stories"
OUTRO_HANDLE_TEXT = "@karmaclockin"
OUTRO_DURATION = 4.0


def pick_background(seed_text):
    """Deterministically rotate through the available background clips so
    the same story always maps to the same clip (reproducible re-renders),
    while different stories get variety."""
    clips = sorted(glob.glob(os.path.join(BACKGROUNDS_DIR, "*.mp4")))
    if not clips:
        raise SystemExit(f"No background clips found in {BACKGROUNDS_DIR}")
    idx = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % len(clips)
    return clips[idx]


def render(
    hook_line,
    script_text,
    output_path,
    orientation="vertical",
    subreddit_tag=None,
    voice_id=None,
    work_dir=None,
):
    work_dir = work_dir or os.path.dirname(os.path.abspath(output_path))
    os.makedirs(work_dir, exist_ok=True)
    narration_path = os.path.join(work_dir, "narration.mp3")
    ass_path = os.path.join(work_dir, "subtitles.ass")

    kwargs = {}
    if voice_id:
        kwargs["voice_id"] = voice_id
    narration_duration = generate_narration(script_text, narration_path, **kwargs)

    cues = build_cues(script_text, narration_duration)
    tag = subreddit_tag or SUBREDDIT_TAG_TEMPLATE
    total_duration = build_ass(
        ass_path, cues, hook_line, tag, narration_duration, OUTRO_DURATION,
        OUTRO_MAIN_TEXT, OUTRO_HANDLE_TEXT,
        play_res_x=(1080 if orientation == "vertical" else 1920),
        play_res_y=(1920 if orientation == "vertical" else 1080),
    )

    bg_path = pick_background(hook_line)

    if orientation == "vertical":
        # Landscape source -> 9:16: scale to cover height, crop centered width.
        vf = "scale=-2:1920,crop=1080:1920:(iw-1080)/2:0,setsar=1"
    else:
        # 16:9 long-form: scale to cover width, crop centered height.
        vf = "scale=1920:-2,crop=1920:1080:0:(ih-1080)/2,setsar=1"

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", bg_path,
        "-i", narration_path,
        "-filter_complex",
        f"[0:v]{vf}[bg];[bg]ass={ass_path}[vout];[1:a]apad=pad_dur={OUTRO_DURATION}[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path, total_duration


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hook-line", required=True)
    ap.add_argument("--script-file", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--orientation", choices=["vertical", "horizontal"], default="vertical")
    ap.add_argument("--subreddit-tag", default=None)
    ap.add_argument("--voice-id", default=None)
    args = ap.parse_args()

    with open(args.script_file) as f:
        script_text = f.read()

    out, dur = render(
        args.hook_line, script_text, args.output,
        orientation=args.orientation, subreddit_tag=args.subreddit_tag,
        voice_id=args.voice_id,
    )
    print(f"Rendered {out} ({dur:.2f}s)")


if __name__ == "__main__":
    _main()
