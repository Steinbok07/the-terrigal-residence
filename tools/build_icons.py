"""Build the PNG/ICO favicons from the same design as assets/img/favicon.svg.

Usage:
    python tools/build_icons.py

Writes favicon.ico (site root, 16/32/48 px), assets/img/favicon-48.png
(the size Google Search prefers) and assets/img/apple-touch-icon.png (180 px).
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG, FG = "#2A2724", "#EAE1D3"
FONT = r"C:\Windows\Fonts\georgia.ttf"


def icon(px):
    s = px * 4  # draw large, then downsample for smooth edges
    im = Image.new("RGB", (s, s), BG)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, round(s * 38 / 64))
    # baseline at 45/64 of the height, as in favicon.svg
    d.text((s / 2, s * 45 / 64), "T", font=f, fill=FG, anchor="ms")
    return im.resize((px, px), Image.LANCZOS)


if __name__ == "__main__":
    icon(48).save(os.path.join(ROOT, "assets", "img", "favicon-48.png"), optimize=True)
    icon(180).save(os.path.join(ROOT, "assets", "img", "apple-touch-icon.png"), optimize=True)
    icon(256).save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    print("icons written")
