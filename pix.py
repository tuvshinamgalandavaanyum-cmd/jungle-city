"""Pixel-art зурах жижиг сан: логик (жижиг) зургийг NEAREST-ээр томруулна.
Фонт шаардахгүй (3x5 pixel фонтыг кодод шууд бичсэн) тул сервер дээр хүрэлцэхгүй фонтоос болж эвдрэхгүй."""
import io
import math
import random

from PIL import Image, ImageDraw

W, H = 160, 80  # логик хэмжээ (SCALE=4 -> 640x320)
SCALE = 4

_G = {
    "A": ".#.|#.#|###|#.#|#.#", "B": "##.|#.#|##.|#.#|##.", "C": ".##|#..|#..|#..|.##",
    "D": "##.|#.#|#.#|#.#|##.", "E": "###|#..|##.|#..|###", "F": "###|#..|##.|#..|#..",
    "G": ".##|#..|#.#|#.#|.##", "H": "#.#|#.#|###|#.#|#.#", "I": "###|.#.|.#.|.#.|###",
    "J": "..#|..#|..#|#.#|.#.", "K": "#.#|#.#|##.|#.#|#.#", "L": "#..|#..|#..|#..|###",
    "M": "#.#|###|###|#.#|#.#", "N": "##.|#.#|#.#|#.#|#.#", "O": ".#.|#.#|#.#|#.#|.#.",
    "P": "##.|#.#|##.|#..|#..", "Q": ".#.|#.#|#.#|##.|.##", "R": "##.|#.#|##.|#.#|#.#",
    "S": ".##|#..|.#.|..#|##.", "T": "###|.#.|.#.|.#.|.#.", "U": "#.#|#.#|#.#|#.#|###",
    "V": "#.#|#.#|#.#|#.#|.#.", "W": "#.#|#.#|###|###|#.#", "X": "#.#|#.#|.#.|#.#|#.#",
    "Y": "#.#|#.#|.#.|.#.|.#.", "Z": "###|..#|.#.|#..|###",
    "0": "###|#.#|#.#|#.#|###", "1": ".#.|##.|.#.|.#.|###", "2": "###|..#|###|#..|###",
    "3": "###|..#|###|..#|###", "4": "#.#|#.#|###|..#|..#", "5": "###|#..|###|..#|###",
    "6": "###|#..|###|#.#|###", "7": "###|..#|..#|.#.|.#.", "8": "###|#.#|###|#.#|###",
    "9": "###|#.#|###|..#|###", ".": "...|...|...|...|.#.", "!": ".#.|.#.|.#.|...|.#.",
    "?": "###|..#|.##|...|.#.", "x": "...|#.#|.#.|#.#|...", "-": "...|...|###|...|...",
    " ": "...|...|...|...|...", "+": "...|.#.|###|.#.|...", ":": "...|.#.|...|.#.|...",
}
GLYPHS = {k: [row for row in v.split("|")] for k, v in _G.items()}

SUITS = {
    "heart": [".##.##.", "#######", "#######", ".#####.", "..###..", "...#...", "......."],
    "spade": ["...#...", "..###..", ".#####.", "#######", "#######", "...#...", "..###.."],
    "diamond": ["...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#..."],
    "club": ["..###..", "..###..", ".#.#.#.", "#######", "#######", "...#...", "..###.."],
}


class Canvas:
    def __init__(self, w=W, h=H, bg=(0, 0, 0)):
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w, h), bg)
        self.d = ImageDraw.Draw(self.im)

    # ---- primitives ----
    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((int(x), int(y)), c)

    def rect(self, x, y, w, h, c):
        self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)

    def box(self, x, y, w, h, fill, edge=None):
        self.rect(x, y, w, h, fill)
        if edge:
            self.d.rectangle([x, y, x + w - 1, y + h - 1], outline=edge)

    def ell(self, x, y, w, h, c, edge=None):
        self.d.ellipse([x, y, x + w - 1, y + h - 1], fill=c, outline=edge)

    def poly(self, pts, c):
        self.d.polygon(pts, fill=c)

    def line(self, pts, c, width=1):
        self.d.line(pts, fill=c, width=width)

    def gradient(self, top, bot, bands=10, y0=0, y1=None):
        y1 = self.h if y1 is None else y1
        span = max(1, y1 - y0)
        for i in range(bands):
            a, b = y0 + span * i // bands, y0 + span * (i + 1) // bands
            t = i / max(1, bands - 1)
            col = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            self.rect(0, a, self.w, max(1, b - a), col)

    def stars(self, n=40, seed=1, y1=None, col=(255, 255, 255)):
        r = random.Random(seed)
        y1 = self.h if y1 is None else y1
        for _ in range(n):
            c = col if r.random() > 0.3 else tuple(int(v * 0.55) for v in col)
            self.px(r.randrange(self.w), r.randrange(max(1, y1)), c)

    # ---- text ----
    def text_w(self, s, scale=1):
        return len(s) * 4 * scale - scale

    def text(self, x, y, s, c, scale=1, shadow=None):
        for i, ch in enumerate(s.upper() if s != "x" else s):
            g = GLYPHS.get(ch if ch in GLYPHS else ch.upper(), GLYPHS["?"])
            for ry, row in enumerate(g):
                for rx, v in enumerate(row):
                    if v == "#":
                        px = x + i * 4 * scale + rx * scale
                        py = y + ry * scale
                        if shadow:
                            self.rect(px + scale, py + scale, scale, scale, shadow)
                        self.rect(px, py, scale, scale, c)

    def ctext(self, cx, y, s, c, scale=1, shadow=None):
        self.text(cx - self.text_w(s, scale) // 2, y, s, c, scale, shadow)

    def suit(self, x, y, name, c, scale=1):
        for ry, row in enumerate(SUITS[name]):
            for rx, v in enumerate(row):
                if v == "#":
                    self.rect(x + rx * scale, y + ry * scale, scale, scale, c)

    # ---- output ----
    def png(self, scale=SCALE) -> bytes:
        big = self.im.resize((self.w * scale, self.h * scale), Image.NEAREST)
        buf = io.BytesIO()
        big.save(buf, "PNG", optimize=True)
        return buf.getvalue()


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def hexc(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def sparkle(cv, x, y, c=(255, 255, 255)):
    cv.px(x, y, c)
    cv.px(x - 1, y, shade(c, 0.7)); cv.px(x + 1, y, shade(c, 0.7))
    cv.px(x, y - 1, shade(c, 0.7)); cv.px(x, y + 1, shade(c, 0.7))


def chips(cv, x, y, color, n=4):
    """Хоолны (casino) chip-ийн багц; x,y = доод төв."""
    for i in range(n):
        yy = y - i * 3
        cv.ell(x - 6, yy - 3, 12, 6, shade(color, 0.7))
        cv.ell(x - 6, yy - 4, 12, 6, color, shade(color, 0.55))
        cv.rect(x - 1, yy - 2, 3, 1, (255, 255, 255))


def card(cv, x, y, rank, suit, red, w=24, h=34):
    cv.box(x, y, w, h, (250, 248, 240), (60, 60, 70))
    col = (200, 30, 40) if red else (30, 30, 40)
    cv.text(x + 2, y + 2, rank, col, 1)
    cv.suit(x + w // 2 - 3, y + h // 2 - 2, suit, col, 1)
    cv.text(x + w - 5, y + h - 8, rank, col, 1)
