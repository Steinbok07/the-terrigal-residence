"""Build the marketing floor plans for The Terrigal Residence from the CDC drawings.

Usage:
    python tools/build_floorplans.py "<folder containing the three CDC PDFs>" [<pdf review folder>]

What it does
  * Reads the architect's vector linework straight out of the PDFs (no tracing),
    so walls, doors, windows, stairs and fixtures keep their drawn positions.
  * Keeps only the residence being marketed (the right-hand one on the drawings)
    by clipping each level to its footprint.
  * Drops the technical layers: demolition (red), hatches (orange/pink),
    section markers (blue), dashed lines, all drawing text, smoke-alarm
    symbols, door tags and annotation leaders.
  * Re-sets room names from the drawing's own labels, in the site's style.
  * Writes plan-<level>.svg into assets/floorplans/ (shown on the website,
    view-only and zoomable; the site deliberately offers no downloads).
  * Optionally writes PDF versions to a review folder OUTSIDE the website, so
    they are never published: plan-<level>.pdf and a combined set.

Nothing is invented: if a room isn't labelled on the drawings it isn't labelled
here, and no dimensions are added beyond those on the drawings.
"""
import math
import os
import sys

import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "floorplans")

PT_TO_M = 25.4 / 72 * 100 / 1000  # 1:100 at A3: 1 pt on paper = 0.035278 m

# Palette (matches assets/css/style.css)
BG = "#FBF9F5"
INK = "#2B2825"
PATTERN = "#E3DACB"
SOFT = "#B5AB9E"
BRONZE = "#8C6A47"
LIFT = "#E8DCC8"  # tone for the (unlabelled) hatched shaft read as the lift
MUTED = "#7B7268"

# ---------------------------------------------------------------- levels
# Clip regions are unions of non-overlapping rectangles in PDF points.
# Labels: (text, x, y) at the centre of the drawing's own room label.
LEVELS = [
    {
        "id": "garage", "name": "Garage", "rl": "57.770",
        "pdf": "Ground 02.pdf",
        "clip": [(432.8, 209, 662, 428.5), (386, 428.5, 662, 571.5)],
        "labels": [("Garage", 577.4, 411.8), ("Cellar", 460.3, 382.6), ("Lobby", 508.6, 312),
                   ("Common entry foyer", 437.5, 529.5), ("Lift", 461.5, 305)],
        "drop": [], "drop_idx": [], "lift": True,
    },
    {
        "id": "lower-ground", "name": "First Floor", "rl": "61.258",
        "pdf": "Lower ground - Ground.pdf",
        "clip": [(413.4, 238, 642, 378), (377.5, 378, 642, 550), (459.5, 550, 642, 612)],
        "labels": [("Kitchen", 566.3, 313.1), ("Dining", 558.6, 403), ("Lounge", 557.7, 479.8),
                   ("Balcony", 560, 567), ("Common stair", 418.8, 470), ("Lift", 443.5, 352)],
        "drop": [(468, 384, 492, 404)],  # D01 door tag
        # dimension strings 750, 6,676 / 240 and 1,211
        "drop_idx": list(range(21924, 21948)), "lift": True,
    },
    {
        "id": "ground", "name": "Second Floor", "rl": "64.450",
        "pdf": "Lower ground - Ground.pdf",
        "clip": [(897.5, 117, 1127, 452), (946, 452, 1127, 622)],
        "labels": [("Bedroom 2", 1069.9, 175.8), ("Laundry", 1006.1, 165.8), ("Bedroom 3", 945, 220.7),
                   ("Bathroom", 1071.5, 270.3), ("Ensuite", 1071.5, 343.4), ("Robe", 1071.4, 400.2),
                   ("Family room", 970.2, 343), ("Bedroom 1", 1063.7, 457), ("Balcony", 1062, 588),
                   ("Lift", 927.2, 428.2)],
        # The lift is not hatched on this sheet. Owner confirmed it serves Garage, First and
        # Second floors; its shaft here is the First Floor (Lower Ground) hatch moved by the
        # stair-to-stair offset between the two plans (+484.6, +76.3). It lands on the winders
        # the drawing marks for demolition, beside the pink head-height zone.
        "lift_rect": (906.0, 408.3, 948.5, 448.1),
        "drop": [(1002, 188, 1026, 218), (1002, 376, 1026, 405)],  # smoke alarms
        # 1,186 dimension; leaders for the louver-door, privacy-screen and louver-window notes
        "drop_idx": list(range(13226, 13237)) + list(range(13244, 13253)) + list(range(13261, 13265)),
        # leftover pieces of the dashed ceiling-rake triangle in Bedroom 1
        "drop_short": [((998, 470, 1125, 612), 9, True)],
    },
    {
        "id": "first", "name": "Third Floor", "rl": "67.130",
        "pdf": "Ground 02.pdf",
        "clip": [(916.5, 256, 1146, 548)],
        "labels": [("Ensuite", 1101, 289), ("Study / Bedroom 4", 1025.6, 347.4), ("Store", 1081.2, 403.7),
                   ("Balcony", 970.9, 454.5)],
        "drop": [(1046, 272, 1072, 302), (1080, 295, 1104, 313)],  # smoke alarm, D02 tag
        "drop_idx": list(range(5584, 5590)),  # leaders for the stub-wall and privacy-screen notes
        "drop_short": [((1040, 410, 1116, 456), 12, False)],  # dashed outlines in the store
    },
]

SECTION = {
    "id": "section", "name": "Section", "pdf": "Section.pdf",
    # left strip stops above the cross-section drawn beside this one on the sheet
    "clip": [(478, 90, 540, 290), (540, 90, 1076, 482)],
    "drop": [(934, 38, 1150, 214)],  # council stamp box
    # dimensions written on the section (text, centre x, centre y, rotated?)
    "dims": [("3,488", 746.8, 418.7, 1), ("1,878", 746.8, 342.8, 1), ("1,314", 746.8, 297.5, 1),
             ("2,680", 746.8, 240.9, 1), ("2,400", 746.8, 169, 1), ("870", 746.8, 122.6, 1),
             ("3,488", 723, 418.7, 1), ("2,668", 723, 331.4, 1), ("524", 723, 302.8, 1),
             ("2,680", 723, 240.9, 1), ("2,400", 723, 169, 1), ("870", 723, 122.6, 1),
             ("3,031", 675.6, 252.9, 0), ("3,645", 770.2, 256.6, 0), ("1,201", 686.8, 265.1, 0)],
    "levels": [("Garage", "57.770", 466), ("First Floor", "61.258", 367.4),
               ("Second Floor", "64.450", 277), ("Third Floor", "67.130", 201),
               ("Existing ceiling", "69.530", 132.8), ("Existing ridge", "70.400", 108.2)],
}

# North point: the drawings' arrow points to sheet-right, rotated 8.8° clockwise.
NORTH_DEG = 8.8



# ---------------------------------------------------------------- geometry
def flatten(items):
    """Turn a drawing's items into polylines (lists of (x, y))."""
    lines, cur = [], []

    def push(a, b):
        nonlocal cur
        if cur and math.dist(cur[-1], a) < 0.01:
            cur.append(b)
        else:
            if len(cur) > 1:
                lines.append(cur)
            cur = [a, b]

    for it in items:
        kind = it[0]
        if kind == "l":
            push((it[1].x, it[1].y), (it[2].x, it[2].y))
        elif kind == "c":
            p0, p1, p2, p3 = [(p.x, p.y) for p in it[1:5]]
            n = max(4, int(math.dist(p0, p3) / 1.2))
            prev = p0
            for i in range(1, n + 1):
                t = i / n
                pt = tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
                           for a, b, c, d in zip(p0, p1, p2, p3))
                push(prev, pt)
                prev = pt
        elif kind == "re":
            r = it[1]
            pts = [(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)]
            for a, b in zip(pts, pts[1:]):
                push(a, b)
        elif kind == "qu":
            q = it[1]
            pts = [(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y), (q.ul.x, q.ul.y)]
            for a, b in zip(pts, pts[1:]):
                push(a, b)
    if len(cur) > 1:
        lines.append(cur)
    return lines


def clip_segment(a, b, r):
    """Liang–Barsky clip of segment ab to rect r=(x0,y0,x1,y1)."""
    x0, y0, x1, y1 = r
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return None
    return ((a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy))


def clip_polyline(pl, rects):
    out = []
    for r in rects:
        run = []
        for a, b in zip(pl, pl[1:]):
            s = clip_segment(a, b, r)
            if s is None:
                if len(run) > 1:
                    out.append(run)
                run = []
                continue
            if run and math.dist(run[-1], s[0]) < 0.01:
                run.append(s[1])
            else:
                if len(run) > 1:
                    out.append(run)
                run = [s[0], s[1]]
        if len(run) > 1:
            out.append(run)
    return out


def clip_polygon(poly, r):
    """Sutherland–Hodgman clip of a closed polygon to rect r."""
    x0, y0, x1, y1 = r
    edges = [(lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
             (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))]
    pts = poly
    for inside, cross in edges:
        if not pts:
            break
        res = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    res.append(cross(prev, cur))
                res.append(cur)
            elif inside(prev):
                res.append(cross(prev, cur))
        pts = res
    return pts if len(pts) >= 3 else None


def bbox_in(r, box):
    return r.x0 >= box[0] and r.y0 >= box[1] and r.x1 <= box[2] and r.y1 <= box[3]


def rects_touch(r, rects):
    return any(not (r.x1 < x0 or r.x0 > x1 or r.y1 < y0 or r.y0 > y1) for x0, y0, x1, y1 in rects)


def near(c, ref, tol=0.03):
    return c is not None and all(abs(a - b) <= tol for a, b in zip(c, ref))


def classify(d, section=False, lift=False):
    """Map a source drawing to a style, or None to drop it."""
    fill, color = d.get("fill"), d.get("color")
    dashed = bool(d.get("dashes")) and d["dashes"] not in ("[] 0", "[] 0.0")
    if d["type"] == "f" or (d["type"] == "fs" and fill):
        if near(fill, (0, 0, 0)):
            return ("fill", INK)
        if near(fill, (1, 1, 1)):
            return ("fill", BG)
        if lift and near(fill, (1, 0.4, 0)):
            return ("fill", LIFT)
        return None  # orange / pink hatch, legend swatches
    if color is None or dashed:
        return None
    w = d.get("width") or 0.36
    if near(color, (0, 0, 0)):
        return ("stroke", INK, w)
    if near(color, (1, 1, 1)):
        return ("stroke", BG, w)
    if near(color, (0.91, 0.91, 0.91)) or near(color, (0.8, 0.8, 0.8)):
        return ("stroke", PATTERN, 0.3)
    if near(color, (0.67, 0.67, 0.67)):
        return ("stroke", SOFT, 0.4)
    if section:
        if near(color, (0.41, 0.7, 0.33)):  # slab hatch
            return ("stroke", PATTERN, 0.3)
        if near(color, (0.75, 0.57, 0.49)) or near(color, (1, 0.6, 0.33)):  # wall / framing hatch
            return ("stroke", SOFT, 0.3)
        if near(color, (0.5, 0.25, 0.25)) or near(color, (1, 0.4, 0)):  # roof line, new framing
            return ("stroke", INK, w)
        if near(color, (0.42, 0.42, 0.42)) or near(color, (0.5, 0.5, 0.5)):
            return ("stroke", SOFT, 0.4)
    return None  # red demolition, blue section lines, etc.


def text_boxes(page):
    boxes = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            if any(sp["text"].strip() for sp in l["spans"]):
                boxes.append(pymupdf.Rect(l["bbox"]))
    return boxes


def dash_runs(drawings):
    """Indices of drawings that are pieces of dashed / dash-dot lines.

    The CDC files store dashed lines as many separate short segments, so they
    are found by grouping short collinear segments separated by regular gaps."""
    segs = {}
    for i, d in enumerate(drawings):
        if (d["type"] != "s" or len(d["items"]) != 1 or d["items"][0][0] != "l"
                or not near(d.get("color"), (0, 0, 0))):
            continue
        a, b = d["items"][0][1], d["items"][0][2]
        L = math.dist(a, b)
        if L > 12:
            continue
        ang = round(math.degrees(math.atan2(b.y - a.y, b.x - a.x)) % 180, 0) % 180
        th = math.radians(ang)
        nx, ny = -math.sin(th), math.cos(th)
        off = round((a.x * nx + a.y * ny) * 2) / 2  # 0.5 pt bins
        t0 = a.x * math.cos(th) + a.y * math.sin(th)
        t1 = b.x * math.cos(th) + b.y * math.sin(th)
        segs.setdefault((ang, off, d.get("color")), []).append((min(t0, t1), max(t0, t1), i))
    out, keys = set(), set()
    for key, runs in segs.items():
        runs.sort()
        chain = [runs[0]]
        def flush(ch):
            if len(ch) >= 3:
                gaps = [b[0] - a[1] for a, b in zip(ch, ch[1:])]
                if all(0.6 <= g <= 12 for g in gaps):
                    out.update(x[2] for x in ch); keys.add(key)
        for r in runs[1:]:
            g = r[0] - chain[-1][1]
            if 0.6 <= g <= 12:
                chain.append(r)
            else:
                flush(chain); chain = [r]
        flush(chain)
    # stray pieces of the same dashed lines (split where text or masks crossed them)
    for key in keys:
        out.update(x[2] for x in segs[key] if x[1] - x[0] < 9)
    return out


def short_line_in(d, zones):
    if (d["type"] != "s" or len(d["items"]) != 1 or d["items"][0][0] != "l"
            or not near(d.get("color"), (0, 0, 0))):
        return False
    a, b = d["items"][0][1], d["items"][0][2]
    L = math.dist(a, b)
    diag = abs(a.x - b.x) > .3 and abs(a.y - b.y) > .3
    return any(bbox_in(d["rect"], z) and L < mx and (diag or not diag_only) for z, mx, diag_only in zones)


def extract(page, clip, drop, section=False, drop_idx=(), drop_short=(), lift=False):
    shapes = []
    drawings = page.get_drawings()
    dashes = dash_runs(drawings)
    texts = text_boxes(page)
    skip = set(drop_idx)
    for i, d in enumerate(drawings):
        r = d["rect"]
        if i in skip or i in dashes or short_line_in(d, drop_short):
            continue
        if not rects_touch(r, clip) or any(bbox_in(r, b) for b in drop):
            continue
        # white masks laid behind annotation text
        if d["type"] == "f" and near(d.get("fill"), (1, 1, 1)) and any(r.intersects(t) for t in texts):
            continue
        style = classify(d, section, lift)
        if style is None:
            continue
        if style[0] == "fill":
            for poly in flatten(d["items"]):
                if len(poly) < 3:
                    continue
                for cr in clip:
                    p = clip_polygon(poly, cr)
                    if p:
                        shapes.append(("fill", style[1], p))
        else:
            for pl in flatten(d["items"]):
                for seg in clip_polyline(pl, clip):
                    shapes.append(("stroke", style[1], style[2], seg))
    return shapes


# ---------------------------------------------------------------- writers
def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def svg_doc(shapes, labels, clip, title, extra_svg="", board=None, north=True):
    x0 = min(c[0] for c in clip); y0 = min(c[1] for c in clip)
    x1 = max(c[2] for c in clip); y1 = max(c[3] for c in clip)
    pad = 28
    w, h = x1 - x0 + pad * 2, y1 - y0 + pad * 2 + 30
    if board:  # common artboard so every level shares one scale on screen
        w, h = board
    ox, oy = (w - (x1 - x0)) / 2 - x0, pad - y0
    tx = lambda p: f"{fmt(p[0] + ox)} {fmt(p[1] + oy)}"
    # group strokes by (colour, width) into single paths to keep files small
    groups, fills = {}, {}
    for s in shapes:
        if s[0] == "fill":
            fills.setdefault(s[1], []).append("M" + "L".join(tx(p) for p in s[2]) + "Z")
        else:
            groups.setdefault((s[1], round(s[2], 2)), []).append("M" + "L".join(tx(p) for p in s[3]))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(w)} {fmt(h)}" '
             f'role="img" aria-label="{title}" class="plan-svg">']
    parts.append(f'<rect width="100%" height="100%" fill="{BG}"/>')
    # paint order: floor pattern, then fills, then linework (mirrors the drawings' layering closely)
    for (c, sw), ds in sorted(groups.items(), key=lambda kv: kv[0][0] != PATTERN):
        if c != PATTERN:
            continue
        parts.append(f'<path fill="none" stroke="{c}" stroke-width="{sw}" d="{"".join(ds)}"/>')
    for c, ds in fills.items():
        if c != INK:
            parts.append(f'<path fill="{c}" d="{"".join(ds)}"/>')
    for (c, sw), ds in groups.items():
        if c == PATTERN:
            continue
        parts.append(f'<path fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" '
                     f'stroke-linejoin="round" d="{"".join(ds)}"/>')
    for c, ds in fills.items():
        if c == INK:
            parts.append(f'<path fill="{c}" d="{"".join(ds)}"/>')
    for text, x, y in labels:
        X, Y = x + ox, y + oy
        tw = len(text) * 4.6 + 7
        parts.append(f'<rect x="{fmt(X - tw / 2)}" y="{fmt(Y - 5.6)}" width="{fmt(tw)}" height="11.2" fill="{BG}" opacity=".9"/>'
                     f'<text x="{fmt(X)}" y="{fmt(Y + 2.4)}" text-anchor="middle" class="plan-label" '
                     f'font-family="Jost, Arial, sans-serif" font-size="6.6" letter-spacing="1.1" fill="{INK}">'
                     f'{text.upper()}</text>')
    parts.append(extra_svg.format(ox=ox, oy=oy, w=w, h=h))
    # scale bar (0–5 m) and north point, bottom-left
    sb = 5 / PT_TO_M
    bx, by = pad, h - 22
    parts.append(f'<g class="plan-scale" fill="{INK}" font-family="Jost, Arial, sans-serif" font-size="4.6" letter-spacing=".5">')
    for i in range(5):
        seg = sb / 5
        parts.append(f'<rect x="{fmt(bx + i * seg)}" y="{fmt(by)}" width="{fmt(seg)}" height="2.2" '
                     f'fill="{INK if i % 2 == 0 else BG}" stroke="{INK}" stroke-width=".35"/>')
    parts.append(f'<text x="{fmt(bx)}" y="{fmt(by + 9)}">0</text><text x="{fmt(bx + sb)}" y="{fmt(by + 9)}" text-anchor="middle">5 m</text></g>')
    nx, ny = w - pad - 10, h - 22
    a = math.radians(NORTH_DEG)
    if not north:
        parts.append("</svg>")
        return "\n".join(parts), (w, h, ox, oy)
    ex, ey = nx + 9 * math.cos(a), ny + 9 * math.sin(a)
    parts.append(f'<g class="plan-north" stroke="{INK}" stroke-width=".5" fill="none">'
                 f'<circle cx="{fmt(nx)}" cy="{fmt(ny)}" r="7"/>'
                 f'<line x1="{fmt(2 * nx - ex)}" y1="{fmt(2 * ny - ey)}" x2="{fmt(ex)}" y2="{fmt(ey)}"/>'
                 f'<path d="M{fmt(ex)} {fmt(ey)} l{fmt(-3.2 * math.cos(a - .45))} {fmt(-3.2 * math.sin(a - .45))} '
                 f'M{fmt(ex)} {fmt(ey)} l{fmt(-3.2 * math.cos(a + .45))} {fmt(-3.2 * math.sin(a + .45))}"/>'
                 f'<text x="{fmt(ex + 3)}" y="{fmt(ey + 2)}" stroke="none" fill="{INK}" '
                 f'font-family="Jost, Arial, sans-serif" font-size="5.4">N</text></g>')
    parts.append("</svg>")
    return "\n".join(parts), (w, h, ox, oy)


def pdf_page(doc, shapes, labels, clip, title, subtitle, notes, section_levels=None):
    """Draw one level onto a new A4 portrait page with a title block."""
    page = doc.new_page(width=595, height=842)
    page.draw_rect(page.rect, color=None, fill=pymupdf.utils.getColor("white"))
    x0 = min(c[0] for c in clip); y0 = min(c[1] for c in clip)
    x1 = max(c[2] for c in clip); y1 = max(c[3] for c in clip)
    # fit drawing into the page area while keeping the same scale for every level
    area = pymupdf.Rect(48, 150, 547, 740)
    s = min(area.width / (x1 - x0), area.height / (y1 - y0), SCALE_PDF)
    ox = area.x0 + (area.width - (x1 - x0) * s) / 2 - x0 * s
    oy = area.y0 - y0 * s
    T = lambda p: pymupdf.Point(p[0] * s + ox, p[1] * s + oy)
    hexrgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    sh = page.new_shape()
    order = ([x for x in shapes if x[0] == "stroke" and x[1] == PATTERN]
             + [x for x in shapes if x[0] == "fill" and x[1] != INK]
             + [x for x in shapes if x[0] == "stroke" and x[1] != PATTERN]
             + [x for x in shapes if x[0] == "fill" and x[1] == INK])
    for x in order:
        if x[0] == "fill":
            sh.draw_polyline([T(p) for p in x[2]] + [T(x[2][0])])
            sh.finish(color=None, fill=hexrgb(x[1]), closePath=True)
        else:
            sh.draw_polyline([T(p) for p in x[3]])
            sh.finish(color=hexrgb(x[1]), width=x[2] * s, closePath=False, lineCap=1, lineJoin=1)
    sh.commit()
    for text, x, y in labels:
        p = T((x, y)); t = text.upper(); fs = 6.4
        tw = pymupdf.get_text_length(t, fontname="helv", fontsize=fs) * 1.0
        page.draw_rect(pymupdf.Rect(p.x - tw / 2 - 3, p.y - 5, p.x + tw / 2 + 3, p.y + 4.5), color=None,
                       fill=hexrgb(BG), fill_opacity=.9)
        page.insert_text(pymupdf.Point(p.x - tw / 2, p.y + 2.2), t, fontname="helv", fontsize=fs, color=hexrgb(INK))
    if section_levels:
        sx0 = min(c[0] for c in SECTION["clip"]); sx1 = max(c[2] for c in SECTION["clip"])
        for name, rl, y in section_levels:
            a, b = T((sx0, y)), T((sx1 + 2, y))
            page.draw_line(a, b, color=hexrgb(SOFT), width=.35, dashes="[3 2] 0")
            page.insert_text(pymupdf.Point(b.x + 4, b.y - 1.5), name.upper(), fontname="helv", fontsize=5.4,
                             color=hexrgb(INK))
            page.insert_text(pymupdf.Point(b.x + 4, b.y + 5.5), f"RL {rl}", fontname="helv", fontsize=5,
                             color=hexrgb(MUTED))
        for t, x, y, rot in SECTION["dims"]:
            p = T((x, y)); tw = pymupdf.get_text_length(t, fontname="helv", fontsize=4.8)
            if rot:
                page.insert_text(pymupdf.Point(p.x + 1.7, p.y + tw / 2), t, fontname="helv", fontsize=4.8,
                                 color=hexrgb(INK), rotate=90)
            else:
                page.insert_text(pymupdf.Point(p.x - tw / 2, p.y + 1.7), t, fontname="helv", fontsize=4.8,
                                 color=hexrgb(INK))
    # title block
    page.insert_font(fontname="geo", fontfile=r"C:\Windows\Fonts\georgia.ttf")
    page.insert_text((48, 74), "THE TERRIGAL RESIDENCE", fontname="helv", fontsize=7.5, color=hexrgb(BRONZE))
    page.insert_text((48, 108), title, fontname="geo", fontsize=26, color=hexrgb(INK))
    page.insert_text((48, 128), subtitle, fontname="helv", fontsize=8, color=hexrgb(MUTED))
    page.draw_line((48, 140), (547, 140), color=hexrgb("#D9CFBF"), width=.5)
    # scale bar at the drawing scale
    sb = 5 / PT_TO_M * s
    for i in range(5):
        page.draw_rect(pymupdf.Rect(48 + i * sb / 5, 760, 48 + (i + 1) * sb / 5, 763), color=hexrgb(INK),
                       fill=hexrgb(INK) if i % 2 == 0 else (1, 1, 1), width=.4)
    page.insert_text((48, 773), "0", fontname="helv", fontsize=6.5, color=hexrgb(INK))
    page.insert_text((48 + sb - 6, 773), "5 m", fontname="helv", fontsize=6.5, color=hexrgb(INK))
    if not section_levels:  # north point on plans only, not on the section
        a = math.radians(NORTH_DEG); cx, cy = 530, 762
        page.draw_circle((cx, cy), 9, color=hexrgb(INK), width=.5)
        ex, ey = cx + 12 * math.cos(a), cy + 12 * math.sin(a)
        page.draw_line((2 * cx - ex, 2 * cy - ey), (ex, ey), color=hexrgb(INK), width=.6)
        page.insert_text((ex - 2, ey - 4), "N", fontname="helv", fontsize=7, color=hexrgb(INK))
    y = 792
    for n in notes:
        page.insert_text((48, y), n, fontname="helv", fontsize=6.2, color=hexrgb(MUTED)); y += 9
    return page


NOTES = [
    "Marketing plan prepared from the May 2026 CDC application drawings (O&Co Building Design, project 47/26).",
    "Indicative only and not to scale for construction. Not verified as-built; layouts and areas subject to confirmation.",
]
SCALE_PDF = 1.15  # PDF points per drawing point: identical for every level page


def main(src, pdf_dir=None):
    os.makedirs(OUT, exist_ok=True)
    if pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)
    full = pymupdf.open()
    span = lambda c, i, j: max(r[j] for r in c) - min(r[i] for r in c)
    board = (max(span(lv["clip"], 0, 2) for lv in LEVELS) + 56,
             max(span(lv["clip"], 1, 3) for lv in LEVELS) + 86)
    for lv in LEVELS:
        page = pymupdf.open(os.path.join(src, lv["pdf"]))[0]
        shapes = extract(page, lv["clip"], lv["drop"], drop_idx=lv["drop_idx"],
                         drop_short=lv.get("drop_short", ()), lift=lv.get("lift", False))
        labels = lv["labels"]
        if lv.get("lift_rect"):
            x0, y0, x1, y1 = lv["lift_rect"]
            shapes.append(("fill", LIFT, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
        svg, _ = svg_doc(shapes, labels, lv["clip"], f'{lv["name"]} plan', board=board)
        with open(os.path.join(OUT, f'plan-{lv["id"]}.svg'), "w", encoding="utf-8") as fh:
            fh.write(svg)
        if pdf_dir:
            for d in (pymupdf.open(), full):
                pdf_page(d, shapes, labels, lv["clip"], f'{lv["name"]} plan', f'Floor level RL {lv["rl"]}', NOTES)
                if d is not full:
                    d.save(os.path.join(pdf_dir, f'plan-{lv["id"]}.pdf'), garbage=4, deflate=True)
        print(f'{lv["id"]:13} {len(shapes):6} shapes  svg {len(svg) // 1024} KB')

    # section
    sp = pymupdf.open(os.path.join(src, SECTION["pdf"]))[0]
    shapes = extract(sp, SECTION["clip"], SECTION["drop"], section=True)
    x0 = min(c[0] for c in SECTION["clip"]); x1 = max(c[2] for c in SECTION["clip"])
    g = [f'<g transform="translate({{ox}} {{oy}})" font-family="Jost, Arial, sans-serif" fill="{MUTED}">']
    for n, rl, y in SECTION["levels"]:
        g.append(f'<line x1="{fmt(x0)}" x2="{fmt(x1 + 2)}" y1="{fmt(y)}" y2="{fmt(y)}" stroke="{SOFT}" '
                 f'stroke-width=".35" stroke-dasharray="3 2"/>'
                 f'<text x="{fmt(x1 + 5)}" y="{fmt(y - 1.6)}" font-size="5" letter-spacing=".6" fill="{INK}">{n.upper()}</text>'
                 f'<text x="{fmt(x1 + 5)}" y="{fmt(y + 5.4)}" font-size="4.6" letter-spacing=".4">RL {rl}</text>')
    for t, x, y, rot in SECTION["dims"]:
        tr = f' transform="rotate(-90 {fmt(x)} {fmt(y)})"' if rot else ""
        g.append(f'<text x="{fmt(x)}" y="{fmt(y + 1.6)}" text-anchor="middle" font-size="4.6" fill="{INK}"{tr}>{t}</text>')
    g.append("</g>")
    extra = "".join(g).replace("{", "{{").replace("}", "}}").replace("{{ox}}", "{ox}").replace("{{oy}}", "{oy}")
    clip_wide = [(478, 90, x1 + 70, 482)]
    svg, _ = svg_doc(shapes, [], clip_wide, "Architectural section", extra, north=False)
    with open(os.path.join(OUT, "plan-section.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)
    if pdf_dir:
        for d in (pymupdf.open(), full):
            pdf_page(d, shapes, [], clip_wide, "Architectural section", "Vertical arrangement of the levels (RL in metres)",
                     NOTES, SECTION["levels"])
            if d is not full:
                d.save(os.path.join(pdf_dir, "plan-section.pdf"), garbage=4, deflate=True)
        full.save(os.path.join(pdf_dir, "the-terrigal-residence-floor-plans.pdf"), garbage=4, deflate=True)
    print(f'section       {len(shapes):6} shapes  svg {len(svg) // 1024} KB')
    print("done")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
