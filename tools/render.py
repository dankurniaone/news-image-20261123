#!/usr/bin/env python3
"""Render THE WORLD TODAY — a one-page broadsheet summing up the world news
of Monday 23 November 2026 — as a 680x1024 PNG.

Drawn at 2x (1360x2048) with Pillow and downscaled with LANCZOS so the
small type stays crisp. Layout: centred masthead and dateline, a lead story
with deck, photograph and two-column body, two stories side by side with a
vertical divider, a briefs strip, and a sources footer. All photographs are
freely licensed file photos, credited in the footer; none is from 23 November
itself. Every story on the page is an event of 23 November 2026.

Run:  python3 tools/render.py   (writes entry.png next to main.py)
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SCALE = 2
W, H = 680 * SCALE, 1024 * SCALE
MARGIN = 28 * SCALE
CW = W - 2 * MARGIN  # content width

PAPER = (246, 242, 231)   # warm newsprint
INK = (17, 17, 17)
RED = (164, 30, 34)
GREY = (90, 86, 78)

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size * SCALE)


def wrap(text, fnt, width, draw):
    """Greedy word wrap to a pixel width; returns a list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, x, y, lines, fnt, fill=INK, leading=None):
    """Draw lines top to bottom; returns the y below the last line."""
    lh = leading if leading is not None else int(fnt.size * 1.35)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def crop_cover(img, tw, th, focus=0.5):
    """Centre-crop an image to the target aspect, then resize to it.
    focus 0.0 takes the top of the frame, 1.0 the bottom, 0.5 the centre."""
    iw, ih = img.size
    ta = tw / th
    ia = iw / ih
    if ia > ta:  # too wide: trim sides
        nw = int(ih * ta)
        x0 = (iw - nw) // 2
        img = img.crop((x0, 0, x0 + nw, ih))
    else:  # too tall: trim top/bottom around the focus point
        nh = int(iw / ta)
        y0 = max(0, min(ih - nh, int((ih - nh) * focus)))
        img = img.crop((0, y0, iw, y0 + nh))
    return img.resize((tw, th), Image.LANCZOS)


def tracked(draw, x, y, text, fnt, fill, tracking=0):
    """Draw text with extra space between characters; returns end x."""
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


# ---------------------------------------------------------------- stories
# Final set (afternoon, 23 Nov). Every event below happened on 23 Nov 2026
# and was checked against primary reporting the same day: the Wellington
# Test ended in a draw, the Nepal–Modi talks were held at Hyderabad House,
# Tata Steel announced its APL Apollo deal, and Bitcoin held above $60,900.
LEAD = {
    "kicker": "NEPAL · NEW DELHI",
    "headline": "SHAH AND MODI HOLD DELHI TALKS",
    "deck": ("Nepal's prime minister holds delegation-level talks with "
             "Narendra Modi in New Delhi, seeking a $2bn package to rebuild "
             "after August's floods and a long-term vision for the "
             "partnership."),
    "photo": os.path.join(ROOT, "assets", "india-gate.jpg"),
    "photo_h": 104,
    "photo_focus": 0.0,
    "caption": "India Gate, New Delhi. (File photo: Larry Johnson, CC BY)",
    "left": ("Shah, who took office in March, arrived in New Delhi on Sunday "
             "for a two-day state visit, his first bilateral trip abroad. On "
             "Monday he received a ceremonial welcome at Rashtrapati Bhavan "
             "and called on President Droupadi Murmu before the talks."),
    "right": ("The two leaders agreed to issue a joint vision document, "
              "\"Samriddha Nepal, Samunnat Bharat\" — Prosperous Nepal, "
              "Developed India — and flag off the Sarayu–Kamala Express to "
              "Janakpur. Kathmandu sought a $2bn package, about $1bn of it "
              "in grants."),
}

MIDDLE_LEFT = {
    "kicker": "CRICKET · WELLINGTON",
    "headline": "NEW ZEALAND BAT OUT THE DAY TO SAVE THE TEST",
    "photo": os.path.join(ROOT, "assets", "basin-reserve.jpg"),
    "photo_h": 72,
    "caption": "Basin Reserve, Wellington, 1981. (File photo: Archives NZ, CC BY)",
    "body": ("Daryl Mitchell, 49 not out, and Glenn Phillips, 26 not out, "
             "batted out the final session as New Zealand finished 239 for 5 "
             "to draw the first Test. India, who declared at 720 for 9, took "
             "three wickets on the final day but fell five short. The draw "
             "dents India's World Test Championship hopes."),
}

MIDDLE_RIGHT = {
    "kicker": "MARKETS · TATA STEEL",
    "headline": "TATA STEEL TO TAKE CONTROL OF APL APOLLO",
    "body": ("Tata Steel said on Monday it will buy a 26.38% promoter stake "
             "in APL Apollo Tubes for Rs 15,510 crore and offer to buy a "
             "further 26% — a holding that could reach 52.38%. The first "
             "9.91% changed hands in a Rs 5,825 crore block deal today."),
    "stats": ["Promoter stake: 26.38% at Rs 2,100 a share",
              "Open offer: 26% at Rs 2,301.40 a share",
              "Control could reach 52.38%"],
}

BRIEFS = [
    ("NEW DELHI", "Shah flies home this evening, departing New Delhi at 18:35 "
                  "after the talks and the official luncheon."),
    ("CHRISTCHURCH", "The second and final Test of the series starts on "
                      "Friday at Hagley Oval, Christchurch."),
    ("MARKETS", "Bitcoin held above $60,900, a second day of gains after "
                "the weekend's two-year low near $55,130."),
]

FOOT_SOURCES = ("All events on this page happened on Monday 23 November 2026. "
                "Sources: Ministry of External Affairs (India); Nepal Ministry "
                "of Foreign Affairs; IANS; ESPN; Moneycontrol; CNBC-TV18; "
                "Reuters.")
FOOT_PHOTOS = ("Photos are freely licensed file photos, not from today: India "
               "Gate — Larry Johnson, CC BY; Basin Reserve — Archives New "
               "Zealand, CC BY.")


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x = MARGIN
    y = 18 * SCALE

    # ---- Masthead ----
    f_mast = font(SERIF_B, 48)
    t = "THE WORLD TODAY"
    d.text(((W - d.textlength(t, font=f_mast)) / 2, y), t, font=f_mast, fill=INK)
    y += int(48 * SCALE * 1.25)

    f_date = font(SANS_B, 15)
    t = "MONDAY, 23 NOVEMBER 2026"
    d.text(((W - d.textlength(t, font=f_date)) / 2, y), t, font=f_date, fill=INK)
    y += int(15 * SCALE * 1.6)

    f_sub = font(SANS, 11)
    t = "ONE DAY  ·  ONE PAGE  ·  No. 327"
    d.text(((W - d.textlength(t, font=f_sub)) / 2, y), t, font=f_sub, fill=GREY)
    y += int(11 * SCALE * 1.6) + 6 * SCALE

    d.rectangle([x, y, x + CW, y + 3 * SCALE], fill=INK)
    y += 5 * SCALE
    d.rectangle([x, y, x + CW, y + 1 * SCALE], fill=INK)
    y += 8 * SCALE

    # ---- Lead ----
    f_kick = font(SANS_B, 13)
    tracked(d, x, y, LEAD["kicker"], f_kick, RED, tracking=2)
    y += int(13 * SCALE * 1.7)

    f_head = font(SERIF_B, 46)
    y = draw_lines(d, x, y, wrap(LEAD["headline"], f_head, CW, d), f_head,
                   leading=int(46 * SCALE * 1.12))
    y += 2 * SCALE

    f_deck = font(SERIF, 16)
    y = draw_lines(d, x, y, wrap(LEAD["deck"], f_deck, CW, d), f_deck,
                   leading=int(16 * SCALE * 1.45))
    y += 4 * SCALE

    lead_photo = Image.open(LEAD["photo"]).convert("RGB")
    ph = LEAD["photo_h"] * SCALE
    img.paste(crop_cover(lead_photo, CW, ph, focus=LEAD.get("photo_focus", 0.5)),
              (x, y))
    y += ph + 4 * SCALE
    f_cap = font(SERIF_I, 11)
    d.text((x, y), LEAD["caption"], font=f_cap, fill=GREY)
    y += int(11 * SCALE * 1.7) + 2 * SCALE

    # Lead body, two columns
    f_body = font(SERIF, 13)
    col_w = (CW - 20 * SCALE) // 2
    lh = int(13 * SCALE * 1.5)
    y1 = draw_lines(d, x, y, wrap(LEAD["left"], f_body, col_w, d), f_body,
                    leading=lh)
    y2 = draw_lines(d, x + col_w + 20 * SCALE, y,
                    wrap(LEAD["right"], f_body, col_w, d), f_body, leading=lh)
    y = max(y1, y2) + 6 * SCALE

    d.rectangle([x, y, x + CW, y + 1 * SCALE], fill=INK)
    y += 8 * SCALE

    # ---- Middle: two stories side by side ----
    mid_y = y
    col_w = (CW - 20 * SCALE) // 2
    f_mid_head = font(SERIF_B, 24)

    def story(cx, s):
        yy = mid_y
        tracked(d, cx, yy, s["kicker"], f_kick, RED, tracking=2)
        yy += int(13 * SCALE * 1.7)
        yy = draw_lines(d, cx, yy, wrap(s["headline"], f_mid_head, col_w, d),
                        f_mid_head, leading=int(24 * SCALE * 1.12))
        yy += 3 * SCALE
        if "photo" in s:
            im = Image.open(s["photo"]).convert("RGB")
            ph2 = s["photo_h"] * SCALE
            img.paste(crop_cover(im, col_w, ph2), (cx, yy))
            yy += ph2 + 4 * SCALE
            d.text((cx, yy), s["caption"], font=f_cap, fill=GREY)
            yy += int(11 * SCALE * 1.7) + 2 * SCALE
        yy = draw_lines(d, cx, yy, wrap(s["body"], f_body, col_w, d), f_body,
                        leading=lh)
        if "stats" in s:
            yy += 4 * SCALE
            f_stat_h = font(SANS_B, 10)
            f_stat = font(SANS, 11)
            box_h = (int(10 * SCALE * 1.6) + len(s["stats"]) * int(11 * SCALE * 1.5)
                     + 8 * SCALE)
            d.rectangle([cx, yy, cx + col_w, yy + box_h], outline=INK, width=1 * SCALE)
            yy += 4 * SCALE
            d.text((cx + 6 * SCALE, yy), "AT A GLANCE", font=f_stat_h, fill=RED)
            yy += int(10 * SCALE * 1.6)
            for st in s["stats"]:
                d.text((cx + 6 * SCALE, yy), st, font=f_stat, fill=INK)
                yy += int(11 * SCALE * 1.5)
            yy += 4 * SCALE
        return yy

    y_left = story(x, MIDDLE_LEFT)
    y_right = story(x + col_w + 20 * SCALE, MIDDLE_RIGHT)
    y = max(y_left, y_right)
    # vertical divider between the two middle stories
    div_x = x + col_w + 10 * SCALE
    d.rectangle([div_x, mid_y, div_x + 1 * SCALE, y - 4 * SCALE], fill=INK)
    y += 6 * SCALE

    d.rectangle([x, y, x + CW, y + 1 * SCALE], fill=INK)
    y += 8 * SCALE

    # ---- The day in brief ----
    f_brief_h = font(SANS_B, 13)
    tracked(d, x, y, "THE DAY IN BRIEF", f_brief_h, INK, tracking=2)
    y += int(13 * SCALE * 1.8)
    n = len(BRIEFS)
    gap = 16 * SCALE
    bw = (CW - (n - 1) * gap) // n
    f_bh = font(SANS_B, 12)
    f_bb = font(SERIF, 13)
    yb = y
    for i, (h, b) in enumerate(BRIEFS):
        bx = x + i * (bw + gap)
        d.text((bx, y), h, font=f_bh, fill=RED)
        yy = draw_lines(d, bx, y + int(12 * SCALE * 1.7),
                        wrap(b, f_bb, bw, d), f_bb, leading=int(13 * SCALE * 1.45))
        yb = max(yb, yy)
    y = yb + 8 * SCALE

    d.rectangle([x, y, x + CW, y + 1 * SCALE], fill=INK)
    y += 6 * SCALE

    # ---- Footer ----
    f_foot = font(SANS, 8)
    y = draw_lines(d, x, y, wrap(FOOT_SOURCES, f_foot, CW, d), f_foot,
                   fill=GREY, leading=int(8 * SCALE * 1.55))
    y = draw_lines(d, x, y + 2 * SCALE, wrap(FOOT_PHOTOS, f_foot, CW, d),
                   f_foot, fill=GREY, leading=int(8 * SCALE * 1.55))

    out = img.resize((680, 1024), Image.LANCZOS)
    out.save(os.path.join(ROOT, "entry.png"), "PNG")
    print("wrote entry.png", out.size,
          os.path.getsize(os.path.join(ROOT, "entry.png")), "bytes,",
          "content ends at y =", y // SCALE, "(logical)")


if __name__ == "__main__":
    main()
