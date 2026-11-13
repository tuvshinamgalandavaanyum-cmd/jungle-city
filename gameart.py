"""Казино, Dately-ийн pixel art зургууд (кодоор зурсан, фонт шаардахгүй)."""
import io
import math
import random

import discord

from pix import Canvas, card, chips, hexc, sparkle, shade

GOLD = (250, 204, 21)
WHITE = (250, 250, 250)
_cache: dict[str, bytes] = {}


def _felt(cv, a=(14, 78, 52), b=(6, 40, 28)):
    cv.gradient(a, b, bands=8)
    r = random.Random(3)
    for _ in range(90):
        cv.px(r.randrange(cv.w), r.randrange(cv.h), shade(a, 0.82))


def _title(cv, s, y=3, scale=2, col=GOLD):
    cv.ctext(cv.w // 2, y, s, col, scale, shadow=(20, 14, 6))


# ---------------- roulette ----------------
def roulette():
    cv = Canvas()
    _felt(cv)
    cx, cy, R = 48, 46, 30
    cv.ell(cx - R - 3, cy - R - 3, 2 * R + 7, 2 * R + 7, (74, 44, 22), (30, 18, 8))
    for y in range(cy - R, cy + R + 1):
        for x in range(cx - R, cx + R + 1):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            if r > R:
                continue
            ang = (math.atan2(dx, -dy)) % (2 * math.pi)
            idx = int(ang / (2 * math.pi) * 37)
            if r > 24:
                col = (96, 60, 30)
            elif r > 17:
                col = (30, 140, 70) if idx == 0 else ((200, 30, 40) if idx % 2 else (28, 28, 34))
                if abs(ang / (2 * math.pi) * 37 - round(ang / (2 * math.pi) * 37)) < 0.11 and r > 18:
                    col = (230, 200, 90)
            elif r > 13:
                col = (214, 168, 56)
            elif r > 5:
                col = (96, 60, 30) if (x + y) % 2 else (110, 70, 34)
            else:
                col = (230, 200, 90)
            cv.px(x, y, col)
    cv.rect(cx - 1, cy - 8, 3, 16, (240, 214, 120))
    cv.rect(cx - 8, cy - 1, 16, 3, (240, 214, 120))
    cv.ell(cx - 2, cy - 2, 5, 5, (255, 240, 170))
    cv.ell(cx + 10, cy - 20, 3, 3, WHITE)  # бөмбөлөг
    # ширээний тор
    gx, gy = 94, 14
    nums = [3, 6, 9, 12, 2, 5, 8, 11, 1, 4, 7, 10]
    for i, n in enumerate(nums):
        x, y = gx + (i % 4) * 15, gy + (i // 4) * 11
        red = n in (1, 3, 5, 7, 9, 12)
        cv.box(x, y, 14, 10, (190, 28, 38) if red else (26, 26, 32), (230, 200, 90))
        cv.ctext(x + 7, y + 2, str(n), WHITE)
    chips(cv, 104, 74, (200, 30, 40), 3)
    chips(cv, 120, 76, (40, 90, 200), 4)
    chips(cv, 136, 74, (30, 30, 36), 3)
    chips(cv, 150, 77, GOLD, 2)
    _title(cv, "ROULETTE", 2, 1, GOLD)
    return cv.png()


# ---------------- blackjack ----------------
def blackjack():
    cv = Canvas()
    _felt(cv)
    _title(cv, "BLACKJACK", 3, 2)
    card(cv, 44, 24, "K", "heart", True, 28, 40)
    card(cv, 62, 20, "A", "spade", False, 28, 40)
    cv.text(104, 26, "21", GOLD, 5, shadow=(20, 14, 6))
    cv.ctext(122, 56, "x2.5", WHITE, 1)
    chips(cv, 20, 74, (200, 30, 40), 4)
    chips(cv, 34, 76, (30, 30, 36), 3)
    chips(cv, 140, 76, (40, 90, 200), 3)
    chips(cv, 152, 74, GOLD, 4)
    return cv.png()


# ---------------- crash ----------------
def rocket(cv, x, y, flame=True):
    cv.poly([(x, y - 9), (x + 4, y - 3), (x + 4, y + 6), (x - 4, y + 6), (x - 4, y - 3)], (236, 240, 248))
    cv.poly([(x, y - 9), (x + 3, y - 4), (x - 3, y - 4)], (220, 38, 38))
    cv.ell(x - 1, y - 2, 3, 3, (60, 150, 230), (30, 70, 120))
    cv.poly([(x - 4, y + 2), (x - 8, y + 8), (x - 4, y + 6)], (200, 40, 40))
    cv.poly([(x + 4, y + 2), (x + 8, y + 8), (x + 4, y + 6)], (200, 40, 40))
    if flame:
        cv.poly([(x - 3, y + 7), (x + 3, y + 7), (x, y + 15)], (250, 150, 30))
        cv.poly([(x - 1, y + 7), (x + 1, y + 7), (x, y + 12)], (255, 230, 120))


def crash():
    cv = Canvas()
    cv.gradient((10, 12, 38), (24, 14, 56), bands=8)
    cv.stars(50, 5, 60)
    for x in range(8, 150, 16):
        cv.line([(x, 14), (x, 74)], (36, 40, 80))
    for y in range(18, 76, 14):
        cv.line([(8, y), (150, y)], (36, 40, 80))
    pts = []
    for i in range(0, 106):
        t = i / 105
        pts.append((10 + i, 72 - (math.exp(2.3 * t) - 1) / (math.exp(2.3) - 1) * 56))
    for (x, y) in pts[::2]:
        cv.line([(x, y), (x, 74)], (18, 70, 54))
    for i in range(len(pts) - 1):
        t = i / len(pts)
        col = (int(60 + 190 * t), int(220 - 40 * t), int(110 - 70 * t))
        cv.line([pts[i], pts[i + 1]], col, 2)
    rocket(cv, int(pts[-1][0]) + 2, int(pts[-1][1]) - 2)
    cv.text(104, 24, "x2.5", GOLD, 2, shadow=(40, 20, 4))
    _title(cv, "CRASH", 3, 2, (255, 120, 90))
    return cv.png()


# ---------------- horse race ----------------
def horse(cv, x, y, coat, jockey, step=0):
    dark = shade(coat, 0.6)
    cv.ell(x, y, 17, 8, coat)
    cv.poly([(x + 13, y + 3), (x + 18, y - 5), (x + 22, y - 4), (x + 19, y + 3)], coat)
    cv.poly([(x + 18, y - 5), (x + 24, y - 4), (x + 25, y - 1), (x + 20, y - 1)], coat)
    cv.px(x + 22, y - 3, (10, 10, 10))
    cv.line([(x + 17, y - 5), (x + 14, y + 1)], dark, 2)  # зулай
    cv.poly([(x + 1, y + 2), (x - 5, y + 6 + step), (x - 3, y + 8 + step), (x + 2, y + 5)], dark)  # сүүл
    for lx, ph in ((x + 2, 0), (x + 5, 1), (x + 11, 1), (x + 14, 0)):
        off = step if ph else -step
        cv.line([(lx, y + 6), (lx + off, y + 13)], dark, 1)
        cv.rect(lx + off, y + 13, 2, 1, (30, 20, 10))
    cv.rect(x + 7, y - 6, 4, 6, jockey)
    cv.ell(x + 7, y - 10, 4, 4, (240, 200, 160))
    cv.rect(x + 7, y - 11, 4, 2, shade(jockey, 0.8))


def horse_race():
    cv = Canvas()
    cv.gradient((110, 190, 245), (190, 228, 250), bands=6, y1=24)
    cv.rect(0, 24, 160, 56, (60, 150, 70))
    cv.rect(0, 30, 160, 44, (176, 128, 74))
    for i, y in enumerate((38, 52, 66)):
        cv.rect(0, y + 8, 160, 1, (150, 104, 58))
    for x in range(0, 160, 8):
        cv.rect(x, 26, 2, 6, WHITE)
    cv.rect(0, 27, 160, 1, WHITE)
    for x in range(8, 150, 5):
        cv.px(x, 21 + (x * 7) % 4, [(220, 60, 60), (60, 90, 220), (240, 210, 60)][x % 3])
    for i in range(8):  # финиш
        for j in range(12):
            cv.rect(142 + (i % 2) * 3, 32 + j * 4 + (i % 2) * 0, 3, 4, (250, 250, 250) if (i + j) % 2 == 0 else (20, 20, 20)) if i < 2 else None
    horse(cv, 78, 34, (120, 70, 36), (220, 40, 50), 1)
    horse(cv, 56, 48, (240, 240, 235), (50, 100, 230), -1)
    horse(cv, 36, 62, (40, 32, 30), (250, 210, 50), 1)
    cv.ctext(60, 6, "HORSE RACE", WHITE, 2, shadow=(20, 60, 100))
    return cv.png()


# ---------------- coinflip ----------------
def coinflip():
    cv = Canvas()
    cv.gradient((40, 22, 80), (18, 10, 44), bands=8)
    cv.stars(40, 9)
    cx, cy = 80, 42
    cv.ell(cx - 20, cy + 22, 40, 8, (10, 6, 24))
    cv.ell(cx - 22, cy - 22, 45, 45, (170, 112, 20), (90, 56, 8))
    cv.ell(cx - 20, cy - 21, 41, 42, (240, 190, 50), (200, 140, 30))
    cv.ell(cx - 15, cy - 16, 31, 31, (252, 214, 90), (200, 150, 40))
    cv.rect(cx - 8, cy - 8, 17, 4, (180, 120, 20))  # T
    cv.rect(cx - 2, cy - 8, 5, 18, (180, 120, 20))
    cv.px(cx - 14, cy - 12, WHITE); cv.px(cx - 13, cy - 13, WHITE); cv.px(cx - 12, cy - 14, WHITE)
    for sx, sy in ((30, 18), (128, 26), (44, 60), (118, 58)):
        sparkle(cv, sx, sy, GOLD)
    for k in range(3):
        cv.line([(cx - 34 - k * 4, cy - 8 + k * 6), (cx - 26 - k * 4, cy - 8 + k * 6)], (140, 110, 200))
        cv.line([(cx + 28 + k * 4, cy - 8 + k * 6), (cx + 36 + k * 4, cy - 8 + k * 6)], (140, 110, 200))
    _title(cv, "COIN FLIP", 3, 2)
    return cv.png()


# ---------------- dice ----------------
def die(cv, x, y, n, size=26):
    cv.ell(x + 2, y + size - 2, size - 2, 5, (30, 6, 8))
    cv.box(x, y, size, size, (248, 246, 240), (80, 80, 90))
    cv.rect(x + 1, y + 1, size - 2, 2, (255, 255, 255))
    cv.rect(x + 1, y + size - 3, size - 2, 2, (210, 208, 200))
    p = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (2, 0), (0, 2), (2, 2)],
         5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)], 6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}[n]
    step = size // 4
    for gx, gy in p:
        cv.ell(x + step - 1 + gx * step, y + step - 1 + gy * step, 4, 4, (190, 30, 40) if n == 1 else (30, 30, 38))


def dice():
    cv = Canvas()
    cv.gradient((90, 14, 28), (40, 6, 16), bands=8)
    cv.stars(25, 4, 50, (255, 170, 150))
    die(cv, 34, 28, 5)
    die(cv, 84, 36, 3, 26)
    sparkle(cv, 122, 24, GOLD); sparkle(cv, 24, 22, GOLD); sparkle(cv, 140, 62, GOLD)
    _title(cv, "DICE", 3, 2)
    return cv.png()


# ---------------- slots ----------------
def _cherry(cv, x, y):
    cv.line([(x + 6, y), (x + 3, y + 7)], (40, 120, 40), 1)
    cv.line([(x + 6, y), (x + 9, y + 7)], (40, 120, 40), 1)
    cv.ell(x, y + 6, 6, 6, (210, 30, 50), (120, 10, 20))
    cv.ell(x + 7, y + 6, 6, 6, (210, 30, 50), (120, 10, 20))
    cv.px(x + 2, y + 8, WHITE); cv.px(x + 9, y + 8, WHITE)


def slots():
    cv = Canvas()
    cv.gradient((30, 14, 60), (12, 6, 30), bands=8)
    cv.stars(30, 11)
    cv.box(36, 4, 88, 72, (190, 28, 44), (90, 8, 20))
    cv.rect(38, 6, 84, 3, (240, 90, 100))
    cv.box(44, 10, 72, 11, (30, 14, 40), GOLD)
    cv.ctext(80, 13, "SLOTS", GOLD, 1)
    for i in range(10):
        cv.ell(46 + i * 7, 22, 4, 4, GOLD if i % 2 else (255, 240, 140))
    cv.box(44, 28, 72, 34, (12, 10, 22), (230, 200, 90))
    for i in range(3):
        x = 47 + i * 23
        cv.box(x, 31, 20, 28, (250, 248, 240), (120, 110, 100))
        if i == 0:
            cv.ctext(x + 10, 36, "7", (210, 30, 40), 3, shadow=(100, 10, 20))
        elif i == 1:
            _cherry(cv, x + 3, 38)
        else:
            cv.box(x + 2, 38, 16, 12, (240, 190, 50), (150, 100, 10))
            cv.ctext(x + 10, 42, "BAR", (90, 50, 0))
    cv.rect(44, 64, 72, 8, (120, 16, 30))
    cv.ell(66, 66, 5, 5, GOLD); cv.ell(78, 66, 5, 5, GOLD); cv.ell(90, 66, 5, 5, GOLD)
    cv.rect(125, 26, 3, 24, (170, 170, 180))   # хөшүүрэг
    cv.ell(122, 18, 9, 9, (230, 40, 50), (120, 10, 20))
    for sx, sy in ((20, 20), (140, 60), (20, 60)):
        sparkle(cv, sx, sy, GOLD)
    return cv.png()


# ---------------- minefield ----------------
def minefield():
    cv = Canvas()
    cv.gradient((34, 36, 44), (16, 18, 24), bands=8)
    gx, gy = 28, 16
    layout = [
        "OOGOOO", "OGOBOO", "OOOGOO",
    ]
    for r, row in enumerate(layout):
        for c, k in enumerate(row):
            x, y = gx + c * 21, gy + r * 19
            if k == "O":
                cv.box(x, y, 19, 17, (110, 118, 132), (60, 64, 76))
                cv.rect(x + 1, y + 1, 17, 2, (160, 168, 182))
                cv.rect(x + 1, y + 14, 17, 2, (80, 86, 98))
            else:
                cv.box(x, y, 19, 17, (22, 24, 30), (60, 64, 76))
                if k == "G":
                    cv.poly([(x + 9, y + 3), (x + 15, y + 8), (x + 9, y + 14), (x + 3, y + 8)], (60, 220, 240))
                    cv.poly([(x + 9, y + 3), (x + 15, y + 8), (x + 9, y + 8)], (170, 250, 255))
                else:
                    cv.ell(x + 4, y + 5, 11, 11, (20, 20, 24), (90, 90, 100))
                    cv.px(x + 6, y + 7, WHITE)
                    cv.line([(x + 12, y + 6), (x + 15, y + 2)], (200, 170, 110))
                    sparkle(cv, x + 16, y + 2, (255, 190, 60))
    _title(cv, "MINEFIELD", 0, 1, (255, 150, 90))
    return cv.png()


# ---------------- duel / draw ----------------
def _cowboy(cv, x, y, face_right, hat, vest):
    d = 1 if face_right else -1
    cv.rect(x - 3, y + 16, 3, 10, (50, 40, 36)); cv.rect(x + 1, y + 16, 3, 10, (50, 40, 36))
    cv.rect(x - 3, y + 25, 4, 2, (30, 20, 16)); cv.rect(x + 1, y + 25, 4, 2, (30, 20, 16))
    cv.rect(x - 5, y + 6, 10, 11, vest)
    cv.rect(x - 1, y + 6, 2, 11, shade(vest, 0.7))
    cv.rect(x - 3, y, 6, 6, (232, 186, 144))
    cv.rect(x - 6, y - 1, 12, 2, hat); cv.rect(x - 3, y - 4, 6, 4, hat)
    ax = x + d * 5
    cv.rect(ax if d > 0 else ax - 8, y + 9, 8, 2, (232, 186, 144))
    gx = x + d * 12 if d > 0 else x - 16
    cv.rect(gx, y + 7, 5, 3, (40, 40, 48)); cv.rect(gx + (3 if d > 0 else 0), y + 9, 2, 3, (40, 40, 48))


def duel(title="DUEL", flash=False):
    cv = Canvas()
    cv.gradient((250, 120, 60), (120, 40, 110), bands=10, y1=48)
    cv.ell(60, 34, 40, 40, (255, 210, 110))
    cv.ell(66, 40, 28, 28, (255, 240, 170))
    cv.rect(0, 48, 160, 32, (150, 80, 50))
    cv.rect(0, 48, 160, 2, (190, 110, 70))
    for x, h in ((12, 20), (146, 24)):
        cv.rect(x, 48 - h + 12, 3, h, (40, 90, 50))
        cv.rect(x - 3, 48 - h + 18, 3, 7, (40, 90, 50)); cv.rect(x + 3, 48 - h + 15, 3, 7, (40, 90, 50))
    _cowboy(cv, 42, 34, True, (80, 50, 30), (180, 40, 40))
    _cowboy(cv, 118, 34, False, (40, 40, 56), (40, 90, 170))
    if flash:
        sparkle(cv, 60, 42, (255, 240, 120)); sparkle(cv, 100, 42, (255, 240, 120))
    for i in range(10):
        cv.px(6 + i * 16, 60 + (i * 5) % 12, (120, 60, 38))
    _title(cv, title, 3, 2, WHITE)
    return cv.png()


# ---------------- dately ----------------
def _heart(cv, x, y, c, s=1):
    cv.suit(x, y, "heart", c, s)


def dately():
    cv = Canvas()
    cv.gradient((255, 150, 190), (150, 70, 160), bands=10)
    r = random.Random(8)
    for _ in range(18):
        _heart(cv, r.randrange(4, 150), r.randrange(4, 70), (255, 220, 235), 1)
    cv.box(58, 6, 44, 70, (30, 24, 44), (14, 10, 22))
    cv.box(61, 10, 38, 62, (255, 232, 242))
    cv.rect(72, 7, 16, 2, (60, 54, 80))
    cv.ell(65, 16, 14, 14, (210, 150, 130), (120, 70, 60)); cv.rect(65, 12, 14, 7, (60, 36, 28))
    cv.ell(81, 16, 14, 14, (232, 190, 150), (120, 70, 60)); cv.rect(81, 12, 14, 6, (28, 24, 34))
    _heart(cv, 74, 34, (230, 40, 90), 2)
    cv.box(65, 52, 14, 9, (60, 190, 100), (20, 100, 50)); cv.ctext(72, 54, "OK", WHITE)
    cv.box(81, 52, 14, 9, (230, 70, 80), (130, 20, 30)); cv.ctext(88, 54, "NO", WHITE)
    cv.box(8, 22, 38, 12, (255, 255, 255), (150, 70, 160)); cv.ctext(21, 26, "OK", (200, 30, 90)); _heart(cv, 31, 25, (230, 40, 90), 1)
    cv.box(114, 40, 38, 12, (255, 255, 255), (150, 70, 160)); cv.ctext(133, 44, "NAHH", (120, 40, 160))
    _title(cv, "DATELY", 62, 2, WHITE) if False else None
    return cv.png()


KINDS = {
    "roulette": roulette, "blackjack": blackjack, "crash": crash, "horse": horse_race,
    "coinflip": coinflip, "dice": dice, "slots": slots, "minefield": minefield,
    "duel": duel, "draw": lambda: duel("QUICK DRAW", True), "dately": dately,
}


def art_bytes(kind: str) -> bytes:
    if kind not in _cache:
        _cache[kind] = KINDS[kind]()
    return _cache[kind]


def art_file(kind: str) -> discord.File:
    return discord.File(io.BytesIO(art_bytes(kind)), filename=f"{kind}.png")


def stamp(embed: discord.Embed, kind: str) -> discord.Embed:
    embed.set_image(url=f"attachment://{kind}.png")
    return embed
