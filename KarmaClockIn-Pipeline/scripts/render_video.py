"""
Compose the final vertical (9:16) video: a looping licensed background clip,
the ElevenLabs narration track, and burned-in .ass captions. Pure ffmpeg,
no paid video API.
"""

import glob
import os
import random
import subprocess

WIDTH, HEIGHT = 1080, 1920


def pick_background(pool_dir="assets/backgrounds"):
    clips = glob.glob(os.path.join(pool_dir, "*.mp4"))
    if not clips:
        raise RuntimeError(
            f"No background clips found in {pool_dir}/. Download a few licensed, "
            "watermark-free Mixkit vertical loops and commit them there before "
            "running the pipeline (see README)."
        )
    return random.choice(clips)


def get_audio_duration(audio_path):
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def render(audio_path, ass_path, out_path="final.mp4", bg_pool_dir="assets/backgrounds"):
    bg_path = pick_background(bg_pool_dir)
    duration = get_audio_duration(audio_path)

    # Fill-crop the background to 9:16, then burn in the caption track.
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"ass={ass_path}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", bg_path,
        "-i", audio_path,
        "-t", str(duration),
        "-vf", vf,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path
