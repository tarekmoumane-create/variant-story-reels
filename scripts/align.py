#!/usr/bin/env python3
"""Get word-level timestamps from a voiceover WAV using faster-whisper.

Usage: python3 align.py <audio.wav> <out_words.json>
"""
import json
import sys

from faster_whisper import WhisperModel


def main():
    audio_path, out_path = sys.argv[1], sys.argv[2]
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({
                "word": w.word.strip(),
                "start": round(w.start, 3),
                "end": round(w.end, 3),
            })
    with open(out_path, "w") as f:
        json.dump(words, f, indent=1)
    print(f"wrote {out_path} ({len(words)} words)")


if __name__ == "__main__":
    main()
