"""Generate narration audio via edge-tts, which uses Microsoft Edge's own
speech service for free — no account, no API key, no plan tier to run into.
This replaces the earlier ElevenLabs-based version, which turned out to
require a paid plan for any voice usable through its API."""
import asyncio
import subprocess

import edge_tts

# Calm, deep, professional-sounding free Neural voice - closest free match to
# the "calm, authoritative narrator" brief. Swapping voices is just a string
# change here (no cloning/design process): try "en-US-GuyNeural" (warmer,
# more conversational) as an alternative - run `edge-tts --list-voices` to
# see the full catalog.
DEFAULT_VOICE = "en-US-ChristopherNeural"


def generate_narration(text, output_path, voice_id=None):
    voice = voice_id or DEFAULT_VOICE
    communicate = edge_tts.Communicate(text, voice)
    asyncio.run(communicate.save(output_path))
    return probe_duration(output_path)


def probe_duration(path):
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())
