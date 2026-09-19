"""Generate narration audio via the ElevenLabs REST API directly (no MCP —
this runs on a GitHub Actions runner, which has plain internet access)."""
import os
import subprocess
import requests

DEFAULT_VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian - Deep, Resonant and Comforting
DEFAULT_MODEL_ID = "eleven_multilingual_v2"


def generate_narration(text, output_path, voice_id=DEFAULT_VOICE_ID, model_id=DEFAULT_MODEL_ID):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {"text": text, "model_id": model_id}
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
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
