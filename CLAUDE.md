# Variant Story Reels

Reddit-story TikTok factory: AI voice reads a juicy Reddit-style confession with
word-by-word captions over Variant gameplay (the app that lets you create your
own mobile games). Modeled on the Minecraft-parkour "Story Time" format.

## Pipeline (all local, no paid services beyond Gemini)

1. Write a story JSON in `stories/NN.json`:
   `{"question": "...", "story": "...", "voice": "Charon"}`
   - assemble.py applies a 1.45x mechanical speedup after TTS by default
     (brainrot pacing, user-approved); override per-story with `"speed"`
   - Question: short, first-person bait ("What's something you'd never tell anyone?")
   - Story: 120–160 words, PG-13, first person, a twist mid-way, punchy last line
     ("I'm taking this one to the grave."). Short sentences — captions are one word at a time.
   - FIRST SENTENCE = the hook; must be shocking enough that a viewer can't
     scroll away (user requirement).
2. Assemble (finished videos go to `downloads/`):
   ```bash
   set -a && source ~/Projects/variant-love-island-reels/.env && set +a
   python3 scripts/assemble.py stories/NN.json downloads/NN.mp4 <seed>
   ```
   `seed` rotates which gameplay clip leads (use the story number).

`assemble.py` does everything: Gemini TTS voiceover (voices: Charon = deep male,
Fenrir = excitable male, Kore = female) → faster-whisper word timestamps →
ASS captions (big white Arial Black, pop-in) → Reddit card PNG shown while the
question is read → ffmpeg layers it over pre-cleaned segments in `gameplay/`
(override with `GAMEPLAY_DIR`).

Two content streams, two folders (mirrored locally and in Google Drive):
- Reddit stories (fictional): `stories/NN.json` → `~/Downloads/Story Reels/story-reel-NN.mp4`
  → Drive "Variant Story Reels"
- Celebrity drama (REAL, web-researched, reported facts only, soft attribution):
  `stories_celeb/NN.json` with `"card_name": "Celebrity Tea"` →
  `~/Downloads/Celebrity Drama/celeb-reel-NN.mp4` → Drive "Variant Celebrity Drama"
  - Celeb reels DEFAULT to the ElevenLabs woman's voice (no `voice`/`tts` needed
    in the JSON — the `"card_name": "Celebrity Tea"` marker triggers it).
  - Celeb b-roll is MIRRORED by default via `"mirror": true` in the JSON (flips
    the gameplay horizontally so the algorithm doesn't flag reused footage).
    Keep adding `"mirror": true` to new celeb stories.

A scheduled routine (`daily-variant-story-reels`, ~8am daily) makes 2 of each
per day and uploads via `~/.local/bin/rclone` (remote `gdrive:`, authorized
2026-07-15). User drops new raw recordings into `raw_gameplay/`; the routine
rebuilds `gameplay/` when it sees newer files there.
NOTE: rclone warns its shared Google client_id is being retired during 2026 —
if Drive uploads start failing, set up a personal client_id per
https://rclone.org/drive/#making-your-own-client-id

## Scripts

- `scripts/tts.py` — Gemini TTS (uses curl; python urllib hits SSL cert issues on this Mac)
- `scripts/align.py` — word timestamps (faster-whisper base.en, cpu/int8)
- `scripts/captions.py` — one-word-at-a-time ASS subtitles
- `scripts/reddit_card.py` — white rounded question card PNG
- `scripts/assemble.py` — orchestrates all of the above + ffmpeg

## Gameplay library

`gameplay/` holds pre-cleaned segments (1080x1920@30, no audio, no menus/dark
screens). When the user adds new raw recordings, rebuild it:
```bash
python3 scripts/prep_gameplay.py <raw_recordings_dir> gameplay
```
`prep_gameplay.py` auto-cuts near-black loading screens (luma < 50 by default;
some Variant games are dark ~60, so the floor is low) and frozen/static
stretches (menus), keeps segments >= 4s. Accepts .mp4/.mov/.m4v. Override the
brightness floor with the `YAVG_MIN` env var (raise for glarey footage, 0 = off).
NOTE: it wipes and rebuilds `gameplay/` each run.

## Known rough edges / next iterations

- No background music yet (drop MP3s in a `music/` dir and mix at ~15% volume).
- Only ~145s of gameplay total — backgrounds repeat across a big batch; user
  should record more pure-gameplay footage.
- GEMINI_API_KEY lives in `~/Projects/variant-love-island-reels/.env`.
- ElevenLabs voices: `ELEVENLABS_API_KEY` + voice IDs (`ELEVENLABS_VOICE_ID` =
  woman/tea, `ELEVENLABS_VOICE_ID_SPORTS_POLITICS`) live in this project's own
  `.env`. assemble.py auto-loads that `.env` (without overriding an already-set
  GEMINI key), so celeb reels get the ElevenLabs voice even if the caller only
  sourced the love-island `.env`. The key is TTS-only (can't list/read voices).
- Set a story's engine explicitly with `"tts": "elevenlabs"` or `"tts": "gemini"`
  and `"voice"` (an ElevenLabs voice ID, or a Gemini name like Charon).
- Voice speed: TTS prompt asks for rushed "Brian rot" delivery + mechanical
  1.45x speedup (assemble.py default, override per-story with "speed").
