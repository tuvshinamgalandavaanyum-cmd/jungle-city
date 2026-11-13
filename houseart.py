"""Байшингийн pixel art зургууд (28 байшин, кодоор зурсан)."""
import io
import math
import random

import discord

from pix import Canvas, shade, sparkle

GY = 62  # газрын түвшин
WHITE = (250, 250, 250)
_cache: dict[str, bytes] = {}


# ---------------- арын дэвсгэр ----------------
def sky(cv, kind="day"):
    if kind == "day":
        cv.gradient((100, 176, 244), (196, 230, 250), bands=8, y1=GY)
        cv.ell(128, 6, 14, 14, (255, 236, 130)); cv.ell(130, 8, 10, 10, (255, 248, 190))
        cloud(cv, 20, 10); cloud(cv, 70, 18); cloud(cv, 104, 8)
    elif kind == "sunset":
        cv.gradient((250, 130, 70), (120, 50, 120), bands=8, y1=GY)
        cv.ell(60, 40, 40, 40, (255, 210, 110))
    elif kind == "night":
        cv.gradient((10, 12, 40), (40, 30, 80), bands=8, y1=GY)
        cv.stars(50, 7, GY)
        cv.ell(130, 6, 12, 12, (240, 240, 210)); cv.ell(134, 5, 11, 11, (14, 16, 44))
    elif kind == "snow":
        cv.gradient((150, 190, 230), (225, 238, 250), bands=8, y1=GY)
    elif kind == "space":
        cv.gradient((4, 4, 20), (20, 10, 50), bands=8)
        cv.stars(90, 3)
    elif kind == "sea":
        cv.gradient((90, 190, 250), (200, 236, 252), bands=8, y1=40)
        cv.ell(128, 6, 14, 14, (255, 236, 130))


def cloud(cv, x, y):
    c = (255, 255, 255)
    cv.ell(x, y + 3, 12, 6, c); cv.ell(x + 5, y, 10, 8, c); cv.ell(x + 11, y + 3, 10, 6, c)


def ground(cv, col=(70, 160, 80), y=GY, dark=None):
    cv.rect(0, y, 160, 80 - y, col)
    cv.rect(0, y, 160, 2, shade(col, 1.25))
    r = random.Random(4)
    for _ in range(40):
        cv.px(r.randrange(160), r.randrange(y + 2, 80), shade(col, 0.8))


def sea(cv, y=44):
    cv.rect(0, y, 160, 80 - y, (36, 130, 210))
    for i in range(6):
        cv.rect(0, y + i * 6, 160, 3, (60, 160, 230) if i % 2 == 0 else (28, 110, 190))
    r = random.Random(2)
    for _ in range(24):
        x, yy = r.randrange(160), r.randrange(y + 2, 78)
        cv.rect(x, yy, 4, 1, (200, 236, 252))


def mountains(cv, y=GY, col=(120, 140, 170), snow=True):
    for cx, h in ((20, 30), (60, 38), (100, 28), (140, 34)):
        cv.poly([(cx - 30, y), (cx, y - h), (cx + 30, y)], col)
        if snow:
            cv.poly([(cx - 7, y - h + 9), (cx, y - h), (cx + 7, y - h + 9), (cx + 3, y - h + 7), (cx, y - h + 10), (cx - 3, y - h + 7)], WHITE)


# ---------------- жижиг эд зүйлс ----------------
def tree(cv, x, y, s=1, col=(40, 130, 60)):
    cv.rect(x - 1, y - 6 * s, 3, 7 * s, (110, 70, 36))
    cv.ell(x - 6 * s, y - 16 * s, 13 * s, 12 * s, col)
    cv.ell(x - 4 * s, y - 20 * s, 9 * s, 8 * s, shade(col, 1.2))


def pine(cv, x, y, s=1, col=(30, 100, 60), snow=False):
    cv.rect(x - 1, y - 3, 3, 4, (90, 60, 30))
    for i in range(3):
        w = (9 - i * 2) * s
        yy = y - 3 - i * 6 * s
        cv.poly([(x - w, yy), (x + w, yy), (x, yy - 9 * s)], col)
        if snow:
            cv.poly([(x - w // 2, yy - 4 * s), (x + w // 2, yy - 4 * s), (x, yy - 9 * s)], WHITE)


def palm(cv, x, y, h=22):
    cv.line([(x, y), (x + 2, y - h // 2), (x + 1, y - h)], (130, 90, 50), 2)
    top = (x + 1, y - h)
    for dx, dy in ((-9, 2), (-6, -3), (0, -5), (7, -3), (10, 2), (-4, 5), (6, 5)):
        cv.line([top, (top[0] + dx, top[1] + dy)], (40, 150, 70), 2)
    cv.ell(x - 1, y - h + 1, 3, 3, (110, 70, 30))


def window(cv, x, y, w=6, h=7, lit=False, frame=(60, 50, 50)):
    cv.box(x, y, w, h, (255, 224, 120) if lit else (150, 200, 240), frame)
    cv.rect(x + w // 2, y, 1, h, frame)
    if not lit:
        cv.px(x + 1, y + 1, WHITE)


def door(cv, x, y, w=6, h=11, col=(120, 70, 40)):
    cv.box(x, y, w, h, col, shade(col, 0.6))
    cv.px(x + w - 2, y + h // 2, (250, 210, 80))


def fence(cv, x0, x1, y, col=(240, 236, 226)):
    for x in range(x0, x1, 4):
        cv.rect(x, y - 5, 2, 6, col)
    cv.rect(x0, y - 4, x1 - x0, 1, col); cv.rect(x0, y - 1, x1 - x0, 1, col)


def smoke(cv, x, y):
    for i in range(4):
        cv.ell(x + (i % 2) * 2, y - i * 4, 4 + i, 3 + i, (230, 230, 235))


def house(cv, x, base, w, h, wall, roof, roof_kind="gable", rows=1, cols=2, lit=False, rh=None, door_on=True, chimney=False):
    top = base - h
    cv.box(x, top, w, h, wall, shade(wall, 0.65))
    cv.rect(x + 1, top + 1, w - 2, 1, shade(wall, 1.2))
    rh = rh or max(6, w // 3)
    if roof_kind == "gable":
        cv.poly([(x - 3, top), (x + w + 2, top), (x + w // 2, top - rh)], roof)
        cv.line([(x - 3, top), (x + w // 2, top - rh), (x + w + 2, top)], shade(roof, 0.65))
    elif roof_kind == "flat":
        cv.box(x - 2, top - 3, w + 4, 3, roof, shade(roof, 0.6))
    elif roof_kind == "hip":
        cv.poly([(x - 3, top), (x + w + 2, top), (x + w - 5, top - rh), (x + 5, top - rh)], roof)
    elif roof_kind == "cone":
        cv.poly([(x - 3, top), (x + w + 2, top), (x + w // 2, top - rh - 2)], roof)
    if chimney:
        cv.rect(x + w - 8, top - rh + 2, 4, rh - 1, (140, 80, 60)); smoke(cv, x + w - 7, top - rh)
    ww = 6
    gap = (w - cols * ww) // (cols + 1)
    for r in range(rows):
        for c in range(cols):
            wx = x + gap + c * (ww + gap)
            wy = top + 4 + r * 11
            if door_on and r == rows - 1 and cols % 2 == 1 and c == cols // 2:
                continue
            window(cv, wx, wy, ww, 7, lit)
    if door_on:
        door(cv, x + w // 2 - 3, base - 11)


# ---------------- байшингууд ----------------
def tent():
    cv = Canvas(); sky(cv); mountains(cv, GY, (110, 150, 120), False); ground(cv, (88, 150, 70))
    cv.poly([(50, GY), (80, 30), (110, GY)], (236, 130, 40))
    cv.poly([(80, 30), (110, GY), (88, GY)], (200, 100, 28))
    cv.poly([(72, GY), (80, 42), (88, GY)], (60, 30, 20))
    cv.line([(80, 30), (80, 24)], (130, 90, 50), 1); cv.poly([(80, 24), (88, 26), (80, 28)], (230, 50, 60))
    cv.ell(124, GY - 6, 12, 5, (60, 50, 50)); cv.poly([(126, GY - 3), (130, GY - 14), (134, GY - 3)], (250, 150, 30))
    cv.poly([(128, GY - 3), (130, GY - 9), (132, GY - 3)], (255, 230, 100))
    pine(cv, 22, GY, 1); pine(cv, 142, GY, 1)
    return cv


def container():
    cv = Canvas(); sky(cv, "day"); ground(cv, (150, 150, 140))
    cv.box(34, 30, 92, 32, (190, 80, 50), (100, 36, 20))
    for x in range(38, 124, 6):
        cv.rect(x, 31, 2, 30, (160, 62, 38))
    cv.box(38, 36, 22, 16, (150, 200, 235), (60, 50, 50)); cv.rect(48, 36, 1, 16, (60, 50, 50))
    cv.box(98, 36, 22, 24, (170, 70, 44), (80, 30, 18)); cv.rect(108, 36, 1, 24, (80, 30, 18))
    cv.rect(34, 62, 92, 2, (50, 50, 56))
    cv.box(130, 50, 14, 12, (60, 120, 170), (30, 60, 90)); cv.box(130, 40, 14, 10, (200, 160, 50), (110, 80, 20))
    return cv


def ger():
    cv = Canvas(); sky(cv); mountains(cv, GY, (110, 150, 120), False); ground(cv, (110, 170, 80))
    cv.box(48, 40, 64, 22, (246, 242, 230), (150, 140, 120))
    for x in range(52, 110, 8):
        cv.rect(x, 41, 1, 20, (210, 204, 190))
    cv.poly([(44, 40), (116, 40), (80, 18)], (240, 236, 224)); cv.line([(44, 40), (80, 18), (116, 40)], (150, 140, 120))
    for x in (56, 68, 80, 92, 104):
        cv.line([(80, 18), (x, 40)], (210, 204, 190))
    cv.ell(74, 15, 12, 5, (200, 40, 40), (110, 20, 20)); cv.rect(77, 14, 6, 2, (30, 30, 30))
    cv.box(74, 46, 12, 16, (230, 110, 40), (120, 50, 20)); cv.rect(79, 46, 2, 16, (160, 70, 24))
    cv.line([(50, 50), (110, 50)], (200, 40, 40), 2)
    cv.rect(100, 24, 2, 14, (140, 100, 60)); smoke(cv, 101, 22)
    # морь
    cv.ell(124, 52, 14, 7, (120, 70, 36)); cv.rect(135, 46, 4, 8, (120, 70, 36)); cv.rect(125, 58, 2, 5, (80, 46, 20)); cv.rect(135, 58, 2, 5, (80, 46, 20))
    return cv


def cabin():
    cv = Canvas(); sky(cv, "day"); mountains(cv, GY, (110, 130, 150)); ground(cv, (70, 140, 74))
    cv.box(44, 38, 62, 24, (150, 96, 52), (70, 40, 20))
    for y in range(40, 62, 4):
        cv.rect(45, y, 60, 1, (110, 70, 36))
    cv.poly([(38, 38), (112, 38), (75, 16)], (90, 54, 40)); cv.line([(38, 38), (75, 16), (112, 38)], (50, 28, 20))
    cv.rect(94, 20, 6, 14, (120, 70, 56)); smoke(cv, 97, 18)
    window(cv, 52, 44, 8, 8, True); window(cv, 88, 44, 8, 8, True); door(cv, 68, 50, 8, 12, (90, 54, 30))
    pine(cv, 22, GY, 1); pine(cv, 136, GY, 1); pine(cv, 148, GY, 1)
    return cv


def studio():
    cv = Canvas(); sky(cv); ground(cv, (150, 160, 160), GY)
    cv.box(40, 36, 80, 26, (240, 240, 244), (130, 130, 140))
    cv.box(34, 32, 92, 5, (60, 66, 80), (30, 30, 40))
    cv.box(46, 42, 40, 16, (130, 200, 240), (60, 80, 100))
    for x in (56, 66, 76):
        cv.rect(x, 42, 1, 16, (60, 80, 100))
    cv.px(48, 44, WHITE); cv.px(49, 44, WHITE)
    door(cv, 96, 46, 8, 16, (60, 66, 80)); window(cv, 108, 44, 8, 8, True)
    tree(cv, 20, GY, 1); tree(cv, 142, GY, 1, (60, 150, 80))
    return cv


def hut():
    cv = Canvas(); sky(cv); ground(cv)
    house(cv, 52, GY, 56, 24, (240, 220, 180), (190, 70, 50), "gable", 1, 2, chimney=True)
    fence(cv, 30, 126, GY + 6, (250, 240, 220)) if False else None
    tree(cv, 26, GY, 1); tree(cv, 136, GY, 1)
    for x, c in ((40, (240, 80, 120)), (46, (250, 210, 60)), (114, (240, 80, 120))):
        cv.px(x, GY - 1, c); cv.px(x, GY, (50, 120, 50))
    return cv


def loft():
    cv = Canvas(); sky(cv, "sunset")
    for x, h, c in ((6, 28, (70, 40, 90)), (26, 38, (60, 36, 80)), (118, 34, (66, 38, 86)), (140, 26, (76, 44, 96))):
        cv.rect(x, GY - h, 18, h, c)
    ground(cv, (90, 90, 100))
    cv.box(46, 22, 68, 40, (170, 70, 56), (80, 30, 24))
    for y in range(24, 62, 4):
        cv.rect(47, y, 66, 1, (140, 54, 44))
    for r in range(2):
        for c in range(3):
            x, y = 52 + c * 20, 28 + r * 16
            cv.box(x, y, 14, 12, (255, 220, 130), (50, 36, 30)); cv.rect(x + 7, y, 1, 12, (50, 36, 30)); cv.rect(x, y + 6, 14, 1, (50, 36, 30))
    door(cv, 72, 52, 14, 10, (50, 40, 44))
    cv.line([(112, 30), (122, 30), (122, 62)], (40, 40, 48))
    for y in (38, 48, 58):
        cv.rect(112, y, 10, 1, (40, 40, 48))
    return cv


def flat():
    cv = Canvas(); sky(cv); ground(cv, (140, 140, 140))
    cv.box(48, 14, 64, 48, (206, 190, 170), (110, 96, 84))
    cv.box(44, 10, 72, 5, (110, 100, 100), (60, 56, 56))
    for r in range(4):
        for c in range(4):
            window(cv, 53 + c * 14, 19 + r * 10, 6, 6, (r * 3 + c) % 3 == 0)
    door(cv, 74, 52, 12, 10, (80, 90, 120))
    tree(cv, 28, GY, 1); tree(cv, 132, GY, 1)
    return cv


def duplex():
    cv = Canvas(); sky(cv); ground(cv)
    house(cv, 30, GY, 50, 26, (240, 210, 170), (150, 60, 50), "gable", 1, 2, door_on=True)
    house(cv, 80, GY, 50, 26, (170, 200, 230), (60, 70, 120), "gable", 1, 2, door_on=True, chimney=True)
    cv.rect(79, GY - 26, 2, 26, (90, 80, 70))
    tree(cv, 14, GY, 1); tree(cv, 146, GY, 1)
    return cv


def bungalow():
    cv = Canvas(); sky(cv, "sea"); sea(cv, 46); cv.rect(0, 58, 160, 22, (238, 214, 160))
    cv.box(40, 44, 80, 18, (250, 244, 230), (150, 140, 120))
    cv.poly([(32, 44), (128, 44), (104, 28), (56, 28)], (200, 160, 80)); cv.line([(32, 44), (56, 28), (104, 28), (128, 44)], (140, 100, 40))
    for x in range(40, 124, 5):
        cv.line([(x, 44), (x - 2, 40)], (150, 110, 50))
    window(cv, 48, 48, 8, 8, True); window(cv, 96, 48, 8, 8, True); door(cv, 72, 50, 8, 12, (140, 90, 50))
    palm(cv, 20, 66, 26); palm(cv, 142, 66, 22)
    return cv


def yard():
    cv = Canvas(); sky(cv); ground(cv)
    house(cv, 44, GY, 62, 28, (236, 220, 196), (80, 100, 150), "gable", 1, 3, chimney=True, door_on=True)
    fence(cv, 8, 40, GY + 8); fence(cv, 110, 152, GY + 8)
    cv.box(122, 52, 12, 10, (190, 110, 60), (100, 50, 20)); cv.poly([(120, 52), (136, 52), (128, 45)], (150, 70, 50)); cv.ell(126, 56, 4, 5, (30, 20, 20))
    tree(cv, 20, GY, 1)
    return cv


def farmhouse():
    cv = Canvas(); sky(cv); ground(cv, (150, 180, 70))
    cv.box(34, 30, 56, 32, (190, 50, 44), (100, 20, 20)); cv.poly([(28, 30), (96, 30), (62, 12)], (90, 60, 50))
    cv.rect(52, 40, 20, 22, (240, 236, 226)); cv.line([(52, 40), (72, 62)], (110, 40, 40)); cv.line([(72, 40), (52, 62)], (110, 40, 40)); cv.d.rectangle([52, 40, 71, 61], outline=(110, 40, 40))
    cv.box(100, 22, 16, 40, (200, 200, 210), (110, 110, 120)); cv.ell(100, 14, 16, 14, (150, 150, 160)); cv.rect(106, 34, 4, 5, (90, 90, 100))
    cv.ell(122, 54, 22, 10, (230, 190, 70), (150, 110, 20))
    fence(cv, 4, 30, GY + 8, (220, 190, 150)); tree(cv, 148, GY, 1)
    return cv


def town():
    cv = Canvas(); sky(cv); ground(cv, (130, 130, 134))
    for i, c in enumerate(((236, 170, 140), (170, 200, 220), (240, 222, 140))):
        x = 22 + i * 40
        h = 38 + (i % 2) * 6
        cv.box(x, GY - h, 36, h, c, shade(c, 0.6))
        cv.box(x - 2, GY - h - 4, 40, 4, shade(c, 0.5), shade(c, 0.35))
        for r in range(3):
            window(cv, x + 6, GY - h + 4 + r * 11, 6, 7, (i + r) % 2 == 0)
            window(cv, x + 24, GY - h + 4 + r * 11, 6, 7, (i + r) % 3 == 0)
        door(cv, x + 14, GY - 10, 8, 10, (90, 60, 50))
    return cv


def chalet():
    cv = Canvas(); sky(cv, "snow"); mountains(cv, GY, (110, 130, 170)); ground(cv, (236, 244, 250))
    cv.poly([(40, GY), (80, 16), (120, GY)], (150, 96, 52)); cv.poly([(40, GY), (80, 16), (84, 16), (50, GY)], (120, 74, 40))
    cv.poly([(34, GY), (80, 10), (126, GY), (118, GY), (80, 20), (42, GY)], (240, 246, 252))
    cv.box(60, 30, 40, 24, (130, 80, 44), (60, 34, 18)); window(cv, 66, 34, 10, 10, True); window(cv, 84, 34, 10, 10, True)
    door(cv, 74, 46, 12, 16, (80, 48, 28)) if False else door(cv, 76, 48, 8, 14, (80, 48, 28))
    pine(cv, 20, GY, 1, snow=True); pine(cv, 138, GY, 1, snow=True); pine(cv, 150, GY, 1, snow=True)
    return cv


def cottage():
    cv = Canvas(); sky(cv); ground(cv, (96, 170, 84))
    cv.box(48, 38, 60, 24, (250, 236, 206), (150, 130, 100))
    cv.poly([(42, 38), (114, 38), (100, 20), (56, 20)], (150, 110, 60)); cv.line([(42, 38), (56, 20), (100, 20), (114, 38)], (100, 70, 36))
    cv.rect(96, 22, 5, 14, (160, 100, 80)); smoke(cv, 98, 20)
    cv.ell(56, 44, 10, 10, (150, 200, 240), (110, 80, 50)); window(cv, 90, 44, 8, 8, True); door(cv, 74, 50, 8, 12, (170, 60, 70))
    for x, c in ((46, (240, 90, 130)), (52, (250, 210, 60)), (60, (180, 100, 240)), (100, (240, 90, 130)), (106, (250, 210, 60))):
        cv.px(x, GY - 2, c); cv.px(x, GY - 1, (50, 130, 50))
    tree(cv, 24, GY, 1); tree(cv, 138, GY, 1, (60, 150, 70))
    return cv


def townvilla():
    cv = Canvas(); sky(cv); ground(cv, (90, 160, 90))
    cv.box(34, 28, 92, 34, (240, 226, 200), (140, 120, 96)); cv.box(30, 24, 100, 5, (120, 70, 60), (70, 36, 30))
    for c in range(4):
        window(cv, 42 + c * 20, 33, 8, 9, c % 2 == 0)
    for c in range(3):
        window(cv, 52 + c * 20, 47, 8, 9, c == 1)
    door(cv, 76, 50, 8, 12, (70, 50, 40)) if False else None
    cv.box(40, 44, 80, 3, (60, 60, 70)); [cv.rect(x, 44, 1, 3, (200, 200, 210)) for x in range(42, 120, 5)]
    tree(cv, 18, GY, 1); tree(cv, 144, GY, 1)
    return cv


def villa():
    cv = Canvas(); sky(cv); ground(cv, (92, 160, 84))
    cv.box(34, 30, 92, 32, (252, 240, 214), (150, 130, 100))
    cv.poly([(28, 30), (132, 30), (116, 16), (44, 16)], (200, 90, 56)); cv.line([(28, 30), (44, 16), (116, 16), (132, 30)], (130, 50, 30))
    for c in range(4):
        x = 42 + c * 20
        cv.d.pieslice([x, 38, x + 12, 50], 180, 360, fill=(150, 200, 240)); cv.rect(x, 44, 12, 8, (150, 200, 240))
        cv.rect(x + 6, 38, 1, 14, (110, 90, 70))
    cv.rect(72, 52, 16, 10, (110, 70, 44))
    cv.ell(10, 64, 28, 10, (90, 190, 230), (230, 230, 230)); cv.ell(122, 64, 28, 10, (90, 190, 230), (230, 230, 230))
    cv.rect(0, 62, 160, 1, (120, 180, 110)) if False else None
    tree(cv, 150, GY, 1)
    return cv


def lakehouse():
    cv = Canvas(); sky(cv, "day"); mountains(cv, 40, (110, 140, 170))
    cv.rect(0, 40, 160, 40, (60, 150, 210))
    for i in range(6):
        cv.rect(10 + i * 26, 46 + (i * 7) % 24, 14, 1, (170, 220, 245))
    cv.rect(0, 62, 60, 18, (96, 150, 80))
    house(cv, 12, 62, 44, 22, (180, 124, 70), (70, 80, 100), "gable", 1, 2, chimney=True)
    cv.rect(56, 60, 70, 3, (150, 110, 70))
    for x in (62, 80, 98, 116):
        cv.rect(x, 62, 2, 10, (110, 80, 50))
    cv.ell(100, 50, 18, 5, (240, 240, 240)); cv.poly([(100, 50), (110, 36), (112, 50)], (240, 240, 245)); cv.line([(110, 36), (110, 50)], (110, 80, 50))
    pine(cv, 142, 70, 1)
    return cv


def mansion():
    cv = Canvas(); sky(cv); ground(cv, (80, 156, 84))
    cv.box(26, 24, 108, 38, (248, 244, 232), (150, 140, 120))
    cv.poly([(20, 24), (140, 24), (122, 10), (38, 10)], (90, 100, 130)); cv.line([(20, 24), (38, 10), (122, 10), (140, 24)], (50, 56, 80))
    cv.poly([(56, 32), (104, 32), (80, 16)], (250, 246, 236)); cv.line([(56, 32), (80, 16), (104, 32)], (150, 140, 120))
    for x in (60, 68, 88, 96):
        cv.rect(x, 32, 3, 30, (255, 252, 244)); cv.rect(x + 2, 32, 1, 30, (200, 196, 186))
    door(cv, 76, 46, 8, 16, (110, 60, 40))
    for c in range(2):
        window(cv, 34 + c * 14, 32, 7, 10, True); window(cv, 106 + c * 14, 32, 7, 10, c == 0)
        window(cv, 34 + c * 14, 46, 7, 10, False); window(cv, 106 + c * 14, 46, 7, 10, True)
    cv.ell(70, 66, 20, 7, (120, 190, 230), (230, 230, 230)); cv.rect(79, 62, 2, 6, (200, 230, 250))
    tree(cv, 14, GY, 1); tree(cv, 148, GY, 1)
    return cv


def penthouse():
    cv = Canvas(); sky(cv, "night")
    for x, h in ((0, 30), (14, 44), (30, 34), (100, 40), (116, 52), (132, 36), (146, 46)):
        cv.rect(x, 80 - h, 14, h, (30, 32, 60))
        for yy in range(80 - h + 3, 78, 5):
            for xx in range(x + 2, x + 12, 4):
                if (xx + yy) % 3:
                    cv.px(xx, yy, (250, 220, 120))
    cv.box(44, 56, 72, 24, (50, 54, 90), (20, 22, 50))
    cv.box(50, 30, 60, 26, (130, 200, 240), (40, 60, 90)); cv.rect(50, 30, 60, 3, (60, 70, 100))
    for x in (65, 80, 95):
        cv.rect(x, 33, 1, 23, (40, 60, 90))
    cv.rect(52, 36, 8, 12, (255, 232, 150)); cv.rect(100, 36, 8, 12, (255, 232, 150))
    cv.box(54, 62, 40, 10, (80, 200, 240), (230, 240, 250))
    for x in range(56, 92, 6):
        cv.rect(x, 66, 3, 1, (200, 240, 255))
    return cv


def beachvilla():
    cv = Canvas(); sky(cv, "sea"); sea(cv, 40); cv.poly([(0, 58), (160, 58), (160, 80), (0, 80)], (240, 218, 164))
    cv.box(40, 36, 80, 24, (252, 252, 252), (170, 170, 180)); cv.box(36, 32, 88, 4, (60, 70, 90), (30, 34, 50))
    cv.box(46, 40, 42, 16, (130, 200, 240), (60, 80, 100)); [cv.rect(x, 40, 1, 16, (60, 80, 100)) for x in (57, 68, 79)]
    cv.box(94, 40, 20, 20, (252, 252, 252), (170, 170, 180)); window(cv, 98, 44, 12, 12, True)
    cv.ell(34, 66, 26, 8, (90, 200, 240), (250, 250, 250))
    palm(cv, 18, 62, 26); palm(cv, 142, 66, 24)
    cv.poly([(124, 66), (140, 66), (132, 60)], (230, 70, 80))
    return cv


def modern():
    cv = Canvas(); sky(cv, "day"); ground(cv, (86, 150, 96))
    cv.box(30, 40, 60, 22, (236, 238, 242), (130, 134, 146))
    cv.box(60, 22, 70, 20, (60, 64, 76), (30, 32, 40))
    cv.box(64, 26, 62, 12, (130, 200, 240), (60, 80, 100)); [cv.rect(x, 26, 1, 12, (60, 80, 100)) for x in (78, 94, 110)]
    cv.box(34, 44, 44, 14, (130, 200, 240), (60, 80, 100)); cv.rect(56, 44, 1, 14, (60, 80, 100))
    cv.box(82, 46, 6, 16, (60, 64, 76), (30, 32, 40))
    cv.rect(90, 42, 40, 2, (60, 64, 76)); cv.rect(92, 44, 2, 18, (170, 174, 186))
    cv.box(96, 54, 30, 8, (80, 70, 60), (50, 44, 40)) if False else None
    cv.ell(100, 62, 40, 8, (90, 200, 240), (240, 240, 246))
    tree(cv, 16, GY, 1, (50, 140, 80)); tree(cv, 150, GY, 1)
    return cv


def castle():
    cv = Canvas(); sky(cv, "sunset"); ground(cv, (70, 110, 70))
    cv.box(40, 30, 80, 32, (160, 160, 172), (80, 80, 96))
    for x in range(40, 120, 8):
        cv.rect(x, 26, 5, 5, (160, 160, 172))
    for x, h in ((26, 46), (118, 46)):
        cv.box(x, GY - h, 18, h, (176, 176, 188), (80, 80, 96))
        for k in range(0, 18, 6):
            cv.rect(x + k, GY - h - 4, 4, 5, (176, 176, 188))
        cv.poly([(x - 2, GY - h - 4), (x + 20, GY - h - 4), (x + 9, GY - h - 18)], (180, 50, 60))
        cv.rect(x + 9, GY - h - 24, 1, 6, (110, 90, 60)); cv.poly([(x + 10, GY - h - 24), (x + 17, GY - h - 22), (x + 10, GY - h - 20)], (250, 200, 50))
        cv.rect(x + 6, GY - h + 8, 6, 9, (30, 30, 44))
    cv.d.pieslice([68, 40, 92, 64], 180, 360, fill=(60, 36, 24)); cv.rect(68, 52, 24, 10, (60, 36, 24))
    for y in range(44, 62, 3):
        cv.rect(70, y, 20, 1, (110, 80, 50))
    cv.rect(56, 36, 5, 8, (30, 30, 44)); cv.rect(99, 36, 5, 8, (30, 30, 44))
    cv.rect(0, 62, 160, 4, (60, 130, 200))
    return cv


def palace():
    cv = Canvas(); sky(cv, "day"); ground(cv, (88, 158, 90))
    cv.box(36, 34, 88, 28, (252, 244, 220), (170, 150, 110))
    cv.box(62, 26, 36, 36, (255, 250, 232), (170, 150, 110))
    cv.d.pieslice([62, 8, 98, 44], 180, 360, fill=(240, 190, 60)); cv.line([(62, 26), (98, 26)], (170, 120, 20)); cv.rect(79, 2, 2, 8, (240, 190, 60))
    for x in (30, 124):
        cv.box(x, 22, 8, 40, (255, 250, 232), (170, 150, 110)); cv.poly([(x - 1, 22), (x + 9, 22), (x + 4, 8)], (240, 190, 60))
    for c in range(4):
        cv.d.pieslice([42 + c * 14 if c < 2 else 70 + c * 14 - 28 + 28, 38, 54 + c * 14 if c < 2 else 82 + c * 14 - 28 + 28, 50], 180, 360, fill=(110, 170, 220))
    cv.d.pieslice([72, 42, 88, 58], 180, 360, fill=(110, 60, 40)); cv.rect(72, 50, 16, 12, (110, 60, 40))
    return cv


def tower():
    cv = Canvas(); sky(cv, "day"); ground(cv, (86, 150, 90))
    cv.box(66, 8, 28, 54, (180, 190, 210), (80, 90, 110))
    for r in range(5):
        for c in range(2):
            window(cv, 70 + c * 12, 14 + r * 9, 8, 6, (r + c) % 2 == 0)
    cv.box(62, 4, 36, 5, (120, 130, 150), (60, 70, 90)); cv.rect(79, 0, 2, 5, (200, 60, 60))
    door(cv, 74, 52, 12, 10, (70, 80, 110))
    cv.ell(40, 40, 14, 6, (230, 230, 240)); cv.ell(110, 22, 14, 6, (230, 230, 240))
    tree(cv, 28, GY, 1); tree(cv, 132, GY, 1)
    return cv


def island():
    cv = Canvas(); sky(cv, "sea"); sea(cv, 40)
    cv.ell(34, 46, 92, 26, (238, 214, 160), (210, 180, 120)); cv.ell(46, 44, 70, 18, (100, 176, 90))
    cv.box(66, 38, 28, 14, (220, 190, 130), (120, 90, 50)); cv.poly([(62, 38), (98, 38), (80, 26)], (190, 150, 70))
    door(cv, 76, 42, 7, 10, (110, 70, 40)) if False else cv.rect(76, 44, 7, 8, (110, 70, 40))
    palm(cv, 52, 56, 24); palm(cv, 112, 58, 22)
    cv.poly([(130, 54), (146, 54), (138, 44)], (250, 250, 250)); cv.rect(129, 54, 18, 3, (140, 90, 50))
    return cv


def yacht():
    cv = Canvas(); sky(cv, "sea"); sea(cv, 46)
    cv.poly([(20, 56), (140, 56), (126, 68), (32, 68)], (250, 250, 252)); cv.poly([(20, 56), (140, 56), (138, 60), (22, 60)], (40, 70, 140))
    cv.box(46, 44, 64, 12, (252, 252, 254), (150, 150, 160)); cv.box(60, 34, 36, 11, (252, 252, 254), (150, 150, 160))
    for x in range(50, 106, 8):
        cv.rect(x, 48, 5, 4, (110, 180, 230))
    for x in (64, 74, 84):
        cv.rect(x, 37, 6, 4, (110, 180, 230))
    cv.rect(77, 24, 2, 11, (150, 150, 160)); cv.poly([(79, 24), (88, 27), (79, 30)], (230, 60, 70))
    cv.rect(0, 68, 160, 12, (30, 110, 190)); [cv.rect(x, 72, 6, 1, (170, 220, 245)) for x in range(4, 160, 20)]
    return cv


def space():
    cv = Canvas(); sky(cv, "space")
    cv.ell(100, 40, 70, 70, (40, 100, 200)); cv.ell(116, 48, 28, 18, (70, 170, 90)); cv.ell(130, 60, 20, 12, (70, 170, 90))
    cv.rect(0, 0, 160, 20, (4, 4, 20)) if False else None
    cv.box(52, 32, 56, 16, (210, 216, 230), (90, 96, 120)); cv.box(70, 22, 20, 36, (190, 198, 216), (90, 96, 120))
    for x in (4, 112):
        cv.box(x, 34, 40, 12, (40, 80, 190), (20, 30, 90))
        for k in range(x + 8, x + 40, 8):
            cv.rect(k, 34, 1, 12, (20, 30, 90))
    cv.ell(76, 36, 8, 8, (100, 190, 250), (40, 60, 100)); cv.rect(66, 30, 3, 20, (250, 200, 50)); cv.rect(92, 30, 3, 20, (250, 200, 50))
    cv.line([(80, 22), (80, 12)], (210, 216, 230)); cv.ell(77, 9, 6, 4, (250, 80, 80))
    for sx, sy in ((20, 14), (140, 10), (30, 64), (60, 70)):
        sparkle(cv, sx, sy, (255, 250, 200))
    return cv


BUILDERS = {
    "tent": tent, "container": container, "ger": ger, "cabin": cabin, "studio": studio, "hut": hut,
    "loft": loft, "flat": flat, "duplex": duplex, "bungalow": bungalow, "yard": yard, "farmhouse": farmhouse,
    "town": town, "chalet": chalet, "cottage": cottage, "townvilla": townvilla, "villa": villa,
    "lakehouse": lakehouse, "mansion": mansion, "penthouse": penthouse, "beachvilla": beachvilla,
    "modern": modern, "castle": castle, "palace": palace, "tower": tower, "island": island,
    "yacht": yacht, "space": space,
}


def house_bytes(key: str) -> bytes:
    if key not in _cache:
        _cache[key] = BUILDERS[key]().png()
    return _cache[key]


def house_file(key: str) -> discord.File:
    return discord.File(io.BytesIO(house_bytes(key)), filename="house.png")


def stamp_house(embed: discord.Embed) -> discord.Embed:
    embed.set_image(url="attachment://house.png")
    return embed
