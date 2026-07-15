---
name: daily-variant-story-reels
description: Make 2 Reddit-story reels + 2 real celebrity-drama reels every morning, saved to Downloads and Google Drive
---

Make 4 new Variant TikTok reels: 2 Reddit-story reels and 2 REAL celebrity-drama reels. Follow these steps exactly.

Project: ~/Projects/variant-story-reels (pipeline docs in its CLAUDE.md; the variant-story-reels skill also describes this workflow — follow whichever is present).

1. Load the Gemini API key: `set -a && source ~/Projects/variant-love-island-reels/.env && set +a` (needs GEMINI_API_KEY).

2. Check for new gameplay footage: if any file in ~/Projects/variant-story-reels/raw_gameplay/ is newer than the newest file in ~/Projects/variant-story-reels/gameplay/, re-run:
   `python3 scripts/prep_gameplay.py raw_gameplay gameplay`
   (This cuts out dark/static parts and keeps only lively gameplay.)

3. REDDIT-STORY REELS (2): write 2 NEW stories as stories/NN.json (next free numbers; look at existing files to avoid reusing numbers). Format:
   {"question": "...", "story": "...", "voice": "Charon"}
   Rules:
   - Read 2-3 existing stories in stories/ first and make the new ones DIFFERENT in topic (rotate themes: childhood secrets, petty revenge, workplace chaos, family drama, dumb lies that spiraled, money stories, roommate stories, school stories).
   - The FIRST SENTENCE is the hook and must be shocking/irresistible on its own (e.g. "I got paid three hundred dollars to cry at a stranger's funeral."). Viewer must not be able to scroll away.
   - PG-13, funny or jaw-dropping, never gross or mean-spirited. 120-160 words. Punchy last line.
   - The "question" is a Reddit-style prompt the story answers.
   Generate each:
   `python3 scripts/assemble.py stories/NN.json "$HOME/Downloads/Story Reels/story-reel-NN.mp4" NN`
   (run from ~/Projects/variant-story-reels; third arg = story number, it varies which gameplay is used)

4. CELEBRITY-DRAMA REELS (2): these must be REAL, currently-reported stories — never invented.
   - Use web search to find 2 celebrity drama stories being reported TODAY or this week by mainstream/entertainment outlets (feuds, lawsuits, breakups, award-show moments, viral incidents).
   - ONLY include facts that appear in reputable published reporting; attribute softly in the narration ("reportedly", "according to court filings"). Nothing about minors, no unverified allegations stated as fact, no health/sexuality speculation. PG-13.
   - Check stories_celeb/ for recent files and DO NOT repeat a story already covered.
   - Write each as stories_celeb/NN.json (next free numbers). Format:
     {"question": "...", "card_name": "Celebrity Tea", "story": "...", "voice": "Charon"}
   - Same hook rule: first sentence must stop the scroll ("Blake Lively just sent Justin Baldoni a bill for eight million dollars."). 120-170 words, punchy last line.
   Generate each:
   `python3 scripts/assemble.py stories_celeb/NN.json "$HOME/Downloads/Celebrity Drama/celeb-reel-NN.mp4" NN`

5. Verify: each of the 4 outputs exists, is >5 MB, and ffprobe shows duration roughly 20-60s. Extract one frame from each and confirm gameplay with captions, not a black/grey screen.

6. Upload to Google Drive (already connected via rclone; re-running is safe — it only uploads new files):
   `~/.local/bin/rclone copy "$HOME/Downloads/Story Reels" "gdrive:Variant Story Reels"`
   `~/.local/bin/rclone copy "$HOME/Downloads/Celebrity Drama" "gdrive:Variant Celebrity Drama"`

7. Report: one short plain-English summary — the hook line of each reel, which folder each is in, and confirmation they're in both Downloads and Google Drive. For celebrity reels, include the news sources used. The user is non-technical; no jargon, no code in the summary.
