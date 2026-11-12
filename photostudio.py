"""Зургийн студи: арын зураг + дүр, хайртай хүн, машин, амьтан, байшин давхаргууд (Pillow)."""
import io
import random

from PIL import Image, ImageDraw, ImageOps

from carart import _car_layer
from itemart import icon_image
from items import car_tier, get_item
from petart import render_pet
from sprite import LH, LW, _character

W, H = 640, 400
GROUND = 330
LAYERS = ["me", "partner", "car", "pet", "house"]
LAYER_NAMES = {"me": "🧍 Би", "partner": "💑 Хайртай хүн", "car": "🚗 Машин", "pet": "🐾 Амьтан", "house": "🏠 Байшин"}
PRESET_NAMES = ["🌾 Хээр тал", "🌃 Хотын шөнө", "🏖️ Далайн эрэг", "🏔️ Уул", "❄️ Цас"]


# ---------------- pixel арын зургууд ----------------
def _preset(i: int) -> Image.Image:
    w, h = W // 4, H // 4
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    rnd = random.Random(i * 77)
    gy = GROUND // 4
    if i == 0:  # хээр тал
        for y in range(gy):
            t = y / gy
            d.line([(0, y), (w, y)], fill=(int(90 + 90 * t), int(160 + 60 * t), int(235 - 20 * t)))
        for cx, cy in ((25, 14), (80, 22), (130, 12)):
            for dx, dy, r in ((0, 0, 6), (6, 2, 5), (-6, 2, 5), (0, 3, 6)):
                d.ellipse([cx + dx - r, cy + dy - r // 2, cx + dx + r, cy + dy + r // 2], fill=(250, 250, 255))
        d.polygon([(0, gy), (30, gy - 14), (60, gy - 4), (100, gy - 16), (160, gy - 2), (160, gy)], fill=(70, 120, 86))
        d.rectangle([0, gy, w, h], fill=(88, 150, 70))
        for _ in range(60):
            x, y = rnd.randrange(w), rnd.randrange(gy, h)
            d.point((x, y), fill=(110, 175, 85))
    elif i == 1:  # хотын шөнө
        for y in range(gy):
            d.line([(0, y), (w, y)], fill=(18 + y // 4, 14 + y // 5, 48 + y // 2))
        for _ in range(26):
            d.point((rnd.randrange(w), rnd.randrange(gy // 2)), fill=(255, 255, 220))
        x = 0
        while x < w:
            bw, bh = rnd.randint(10, 22), rnd.randint(25, 62)
            d.rectangle([x, gy - bh, x + bw, gy], fill=(30 + rnd.randint(0, 20), 28, 62))
            for wx in range(x + 2, x + bw - 1, 4):
                for wy in range(gy - bh + 3, gy - 2, 5):
                    if rnd.random() < 0.55:
                        d.rectangle([wx, wy, wx + 1, wy + 2], fill=(255, 220, 120))
            x += bw + 1
        d.rectangle([0, gy, w, h], fill=(36, 36, 52))
        for x in range(0, w, 16):
            d.rectangle([x, gy + 14, x + 8, gy + 15], fill=(200, 200, 90))
    elif i == 2:  # далайн эрэг
        for y in range(gy):
            t = y / gy
            d.line([(0, y), (w, y)], fill=(int(255 - 80 * t), int(190 - 20 * t), int(110 + 100 * t)))
        d.ellipse([105, 14, 129, 38], fill=(255, 238, 150))
        d.rectangle([0, gy - 18, w, gy], fill=(40, 120, 200))
        for x in range(0, w, 12):
            d.rectangle([x, gy - 10, x + 6, gy - 10], fill=(150, 210, 250))
        d.rectangle([0, gy, w, h], fill=(238, 214, 150))
        for _ in range(40):
            d.point((rnd.randrange(w), rnd.randrange(gy, h)), fill=(214, 188, 120))
    elif i == 3:  # уул
        for y in range(gy):
            t = y / gy
            d.line([(0, y), (w, y)], fill=(int(120 + 70 * t), int(170 + 50 * t), 255))
        d.polygon([(0, gy), (40, 18), (80, gy)], fill=(98, 110, 130))
        d.polygon([(40, 18), (30, 38), (50, 38)], fill=(245, 245, 250))
        d.polygon([(60, gy), (110, 8), (160, gy)], fill=(84, 96, 118))
        d.polygon([(110, 8), (98, 34), (122, 34)], fill=(245, 245, 250))
        d.rectangle([0, gy, w, h], fill=(70, 130, 80))
        for x in range(4, w, 14):
            d.polygon([(x, gy + 4), (x + 5, gy - 12), (x + 10, gy + 4)], fill=(34, 90, 52))
    else:  # цас
        for y in range(gy):
            t = y / gy
            d.line([(0, y), (w, y)], fill=(int(170 + 60 * t), int(190 + 50 * t), int(225 + 20 * t)))
        d.rectangle([0, gy, w, h], fill=(240, 244, 252))
        for _ in range(60):
            d.point((rnd.randrange(w), rnd.randrange(gy)), fill=(255, 255, 255))
        for x in (20, 70, 125):
            d.polygon([(x, gy + 2), (x + 8, gy - 20), (x + 16, gy + 2)], fill=(40, 100, 70))
            d.polygon([(x + 3, gy - 12), (x + 8, gy - 20), (x + 13, gy - 12)], fill=(240, 246, 252))
    return im.resize((W, H), Image.NEAREST)


def make_background(index: int, custom: Image.Image | None) -> Image.Image:
    """index 0 = өөрийн зураг (байвал), дараа нь preset-үүд."""
    if custom is not None and index == 0:
        return ImageOps.fit(custom.convert("RGB"), (W, H), Image.LANCZOS)
    i = index - (1 if custom is not None else 0)
    return _preset(i % len(PRESET_NAMES))


# ---------------- давхаргын зургууд ----------------
def _trim(im: Image.Image) -> Image.Image:
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def layer_image(kind: str, data: dict) -> Image.Image | None:
    if kind in ("me", "partner"):
        ch = _character(1, data["gender"], data["skin"], data["outfit"], False)
        ch = _trim(ch)
        base = ch.resize((ch.width * 5, ch.height * 5), Image.NEAREST)
    elif kind == "car":
        it = get_item(data["key"])
        base = _trim(_car_layer(it.name, it.level, car_tier(it.level)[1], 0, 1))
        base = base.resize((int(base.width * 0.55), int(base.height * 0.55)), Image.NEAREST)
    elif kind == "pet":
        base = _trim(render_pet(data["key"], 120))
    elif kind == "house":
        base = icon_image(data["key"], 192)
        if base is None:
            return None
        base = _trim(base)
    else:
        return None
    return base


DEFAULT_POS = {
    "me": (120, GROUND + 8, 0.75),
    "partner": (182, GROUND + 8, 0.75),
    "car": (390, GROUND + 14, 0.9),
    "pet": (262, GROUND + 12, 0.9),
    "house": (560, GROUND - 6, 1.0),
}


def default_state(available: list[str]) -> dict:
    st = {}
    for k in LAYERS:
        x, y, s = DEFAULT_POS[k]
        st[k] = {"x": x, "y": y, "scale": s, "flip": False, "visible": k in available}
    return st


def compose(bg: Image.Image, state: dict, assets: dict, order=("house", "car", "pet", "partner", "me")) -> bytes:
    canvas = bg.convert("RGBA")
    for k in order:
        st = state.get(k)
        img = assets.get(k)
        if not st or img is None or not st["visible"]:
            continue
        s = max(0.2, min(3.0, st["scale"]))
        im = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.NEAREST)
        if st["flip"]:
            im = ImageOps.mirror(im)
        # сүүдэр
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([st["x"] - im.width // 2, st["y"] - 8, st["x"] + im.width // 2, st["y"] + 8], fill=(0, 0, 0, 70))
        canvas.alpha_composite(sh)
        canvas.alpha_composite(im, (int(st["x"] - im.width / 2), int(st["y"] - im.height)))
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, "JPEG", quality=92)
    return buf.getvalue()
