#!/usr/bin/env python3
"""Render a Reddit-style question card PNG (transparent background).

Usage: python3 reddit_card.py "<question text>" <out.png> [username]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

CARD_W = 860
PAD = 44
SCALE = 2  # render 2x then downsample for crisp edges

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def wrap(draw, text, font, max_w):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def main():
    question = sys.argv[1]
    out_path = sys.argv[2]
    username = sys.argv[3] if len(sys.argv) > 3 else "Story Time"

    s = SCALE
    name_font = ImageFont.truetype(FONT_BOLD, 30 * s)
    q_font = ImageFont.truetype(FONT_BOLD, 40 * s)
    meta_font = ImageFont.truetype(FONT_REG, 28 * s)

    tmp = Image.new("RGBA", (10, 10))
    tdraw = ImageDraw.Draw(tmp)
    text_w = (CARD_W - 2 * PAD) * s
    lines = wrap(tdraw, question, q_font, text_w)
    line_h = int(52 * s)

    header_h = 92
    footer_h = 88
    card_h = header_h + len(lines) * (line_h // s) + footer_h + 24

    img = Image.new("RGBA", (CARD_W * s, card_h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # white card with rounded corners
    d.rounded_rectangle(
        [0, 0, CARD_W * s - 1, card_h * s - 1], radius=28 * s,
        fill=(255, 255, 255, 255),
    )

    # avatar: orange circle with white book-ish glyph
    ax, ay, ar = PAD * s + 26 * s, 46 * s, 26 * s
    d.ellipse([ax - ar, ay - ar, ax + ar, ay + ar], fill=(59, 130, 246, 255))
    d.rounded_rectangle(
        [ax - 13 * s, ay - 9 * s, ax + 13 * s, ay + 9 * s],
        radius=4 * s, outline=(255, 255, 255, 255), width=3 * s,
    )
    d.line([ax, ay - 9 * s, ax, ay + 9 * s], fill=(255, 255, 255, 255), width=3 * s)

    # username + verified badge
    nx = ax + ar + 18 * s
    d.text((nx, ay), username, font=name_font, fill=(20, 20, 20, 255), anchor="lm")
    name_w = d.textlength(username, font=name_font)
    bx = nx + name_w + 14 * s + 12 * s
    d.ellipse([bx - 12 * s, ay - 12 * s, bx + 12 * s, ay + 12 * s], fill=(29, 155, 240, 255))
    d.line([bx - 6 * s, ay, bx - 2 * s, ay + 5 * s], fill=(255, 255, 255, 255), width=3 * s)
    d.line([bx - 2 * s, ay + 5 * s, bx + 6 * s, ay - 5 * s], fill=(255, 255, 255, 255), width=3 * s)

    # question text
    y = header_h * s
    for ln in lines:
        d.text((PAD * s, y), ln, font=q_font, fill=(10, 10, 10, 255))
        y += line_h

    # footer: upvote 999+ / comment 999+ / share
    fy = y + 30 * s
    gray = (90, 90, 90, 255)
    # up arrow
    d.polygon([(PAD * s, fy + 8 * s), (PAD * s + 12 * s, fy - 8 * s),
               (PAD * s + 24 * s, fy + 8 * s)], outline=gray, width=3 * s)
    d.line([(PAD * s + 12 * s, fy + 8 * s), (PAD * s + 12 * s, fy + 16 * s)],
           fill=gray, width=3 * s)
    d.text((PAD * s + 36 * s, fy + 2 * s), "999+", font=meta_font, fill=gray, anchor="lm")
    # comment bubble
    cx = PAD * s + 170 * s
    d.rounded_rectangle([cx, fy - 10 * s, cx + 30 * s, fy + 10 * s],
                        radius=8 * s, outline=gray, width=3 * s)
    d.polygon([(cx + 6 * s, fy + 10 * s), (cx + 6 * s, fy + 18 * s),
               (cx + 16 * s, fy + 10 * s)], fill=gray)
    d.text((cx + 42 * s, fy + 2 * s), "999+", font=meta_font, fill=gray, anchor="lm")
    # share (right aligned)
    share_w = d.textlength("Share", font=meta_font)
    sx = (CARD_W - PAD) * s - share_w - 40 * s
    d.polygon([(sx, fy + 6 * s), (sx + 14 * s, fy - 8 * s), (sx + 28 * s, fy + 6 * s)],
              outline=gray, width=3 * s)
    d.text((sx + 40 * s, fy + 2 * s), "Share", font=meta_font, fill=gray, anchor="lm")

    img = img.resize((CARD_W, card_h), Image.LANCZOS)
    img.save(out_path)
    print(f"wrote {out_path} ({CARD_W}x{card_h})")


if __name__ == "__main__":
    main()
