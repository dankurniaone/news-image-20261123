#!/usr/bin/env python3
"""Render THE WORLD TODAY — a one-page broadsheet summing up the world news
of Tuesday 24 November 2026 — as a 680x1024 PNG.

Drawn at 2x (1360x2048) with Pillow and downscaled with LANCZOS so the
small type stays crisp. Layout: centred masthead and dateline, a lead story
with deck, photograph and two-column body, two stories side by side with a
vertical divider (the markets story carries a deal-terms box, the Nepal
story a photograph), a briefs strip, and a sources footer. All photographs
are freely licensed file photos, credited in the footer; none is from 24
November itself. Every story on the page is an event of 24 November 2026:
each was checked against primary reporting the same day.

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
# Final set (evening, 24 Nov). Every event below happened on 24 Nov 2026
# and was checked against primary reporting the same day: the Gaza strikes
# and the security chief's death were reported by Reuters on Tuesday 24 Nov;
# Sanofi announced its Insmed deal on Tuesday 24 Nov (company release,
# Reuters, WSJ); the Nepal quake struck at 07:17 local time on Tuesday
# 24 Nov (Nepal monitoring centre); the Shenzhou-24 crew was unveiled at
# Jiuquan on Tuesday 24 Nov; the Banten toll reached 26 on Tuesday 24 Nov;
# Kyiv announced the DELTA access for Germany on Tuesday 24 Nov.
LEAD = {
    "kicker": "GAZA · KHAN YOUNIS",
    "headline": "ISRAELI STRIKES KILL SIX IN GAZA",
    "deck": ("Israeli airstrikes killed at least six Palestinians across "
             "Gaza on Tuesday, and Gaza's interior ministry said its "
             "internal security chief had been killed."),
    "photo": os.path.join(ROOT, "assets", "gaza-rubble.jpg"),
    "photo_h": 96,
    "photo_focus": 0.5,
    "caption": "Rubble in Gaza. (File photo: Felton Davis, public domain)",
    "left": ("Three people were killed in a strike on a police post in "
             "Khan Younis in southern Gaza, two of them police officers, "
             "medics said; five more were wounded. Later on Tuesday a "
             "second strike near the Netzarim corridor killed three more."),
    "right": ("Gaza's interior ministry said on Tuesday that an Israeli "
              "strike had killed its internal security chief, Naim "
              "Mohammed Abu Nahl. The strikes came despite a US-backed "
              "ceasefire in effect since October, and as health officials "
              "declared a territory-wide meningitis alert."),
}

MIDDLE_LEFT = {
    "kicker": "MARKETS · SANOFI",
    "headline": "SANOFI TO BUY INSMED IN $41BN DEAL",
    "body": ("Sanofi said on Tuesday it will buy US biotech Insmed for "
             "$175 a share in cash, the biggest biotech deal in nearly "
             "three years. The French drugmaker gains two respiratory "
             "medicines, Brinsupri and Arikayce, and a late-stage pipeline "
             "as it prepares for patent expiries on its own blockbusters."),
    "stats": ["Price: $175 a share, $41.0bn in cash",
              "Premium: 46% to the 18 Nov close",
              "Closes: first half of 2027"],
}

MIDDLE_RIGHT = {
    "kicker": "NEPAL · TAPLEJUNG",
    "headline": "QUAKE SHAKES NEPAL'S FAR EAST",
    "photo": os.path.join(ROOT, "assets", "annapurna.jpg"),
    "photo_h": 64,
    "photo_focus": 0.75,
    "caption": "The Annapurna range, Nepal. (File photo: dave.see, CC BY)",
    "body": ("A magnitude 5.6 earthquake struck near Olangchung Gola in "
             "Taplejung district at 07:17 on Tuesday, Nepal's monitoring "
             "centre said, close to the border with Tibet. Tremors were "
             "felt in India, Bhutan and Bangladesh; no casualties or major "
             "damage had been reported."),
}

BRIEFS = [
    ("JIUQUAN", "China unveiled the Shenzhou-24 crew on Tuesday: Pakistani "
                "Muhammad Zeeshan Ali, 40, will be the first foreign "
                "astronaut aboard Tiangong; launch is Wednesday."),
    ("SERANG", "The toll from the 21 Nov candy-factory fire in Banten rose "
               "to 26 on Tuesday, police said; 28 workers are still "
               "missing and a criminal inquiry has been opened."),
    ("BERLIN", "Ukraine said on Tuesday that Germany will become the first "
               "foreign country to use its DELTA battlefield system; Kyiv "
               "will share no combat data."),
]

FOOT_SOURCES = ("All events on this page happened on Tuesday 24 November "
                "2026. Sources: Reuters; Sanofi; Nepal National Earthquake "
                "Monitoring and Research Centre; Xinhua; AP; Ukrinform; "
                "Banten Police.")
FOOT_PHOTOS = ("Photos are freely licensed file photos, not from today: "
               "Gaza rubble — Felton Davis, public domain; Annapurna — "
               "dave.see, CC BY.")


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
    t = "TUESDAY, 24 NOVEMBER 2026"
    d.text(((W - d.textlength(t, font=f_date)) / 2, y), t, font=f_date, fill=INK)
    y += int(15 * SCALE * 1.6)

    f_sub = font(SANS, 11)
    t = "ONE DAY  ·  ONE PAGE  ·  No. 328"
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
            img.paste(crop_cover(im, col_w, ph2,
                                 focus=s.get("photo_focus", 0.5)), (cx, yy))
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
    out.save(os.path.join(ROOT, "entry.png"), "PNG", optimize=True)
    print("wrote entry.png", out.size,
          os.path.getsize(os.path.join(ROOT, "entry.png")), "bytes,",
          "content ends at y =", y // SCALE, "(logical)")


if __name__ == "__main__":
    main()
