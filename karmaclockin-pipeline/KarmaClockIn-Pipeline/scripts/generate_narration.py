"""
Generate narration audio via ElevenLabs' "with timestamps" endpoint, which
returns character-level alignment alongside the audio so we can build
captions that are actually synced to the voice instead of guessed.

Requires:
  ELEVENLABS_API_KEY
  ELEVENLABS_VOICE_ID   - pick one with `creative_list_voices` (or the
                          ElevenLabs dashboard) and pin it here so every
                          video uses the same narrator.
"""

import base64
import os

import requests

BASE = "https://api.elevenlabs.io/v1"


def generate_narration(text, out_audio_path="narration.mp3"):
    voice_id = os.environ["ELEVENLABS_VOICE_ID"]
    url = f"{BASE}/text-to-speech/{voice_id}/with-timestamps"
    headers = {
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    with open(out_audio_path, "wb") as f:
        f.write(base64.b64decode(data["audio_base64"]))

    # {"characters": [...], "character_start_times_seconds": [...], "character_end_times_seconds": [...]}
    return data["alignment"]
