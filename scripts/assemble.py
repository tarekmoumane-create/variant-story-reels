#!/usr/bin/env python3
"""Assemble a Reddit-story reel over Variant gameplay.

Usage: python3 assemble.py <story.json> <out.mp4> [seed]

story.json: {"question": "...", "story": "...", "voice": "Charon"}
Requires GEMINI_API_KEY in env. Gameplay pulled from GAMEPLAY_DIR.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAMEPLAY_DIR = os.environ.get(
    "GAMEPLAY_DIR",
    os.path.expanduser("~/Projects/variant-story-reels/gameplay"),
)
CARD_Y = 640  # vertical position of the question card


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)[:160])
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def gameplay_clips(seed):
    clips = sorted(
        f for f in os.listdir(GAMEPLAY_DIR)
        if f.lower().endswith(".mp4") and not f.startswith(".")
    )
    if not clips:
        sys.exit(f"no gameplay clips in {GAMEPLAY_DIR}")
    k = seed % len(clips)
    return [os.path.join(GAMEPLAY_DIR, f) for f in clips[k:] + clips[:k]]


def main():
    story_path, out_path = sys.argv[1], sys.argv[2]
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    story = json.load(open(story_path))
    question, body = story["question"].strip(), story["story"].strip()
    voice = story.get("voice", "Charon")

    work = tempfile.mkdtemp(prefix="reel_")
    full_text = question + "\n\n" + body

    # 1. voiceover (then mechanically sped up for brainrot pacing)
    txt = os.path.join(work, "full.txt")
    open(txt, "w").write(full_text)
    wav_raw = os.path.join(work, "vo_raw.wav")
    run(["python3", f"{HERE}/tts.py", txt, wav_raw, voice])
    speed = float(story.get("speed", 1.3))
    wav = os.path.join(work, "vo.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", wav_raw,
         "-filter:a", f"atempo={speed}", wav])
    vo_dur = probe_duration(wav)

    # 2. word timestamps
    words_json = os.path.join(work, "words.json")
    run(["python3", f"{HERE}/align.py", wav, words_json])
    words = json.load(open(words_json))

    # 3. split question vs story words (card shows during question)
    n_q = len(question.split())
    n_q = min(n_q, max(len(words) - 1, 1))
    q_end = words[n_q - 1]["end"] + 0.25
    story_words = words[n_q:]
    sw_json = os.path.join(work, "story_words.json")
    json.dump(story_words, open(sw_json, "w"))
    ass = os.path.join(work, "captions.ass")
    run(["python3", f"{HERE}/captions.py", sw_json, ass])

    # 4. reddit card
    card = os.path.join(work, "card.png")
    run(["python3", f"{HERE}/reddit_card.py", question, card,
         story.get("card_name", "Story Time")])

    # 5. gather enough gameplay to cover the voiceover
    total = vo_dur + 0.6
    picked, acc = [], 0.0
    pool = gameplay_clips(seed)
    i = 0
    while acc < total:
        clip = pool[i % len(pool)]
        picked.append(clip)
        acc += probe_duration(clip)
        i += 1

    # 6. assemble with ffmpeg
    inputs = []
    for c in picked:
        inputs += ["-i", c]
    inputs += ["-i", wav, "-i", card]
    n = len(picked)
    vparts = "".join(
        f"[{j}:v]scale=1080:-2,crop=1080:1920:0:(ih-1920)/2,fps=30,setsar=1[v{j}];"
        for j in range(n)
    )
    concat = "".join(f"[v{j}]" for j in range(n)) + f"concat=n={n}:v=1:a=0[base];"
    ass_escaped = ass.replace(":", r"\:").replace("'", r"\'")
    fc = (
        vparts + concat +
        f"[base][{n + 1}:v]overlay=(W-w)/2:{CARD_Y}:enable='between(t,0,{q_end:.2f})'[carded];"
        f"[carded]subtitles=filename='{ass_escaped}'[vout]"
    )
    run([
        "ffmpeg", "-y", "-v", "error", *inputs,
        "-filter_complex", fc,
        "-map", "[vout]", "-map", f"{n}:a",
        "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_path,
    ])
    print(f"\nDONE {out_path} ({probe_duration(out_path):.1f}s, card until {q_end:.1f}s)")


if __name__ == "__main__":
    main()
