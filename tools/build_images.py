"""Build the web-optimised photo set for The Terrigal Residence.

Usage:
    python tools/build_images.py "<folder containing the original PNGs>"

Each original is written to assets/img/photos/<slug>-<width>.webp at a few
widths (480, 960 and the original width), so browsers download only what
the screen needs. Originals are never modified. Also writes the social
sharing preview assets/img/og.jpg from the hero photograph.

To change a photo: replace the PNG in the source folder (same filename),
or edit PHOTOS below, then re-run this script.
"""
import os
import sys

from PIL import Image

PHOTOS = {
    # slug: original filename
    "terrigal-ocean-view-living-room": "Coastal Living Room with Ocean View.png",  # homepage hero
    "terrigal-three-level-residence-exterior": "Modern Coastal Townhouse Exterior.png",
    "terrigal-residence-double-garage": "Modern Coastal Home with Open Garage.png",
    "terrigal-sunlit-living-room-ocean-view": "Sunlit Coastal Glass Living Room.png",
    "terrigal-balcony-sunrise-ocean-view": "Sunrise Balcony Overlooking Terrigal.png",
    "terrigal-upper-level-room-ocean-view": "Bright Coastal Loft with Ocean Views.png",
    "terrigal-contemporary-kitchen": "Warm Minimalist Kitchen with Integrated Fridge.png",
    "terrigal-kitchen-waterfall-stone-benchtop": "Warm Minimalist U-Shaped Kitchen.png",
    "terrigal-master-bedroom-balcony-views": "Sunlit Bedroom with Coastal Views.png",
    "terrigal-bathroom-ribbed-timber-vanity": "Luxurious Ribbed Oak Vanity Bathroom.png",
    "terrigal-bathroom-fluted-bath": "Luxury Taupe Bathroom with Freestanding Tub.png",
    "terrigal-residence-timber-staircase": "Minimalist Coastal Stairwell with Warm Lighting.png",
    "terrigal-residence-stairwell-pendant": "Scandinavian Stairwell with Wicker Pendant.png",
    "terrigal-residence-private-internal-lift": "Modern Home Lift in Warm Minimalist Hallway.png",
    "terrigal-residence-laundry": "Scandinavian Oak Laundry Room.png",
    "terrigal-residence-private-courtyard": "Minimalist Courtyard with Linear Drains.png",
}
# Superseded and deliberately excluded: "Minimal Coastal Living Space with Ocean Views.png"

WIDTHS = (480, 960)
QUALITY = 82

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "img", "photos")


def main(src):
    os.makedirs(OUT, exist_ok=True)
    for slug, name in PHOTOS.items():
        im = Image.open(os.path.join(src, name)).convert("RGB")
        w, h = im.size
        widths = [x for x in WIDTHS if x < w] + [w]
        for tw in widths:
            th = round(h * tw / w)
            out = im if tw == w else im.resize((tw, th), Image.LANCZOS)
            out.save(os.path.join(OUT, f"{slug}-{tw}.webp"), "WEBP", quality=QUALITY, method=6)
        srcset = ", ".join(f"assets/img/photos/{slug}-{x}.webp {x}w" for x in widths)
        print(f"{slug:42} {w}x{h}  {srcset}")

    # Social preview, 1200x630, centred crop of the hero
    hero = Image.open(os.path.join(src, PHOTOS["terrigal-ocean-view-living-room"])).convert("RGB")
    w, h = hero.size
    ch = round(w * 630 / 1200)
    top = (h - ch) // 2
    hero.crop((0, top, w, top + ch)).resize((1200, 630), Image.LANCZOS).save(
        os.path.join(ROOT, "assets", "img", "og.jpg"), "JPEG", quality=85, optimize=True, progressive=True
    )
    print("og.jpg written")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
