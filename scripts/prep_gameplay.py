#!/usr/bin/env python3
"""Cut raw gameplay recordings into clean, action-only segments.

Scans each clip for dark frames (low brightness) and frozen/static stretches
(menus, loading screens), keeps only lively intervals >= MIN_SEG seconds, and
exports them pre-normalized to 1080x1920@30 into the output dir.

Usage: python3 prep_gameplay.py <raw_dir> <out_dir>
"""
import os
import re
import subprocess
import sys

MIN_SEG = 4.0       # keep intervals at least this long
YAVG_MIN = float(os.environ.get("YAVG_MIN", "50"))
                    # average luma below this (0-255) = near-black loading screen.
                    # Some Variant games are dark (~60), so this floor is low and
                    # we lean on freezedetect to strip static menus. Override with
                    # the YAVG_MIN env var (raise it for glarey footage, 0 = off).
VIDEO_EXTS = (".mp4", ".mov", ".m4v")
SAMPLE_FPS = 2      # brightness samples per second
FREEZE_NOISE = "0.0015"
FREEZE_DUR = 1.5    # static for this long = menu/idle


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def bad_intervals(path, duration):
    """Return merged list of (start, end) intervals that are dark or frozen."""
    bad = []

    # brightness: sample YAVG at SAMPLE_FPS
    out = subprocess.run(
        ["ffmpeg", "-i", path, "-vf",
         f"fps={SAMPLE_FPS},signalstats,metadata=print:key=lavfi.signalstats.YAVG",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    times, vals = [], []
    t = None
    for line in out.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1))
        m = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", line)
        if m and t is not None:
            times.append(t)
            vals.append(float(m.group(1)))
    step = 1.0 / SAMPLE_FPS
    for t, v in zip(times, vals):
        if v < YAVG_MIN:
            bad.append((t, t + step))

    # frozen frames
    out = subprocess.run(
        ["ffmpeg", "-i", path, "-vf",
         f"freezedetect=n={FREEZE_NOISE}:d={FREEZE_DUR}",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    fstart = None
    for line in out.stderr.splitlines():
        m = re.search(r"freeze_start: ([\d.]+)", line)
        if m:
            fstart = float(m.group(1))
        m = re.search(r"freeze_end: ([\d.]+)", line)
        if m and fstart is not None:
            bad.append((fstart, float(m.group(1))))
            fstart = None
    if fstart is not None:
        bad.append((fstart, duration))

    # merge overlaps (with a little padding around bad zones)
    pad = 0.3
    bad = sorted((max(0, s - pad), min(duration, e + pad)) for s, e in bad)
    merged = []
    for s, e in bad:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def good_intervals(duration, bad):
    good, cur = [], 0.0
    for s, e in bad:
        if s - cur >= MIN_SEG:
            good.append((cur, s))
        cur = max(cur, e)
    if duration - cur >= MIN_SEG:
        good.append((cur, duration))
    return good


def main():
    raw_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".mp4"):
            os.remove(os.path.join(out_dir, f))
    n = 0
    clips = sorted(f for f in os.listdir(raw_dir)
                   if f.lower().endswith(VIDEO_EXTS) and not f.startswith("."))
    for clip in clips:
        path = os.path.join(raw_dir, clip)
        dur = probe_duration(path)
        bad = bad_intervals(path, dur)
        good = good_intervals(dur, bad)
        kept = sum(e - s for s, e in good)
        print(f"{clip}: {dur:.1f}s total, kept {kept:.1f}s in {len(good)} segment(s)")
        for s, e in good:
            n += 1
            out = os.path.join(out_dir, f"seg{n:02d}.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.2f}", "-i", path,
                 "-t", f"{e - s:.2f}",
                 "-vf", "scale=1080:-2,crop=1080:1920:0:(ih-1920)/2,fps=30,setsar=1",
                 "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                 "-pix_fmt", "yuv420p", out], check=True)
    print(f"\n{n} segments written to {out_dir}")


if __name__ == "__main__":
    main()
