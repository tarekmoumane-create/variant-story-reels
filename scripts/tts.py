#!/usr/bin/env python3
"""Generate a voiceover WAV/MP3 from story text.

Two engines, chosen by the TTS_ENGINE env var (default "gemini"):
  gemini      — Google Gemini TTS (needs GEMINI_API_KEY); voice is a name like "Charon"
  elevenlabs  — ElevenLabs TTS (needs ELEVENLABS_API_KEY); voice is a voice ID

Usage: python3 tts.py <story.txt> <out> [voice] [model]
"""
import base64
import json
import os
import struct
import subprocess
import sys
import time

DEFAULT_VOICE = "Charon"
DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"
ELEVENLABS_DEFAULT_MODEL = "eleven_multilingual_v2"

STYLE = (
    "Read this at a normal, steady pace in a deep male voice with a flat, "
    "even, matter-of-fact delivery — like a text-to-speech narrator. No "
    "dramatic pauses, no rushing, no emotional swings. Consistent rhythm "
    "throughout (the audio will be mechanically sped up afterwards):\n\n"
)


def synthesize(text: str, voice: str, model: str, api_key: str) -> bytes:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "contents": [{"parts": [{"text": STYLE + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
            },
        },
    }
    # The TTS preview model returns 503 "high demand" fairly often; retry a few
    # times with backoff before giving up (the daily routine runs unattended).
    for attempt in range(6):
        out = subprocess.run(
            ["curl", "-sS", "--fail-with-body", "--max-time", "300",
             "-X", "POST", url,
             "-H", "Content-Type: application/json", "-d", "@-"],
            input=json.dumps(body).encode(), capture_output=True, timeout=330,
        )
        if out.returncode == 0:
            break
        err = out.stdout.decode(errors="replace")
        transient = '"code": 503' in err or '"code": 429' in err or out.returncode == 28
        if not transient or attempt == 5:
            sys.exit(f"TTS request failed: {err[:500]} {out.stderr.decode()[:200]}")
        wait = 20 * (attempt + 1)
        print(f"TTS transient error, retrying in {wait}s "
              f"(attempt {attempt + 2}/6)", file=sys.stderr)
        time.sleep(wait)
    data = json.loads(out.stdout)
    part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    mime = part["mimeType"]  # e.g. audio/L16;codec=pcm;rate=24000
    pcm = base64.b64decode(part["data"])
    rate = 24000
    for token in mime.split(";"):
        if token.strip().startswith("rate="):
            rate = int(token.strip()[5:])
    return wav_from_pcm(pcm, rate)


def synthesize_elevenlabs(text: str, voice: str, model: str, api_key: str) -> bytes:
    # Returns MP3 bytes; downstream ffmpeg decodes it fine regardless of extension.
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        f"?output_format=mp3_44100_128"
    )
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    out = subprocess.run(
        ["curl", "-sS", "--fail-with-body", "-X", "POST", url,
         "-H", f"xi-api-key: {api_key}",
         "-H", "Content-Type: application/json",
         "-H", "Accept: audio/mpeg",
         "-d", "@-"],
        input=json.dumps(body).encode(), capture_output=True, timeout=300,
    )
    if out.returncode != 0:
        sys.exit(f"ElevenLabs TTS failed: {out.stdout.decode(errors='replace')[:500]} "
                 f"{out.stderr.decode(errors='replace')[:200]}")
    return out.stdout


def wav_from_pcm(pcm: bytes, rate: int) -> bytes:
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(pcm), b"WAVE", b"fmt ", 16,
        1, 1, rate, rate * 2, 2, 16, b"data", len(pcm),
    )
    return header + pcm


def main():
    story_path, out_path = sys.argv[1], sys.argv[2]
    engine = os.environ.get("TTS_ENGINE", "gemini").lower()
    text = open(story_path).read().strip()

    if engine == "elevenlabs":
        voice = sys.argv[3] if len(sys.argv) > 3 else ""
        model = sys.argv[4] if len(sys.argv) > 4 else ELEVENLABS_DEFAULT_MODEL
        if not voice:
            sys.exit("elevenlabs engine needs a voice ID (set \"voice\" in the story JSON)")
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            sys.exit("ELEVENLABS_API_KEY not set (add it to .env)")
        audio = synthesize_elevenlabs(text, voice, model, api_key)
    else:
        voice = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE
        model = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL
        api_key = os.environ["GEMINI_API_KEY"]
        audio = synthesize(text, voice, model, api_key)

    with open(out_path, "wb") as f:
        f.write(audio)
    print(f"wrote {out_path} ({len(audio)} bytes, engine={engine})")


if __name__ == "__main__":
    main()
