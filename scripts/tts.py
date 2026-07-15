#!/usr/bin/env python3
"""Generate a voiceover MP3/WAV from story text using Gemini TTS.

Usage: python3 tts.py <story.txt> <out.wav> [voice] [model]
"""
import base64
import json
import os
import struct
import subprocess
import sys

DEFAULT_VOICE = "Charon"
DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"

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
    out = subprocess.run(
        ["curl", "-sS", "--fail-with-body", "-X", "POST", url,
         "-H", "Content-Type: application/json", "-d", "@-"],
        input=json.dumps(body).encode(), capture_output=True, timeout=300,
    )
    if out.returncode != 0:
        sys.exit(f"TTS request failed: {out.stdout.decode()[:500]} {out.stderr.decode()[:200]}")
    data = json.loads(out.stdout)
    part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    mime = part["mimeType"]  # e.g. audio/L16;codec=pcm;rate=24000
    pcm = base64.b64decode(part["data"])
    rate = 24000
    for token in mime.split(";"):
        if token.strip().startswith("rate="):
            rate = int(token.strip()[5:])
    return wav_from_pcm(pcm, rate)


def wav_from_pcm(pcm: bytes, rate: int) -> bytes:
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(pcm), b"WAVE", b"fmt ", 16,
        1, 1, rate, rate * 2, 2, 16, b"data", len(pcm),
    )
    return header + pcm


def main():
    story_path, out_path = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE
    model = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL
    api_key = os.environ["GEMINI_API_KEY"]
    text = open(story_path).read().strip()
    wav = synthesize(text, voice, model, api_key)
    with open(out_path, "wb") as f:
        f.write(wav)
    print(f"wrote {out_path} ({len(wav)} bytes)")


if __name__ == "__main__":
    main()
