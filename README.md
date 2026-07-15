# Variant Story Reels

TikTok reel factory for **Variant** (the app that lets you create your own mobile
games). Generates "Reddit story time" style videos: an AI voice reads a juicy
story with big word-by-word captions over Variant gameplay, opening on a
Reddit-style question card. Modeled on the Minecraft-parkour "Story Time" format.

Two content streams:

| Stream | Stories | Card name | Output |
|---|---|---|---|
| **Story Reels** | Fictional Reddit-style confessions (`stories/`) | Story Time | `~/Downloads/Story Reels/story-reel-NN.mp4` |
| **Celebrity Drama** | Real, currently-reported celebrity news (`stories_celeb/`) | Celebrity Tea | `~/Downloads/Celebrity Drama/celeb-reel-NN.mp4` |

## Requirements

- macOS with `ffmpeg` on PATH
- Python 3.11+ with `pillow` and `faster-whisper` (`pip3 install pillow faster-whisper`)
- A Google Gemini API key (free tier works) — used for the voiceover
- Optional: `rclone` configured with a `gdrive:` remote for Google Drive upload

## Setup

```bash
cp .env.example .env        # paste your Gemini key inside
mkdir -p raw_gameplay gameplay
# drop portrait screen recordings of Variant gameplay into raw_gameplay/, then:
python3 scripts/prep_gameplay.py raw_gameplay gameplay
```

`prep_gameplay.py` auto-cuts dark screens and frozen/static stretches (menus,
loading) and keeps only lively segments, normalized to 1080x1920@30.

## Make a reel

1. Write a story file, e.g. `stories/07.json`:

```json
{
  "question": "What's something you'd never tell anyone?",
  "story": "120-160 words, first person, PG-13. THE FIRST SENTENCE IS THE HOOK — it must stop the scroll on its own. Twist midway, punchy last line.",
  "voice": "Charon"
}
```

Optional fields: `"card_name"` (default "Story Time"), `"speed"` (mechanical
audio speedup after TTS, default 1.3 — the "sped up AI narrator" sound).

2. Assemble:

```bash
set -a && source .env && set +a
python3 scripts/assemble.py stories/07.json out.mp4 7
```

The last argument is a seed that rotates which gameplay segments are used.
Takes ~2 minutes. The script chains: Gemini TTS voiceover → mechanical speedup
→ faster-whisper word timestamps → one-word-at-a-time ASS captions → question
card PNG → ffmpeg composite over gameplay.

## Celebrity drama rules

Real reporting only — never invented. Facts must come from reputable published
outlets, attributed softly in the narration ("reportedly", "according to court
filings"). Nothing about minors, no unverified allegations stated as fact,
no health/sexuality speculation. PG-13.

## Scripts

| Script | Job |
|---|---|
| `scripts/tts.py` | Gemini TTS voiceover (voices: Charon = deep male, Fenrir = excitable male, Kore = female) |
| `scripts/align.py` | Word-level timestamps (faster-whisper base.en) |
| `scripts/captions.py` | One-word-at-a-time ASS subtitles |
| `scripts/reddit_card.py` | Question card PNG (question, output path, optional account name) |
| `scripts/assemble.py` | Orchestrates everything |
| `scripts/prep_gameplay.py` | Cleans raw recordings into usable gameplay segments |

## Automation

`docs/daily-routine.md` is the prompt for a Claude scheduled task that runs
every morning: writes 2 fresh fictional stories, web-researches 2 real
celebrity stories, builds all 4 videos, and uploads them to Google Drive
("Variant Story Reels" / "Variant Celebrity Drama" folders) via rclone.
