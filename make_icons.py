"""
Generate .ico and favicon files for the PostgresDataMigration app.

Pillow-only. No ImageMagick, no Cairo, no svglib — Pillow is the single dependency
and is already installed. Just run:

    python make_icons.py

Produces, next to this script:
    PostgresDataMigration.ico   (16, 32, 48, 64, 128, 256)
    favicon.ico                 (16, 32, 48)
    favicon-32.png, favicon-16.png
    preview-512.png
"""
from pathlib import Path
import re
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SS = 4                      # supersample factor for smooth edges
BASE = 512
W = BASE * SS

# palette
BG_TOP = (59, 111, 168)     # #3B6FA8
BG_BOT = (42, 76, 119)      # #2A4C77
ELEPH = (234, 242, 251)     # #EAF2FB
EAR = (211, 226, 244)       # #D3E2F4
EYE = (42, 76, 119)         # #2A4C77
WHITE = (255, 255, 255)
GREEN = (76, 191, 125)      # mid of #5FD38A / #37A96B
CYL_BOT = (201, 218, 240)   # #C9DAF0


# ---- tiny SVG-path flattener (M/m L/l H/h V/v C/c Q/q Z/z) ----
def _bezier(p0, p1, p2, p3, n=28):
    pts = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0]
        y = mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def _quad(p0, p1, p2, n=28):
    pts = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        x = mt*mt*p0[0] + 2*mt*t*p1[0] + t*t*p2[0]
        y = mt*mt*p0[1] + 2*mt*t*p1[1] + t*t*p2[1]
        pts.append((x, y))
    return pts


def flatten(d):
    toks = re.findall(r"[MmLlHhVvCcQqZz]|-?\d*\.?\d+", d)
    i = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    out = []

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    cmd = None
    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t; i += 1
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            x = num(); y = num()
            if rel:
                x += cur[0]; y += cur[1]
            cur = (x, y); start = cur; out.append(cur)
            cmd = "l" if rel else "L"
        elif c == "L":
            x = num(); y = num()
            if rel:
                x += cur[0]; y += cur[1]
            cur = (x, y); out.append(cur)
        elif c == "H":
            x = num()
            if rel:
                x += cur[0]
            cur = (x, cur[1]); out.append(cur)
        elif c == "V":
            y = num()
            if rel:
                y += cur[1]
            cur = (cur[0], y); out.append(cur)
        elif c == "C":
            x1 = num(); y1 = num(); x2 = num(); y2 = num(); x = num(); y = num()
            if rel:
                x1 += cur[0]; y1 += cur[1]; x2 += cur[0]; y2 += cur[1]; x += cur[0]; y += cur[1]
            out += _bezier(cur, (x1, y1), (x2, y2), (x, y))
            cur = (x, y)
        elif c == "Q":
            x1 = num(); y1 = num(); x = num(); y = num()
            if rel:
                x1 += cur[0]; y1 += cur[1]; x += cur[0]; y += cur[1]
            out += _quad(cur, (x1, y1), (x, y))
            cur = (x, y)
        elif c == "Z":
            out.append(start); cur = start
    return out


def S(seq):
    return [(x * SS, y * SS) for x, y in seq]


BODY = "M150 300 c0 -50 40 -92 92 -92 c30 0 57 14 74 36 c8 -3 17 -3 25 0 c15 5 25 19 25 35 c0 12 -6 23 -15 30 c1 6 1 12 0 18 l0 40 c0 8 -6 14 -14 14 l-14 0 c-8 0 -14 -6 -14 -14 l0 -18 c-14 5 -29 8 -45 8 c-9 0 -18 -1 -27 -3 l0 27 c0 8 -6 14 -14 14 l-14 0 c-8 0 -14 -6 -14 -14 l0 -40 c-20 -16 -30 -40 -30 -66 z"
EAR_P = "M300 236 c22 0 40 18 40 40 c0 20 -14 36 -33 39 c8 -12 12 -26 12 -41 c0 -14 -7 -27 -19 -38 z"
TRUNK = "M232 244 c-20 2 -34 18 -34 40 c0 20 6 40 6 58 c0 10 8 18 18 18 c9 0 16 -7 16 -16 c0 -18 -6 -36 -6 -54 c0 -12 6 -22 16 -27 c-6 -10 -13 -17 -22 -19 z"
TUSK = "M236 300 c-6 8 -6 18 -2 27 c-8 -6 -12 -18 -8 -28 z"
ARROW = "M140 402 q130 60 236 -8"
HEAD = "M356 416 l34 -34 l2 50 z"


def build_base():
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))

    # vertical gradient
    grad = Image.new("RGBA", (1, W))
    for y in range(W):
        t = y / (W - 1)
        r = round(BG_TOP[0] + (BG_BOT[0]-BG_TOP[0])*t)
        g = round(BG_TOP[1] + (BG_BOT[1]-BG_TOP[1])*t)
        b = round(BG_TOP[2] + (BG_BOT[2]-BG_TOP[2])*t)
        grad.putpixel((0, y), (r, g, b, 255))
    grad = grad.resize((W, W))

    # rounded-rect mask for the tile
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [16*SS, 16*SS, 496*SS, 496*SS], radius=104*SS, fill=255)
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    d.polygon(S(flatten(BODY)), fill=ELEPH)
    d.polygon(S(flatten(EAR_P)), fill=EAR)
    d.polygon(S(flatten(TRUNK)), fill=ELEPH)
    d.polygon(S(flatten(TUSK)), fill=WHITE)

    # eye
    ex, ey, er = 286*SS, 252*SS, 8*SS
    d.ellipse([ex-er, ey-er, ex+er, ey+er], fill=EYE)

    # source data cylinder (translate 140,388)
    cx, cy = 140*SS, 388*SS
    rx, ry = 19*SS, 7*SS
    d.rectangle([cx-rx, cy, cx+rx, cy+20*SS], fill=ELEPH)
    d.ellipse([cx-rx, cy+20*SS-ry, cx+rx, cy+20*SS+ry], fill=CYL_BOT)
    d.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=ELEPH)
    d.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], outline=CYL_BOT, width=max(1, 2*SS))

    # migration arrow (thick round-capped stroke + triangular head)
    stroke = S(flatten(ARROW))
    d.line(stroke, fill=GREEN, width=24*SS, joint="curve")
    for px, py in (stroke[0], stroke[-1]):
        rr = 12*SS
        d.ellipse([px-rr, py-rr, px+rr, py+rr], fill=GREEN)
    d.polygon(S(flatten(HEAD)), fill=GREEN)

    return img


def main():
    base = build_base()
    sizes = [16, 32, 48, 64, 128, 256, 512]
    imgs = {s: base.resize((s, s), Image.LANCZOS) for s in sizes}

    imgs[256].save(HERE / "PostgresDataMigration.ico",
                   sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    imgs[48].save(HERE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    imgs[32].save(HERE / "favicon-32.png")
    imgs[16].save(HERE / "favicon-16.png")
    imgs[512].save(HERE / "preview-512.png")
    print("Wrote PostgresDataMigration.ico, favicon.ico, favicon-32.png, favicon-16.png, preview-512.png")


if __name__ == "__main__":
    main()
