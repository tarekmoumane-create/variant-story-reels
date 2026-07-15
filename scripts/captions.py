#!/usr/bin/env python3
"""Build an ASS subtitle file (one big word at a time) from word timestamps.

Usage: python3 captions.py <words.json> <out.ass> [time_offset_seconds]
"""
import json
import sys

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,Arial Black,110,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,2,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def main():
    words_path, out_path = sys.argv[1], sys.argv[2]
    offset = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    words = json.load(open(words_path))
    lines = [HEADER]
    for i, w in enumerate(words):
        start = w["start"] + offset
        # hold each word until the next one starts so there's no flicker
        if i + 1 < len(words):
            end = words[i + 1]["start"] + offset
        else:
            end = w["end"] + offset + 0.4
        text = w["word"].upper().replace("{", "").replace("}", "")
        # quick pop-in: start slightly large, settle at 100% in 60ms
        fx = r"{\fscx120\fscy120\t(0,60,\fscx100\fscy100)\pos(540,960)}"
        lines.append(
            f"Dialogue: 0,{ts(start)},{ts(end)},Word,,0,0,0,,{fx}{text}\n"
        )
    with open(out_path, "w") as f:
        f.writelines(lines)
    print(f"wrote {out_path} ({len(words)} words)")


if __name__ == "__main__":
    main()
