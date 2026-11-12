"""Pixel-art chibi дүр (кодоор зурсан). 4 фрэймтэй алхалтын GIF + тэжээвэр амьтан."""
import io

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from petart import render_pet

LW, LH = 40, 46  # логик (pixel) хэмжээ
SCALE = 6
DEFAULT_OUTFIT = {"top": ("tee", "#9ca3af"), "bottom": ("pants", "#374151"), "shoes": ("sneaker", "#e5e7eb")}


def _rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def _sh(c, f):
    return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))), max(0, min(255, int(c[2] * f))), 255)


class Cv:
    def __init__(self):
        self.im = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def r(self, x, y, w, h, c):
        if w > 0 and h > 0:
            self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)

    def p(self, x, y, c):
        self.d.point((x, y), fill=c)


HAIR = {"male": "#2b1b12", "female": "#3a2314"}


def _character(frame, gender, skin_hex, outfit, dead=False):
    """Нэг фрэймийн дүр (outline-тай, logical хэмжээ)."""
    cv = Cv()
    skin = _rgb(skin_hex)
    hair = _rgb(HAIR.get(gender, "#2b1b12"))
    fem = gender == "female"
    top_style, top_c = outfit.get("top", DEFAULT_OUTFIT["top"])
    bot_style, bot_c = outfit.get("bottom", DEFAULT_OUTFIT["bottom"])
    sh_style, sh_c = outfit.get("shoes", DEFAULT_OUTFIT["shoes"])
    top_c, bot_c, sh_c = _rgb(top_c) if isinstance(top_c, str) else top_c, _rgb(bot_c) if isinstance(bot_c, str) else bot_c, _rgb(sh_c) if isinstance(sh_c, str) else sh_c
    bob = 1 if frame in (1, 3) and not dead else 0
    lift_l = 1 if frame == 0 else 0  # зүүн хөл гарна
    lift_r = 1 if frame == 2 else 0
    swing = {0: (1, -1), 1: (0, 0), 2: (-1, 1), 3: (0, 0)}[frame] if not dead else (0, 0)
    ox = 10  # дүрийн зүүн ирмэг
    oy = 8 - bob
    hx = ox + 2  # толгойн x

    # ---- хөл ----
    ly = oy + 23
    long_bottom = bot_style in ("pants", "jeans")
    for i, lift in ((0, lift_l), (1, lift_r)):
        x = ox + 5 + i * 8
        y = ly - lift
        if long_bottom:
            cv.r(x, y, 4, 8, bot_c)
            cv.r(x, y, 1, 8, _sh(bot_c, 0.8))
        elif bot_style == "shorts":
            cv.r(x, y, 4, 4, bot_c)
            cv.r(x, y + 4, 4, 4, skin)
        elif bot_style == "skirt":
            cv.r(x, y + 2, 4, 6, skin)
        else:
            cv.r(x, y, 4, 8, bot_c)
        # гутал
        by = y + 8
        st = sh_style
        if st == "boot" or st == "mongolboot":
            cv.r(x - 1, by - 3, 6, 5, sh_c)
            cv.r(x - 1, by - 3, 6, 1, _sh(sh_c, 1.25))
            if st == "mongolboot":
                cv.p(x + (4 if i else -2), by + 1, sh_c)
                cv.p(x + (4 if i else -2), by, sh_c)
        elif st == "sandal":
            cv.r(x - 1, by, 6, 2, sh_c)
            cv.r(x, by - 1, 4, 1, _sh(sh_c, 0.8))
        elif st == "dress":
            cv.r(x - 1, by - 1, 6, 3, _sh(sh_c, 0.55))
            cv.r(x - 1, by - 1, 6, 1, _sh(sh_c, 0.9))
        else:  # sneaker
            cv.r(x - 1, by - 1, 6, 3, sh_c)
            cv.r(x - 1, by + 1, 6, 1, (245, 245, 245, 255) if sum(sh_c[:3]) < 650 else (160, 160, 160, 255))
    # ---- банзал ----
    if bot_style == "skirt":
        cv.r(ox + 3, oy + 22, 14, 5, bot_c)
        cv.r(ox + 2, oy + 25, 16, 2, bot_c)
        cv.r(ox + 3, oy + 26, 14, 1, _sh(bot_c, 0.8))
    # ---- гар (хөдөлгөөнтэй) ----
    sleeves_long = top_style in ("hoodie", "shirt", "jacket", "sweater", "coat", "deel", "suit")
    for i, sw in ((0, swing[0]), (1, swing[1])):
        ax = ox + (-1 if i == 0 else 16)
        ay = oy + 15 + sw
        cv.r(ax, ay, 3, 9, skin)
        sl = 8 if sleeves_long else 4
        cv.r(ax, ay, 3, sl, top_c)
        cv.r(ax, ay + sl - 1 if sleeves_long else ay + sl - 1, 3, 1, _sh(top_c, 0.8))
    # ---- бие ----
    bw = 12 if fem else 14
    bx = ox + (3 if fem else 2)
    tall = 8
    if top_style in ("coat", "deel"):
        tall = 13
    if top_style == "dress":
        tall = 14
    cv.r(bx, oy + 15, bw, tall, top_c)
    cv.r(bx, oy + 15, bw, 1, _sh(top_c, 1.2))
    cv.r(bx, oy + 15 + tall - 1, bw, 1, _sh(top_c, 0.8))
    if top_style == "dress":
        cv.r(bx - 1, oy + 25, bw + 2, 4, top_c)
        cv.r(bx - 1, oy + 28, bw + 2, 1, _sh(top_c, 0.8))
    if top_style == "hoodie":
        cv.r(bx + 2, oy + 19, bw - 4, 3, _sh(top_c, 0.85))
        cv.r(bx + 2, oy + 14, bw - 4, 2, _sh(top_c, 0.8))
        cv.p(bx + 5, oy + 17, (240, 240, 240, 255))
        cv.p(bx + bw - 6, oy + 17, (240, 240, 240, 255))
    elif top_style == "shirt":
        cv.r(bx + bw // 2, oy + 16, 1, 7, _sh(top_c, 0.75))
        cv.r(bx + 2, oy + 15, 3, 2, (245, 245, 245, 255))
        cv.r(bx + bw - 5, oy + 15, 3, 2, (245, 245, 245, 255))
    elif top_style == "jacket":
        cv.r(bx + bw // 2 - 1, oy + 15, 1, 8, _sh(top_c, 0.65))
        cv.r(bx + 1, oy + 20, 3, 1, _sh(top_c, 0.75))
        cv.r(bx + bw - 4, oy + 20, 3, 1, _sh(top_c, 0.75))
    elif top_style == "sweater":
        for k in range(0, bw, 2):
            cv.p(bx + k, oy + 18, _sh(top_c, 0.85))
            cv.p(bx + k + 1, oy + 20, _sh(top_c, 0.85))
    elif top_style == "coat":
        cv.r(bx + bw // 2, oy + 15, 1, 13, _sh(top_c, 0.6))
        for yy in (18, 21, 24):
            cv.p(bx + bw // 2 - 2, oy + yy, (230, 230, 230, 255))
            cv.p(bx + bw // 2 + 2, oy + yy, (230, 230, 230, 255))
    elif top_style == "deel":
        cv.r(bx, oy + 21, bw, 2, (250, 204, 21, 255))  # бүс
        cv.r(bx + bw - 4, oy + 15, 1, 6, (250, 204, 21, 255))
        cv.r(bx, oy + 15, bw, 1, (250, 204, 21, 255))
    elif top_style == "suit":
        cv.r(bx + 5, oy + 15, 4, 7, (245, 245, 245, 255))
        cv.r(bx + 6, oy + 16, 2, 6, (220, 38, 38, 255))
        cv.r(bx + 2, oy + 16, 2, 6, _sh(top_c, 0.7))
        cv.r(bx + bw - 4, oy + 16, 2, 6, _sh(top_c, 0.7))
    # ---- толгой ----
    cv.r(hx + 3, oy + 13, 6, 3, skin)  # хүзүү
    if fem:  # арын үс
        cv.r(hx - 1, oy + 4, 16, 12, hair)
    cv.r(hx, oy + 3, 14, 12, skin)
    cv.r(hx - 1, oy + 5, 1, 7, skin)
    cv.r(hx + 14, oy + 5, 1, 7, skin)
    # үс
    cv.r(hx - 1, oy + 1, 16, 5, hair)
    cv.r(hx - 1, oy + 1, 16, 1, _sh(hair, 1.4))
    cv.r(hx - 1, oy + 5, 3, 3 if not fem else 6, hair)
    cv.r(hx + 12, oy + 5, 3, 3 if not fem else 6, hair)
    if fem:
        cv.r(hx + 2, oy + 5, 6, 1, hair)
        cv.r(hx + 8, oy + 5, 3, 2, hair)
    else:
        cv.r(hx + 3, oy + 5, 3, 1, hair)
        cv.r(hx + 9, oy + 5, 2, 1, hair)
    # нүд
    if dead:
        for ex in (hx + 3, hx + 9):
            cv.p(ex, oy + 8, (220, 38, 38, 255)); cv.p(ex + 2, oy + 8, (220, 38, 38, 255))
            cv.p(ex + 1, oy + 9, (220, 38, 38, 255))
            cv.p(ex, oy + 10, (220, 38, 38, 255)); cv.p(ex + 2, oy + 10, (220, 38, 38, 255))
        cv.r(hx + 5, oy + 12, 4, 1, (60, 30, 30, 255))
    else:
        for ex in (hx + 3, hx + 9):
            cv.r(ex, oy + 8, 2, 3, (20, 20, 30, 255))
            cv.p(ex, oy + 8, (255, 255, 255, 255))
        cv.r(hx + 2, oy + 11, 2, 1, (244, 143, 160, 255))
        cv.r(hx + 10, oy + 11, 2, 1, (244, 143, 160, 255))
        cv.r(hx + 6, oy + 12, 2, 1, (150, 60, 60, 255))
    # ---- сэлбэг (гоёл) ----
    acc_style, acc_c = outfit.get("acc", (None, None))
    if acc_style:
        ac = _rgb(acc_c) if isinstance(acc_c, str) else acc_c
        if acc_style == "glasses":
            cv.r(hx + 2, oy + 7, 4, 4, (0, 0, 0, 0))
            for ex in (hx + 2, hx + 8):
                cv.d.rectangle([ex, oy + 7, ex + 3, oy + 10], outline=ac)
            cv.p(hx + 6, oy + 8, ac); cv.p(hx + 7, oy + 8, ac)
        elif acc_style == "necklace":
            cv.r(bx + 3, oy + 15, bw - 6, 1, ac)
            cv.p(bx + bw // 2 - 1, oy + 16, ac); cv.p(bx + bw // 2, oy + 17, (255, 230, 120, 255))
        elif acc_style == "scarf":
            cv.r(bx, oy + 14, bw, 3, ac)
            cv.r(bx + bw - 3, oy + 17, 3, 6, ac)
        elif acc_style == "belt":
            cv.r(bx, oy + 22, bw, 1, ac)
            cv.r(bx + bw // 2 - 1, oy + 22, 2, 1, (250, 204, 21, 255))
        elif acc_style == "watch":
            cv.r(ox + 16, oy + 22 + swing[1], 3, 2, ac)
            cv.p(ox + 17, oy + 22 + swing[1], (255, 255, 255, 255))
        elif acc_style == "bag":
            cv.d.line([(bx + 1, oy + 15), (bx + bw + 1, oy + 24)], fill=_sh(ac, 0.8))
            cv.r(bx + bw - 1, oy + 22, 5, 5, ac)
            cv.r(bx + bw - 1, oy + 22, 5, 1, _sh(ac, 1.3))
    # ---- малгай ----
    hat_style, hat_c = outfit.get("hat", (None, None))
    if hat_style:
        hc = _rgb(hat_c) if isinstance(hat_c, str) else hat_c
        hl = _sh(hc, 1.25)
        if hat_style == "cap":
            cv.r(hx - 1, oy, 16, 5, hc); cv.r(hx - 1, oy, 16, 1, hl)
            cv.r(hx + 4, oy + 5, 14, 2, _sh(hc, 0.8))
        elif hat_style == "beanie":
            cv.r(hx - 1, oy - 1, 16, 6, hc); cv.r(hx - 2, oy + 4, 18, 2, _sh(hc, 0.8))
            cv.r(hx + 6, oy - 3, 3, 2, hl)
        elif hat_style == "bucket":
            cv.r(hx, oy - 1, 14, 5, hc); cv.r(hx - 3, oy + 4, 20, 2, _sh(hc, 0.85))
        elif hat_style == "fedora":
            cv.r(hx + 1, oy - 2, 12, 6, hc); cv.r(hx - 3, oy + 4, 20, 2, _sh(hc, 0.85))
            cv.r(hx + 1, oy + 2, 12, 1, (30, 30, 30, 255))
        elif hat_style == "tophat":
            cv.r(hx + 2, oy - 8, 10, 11, hc); cv.r(hx - 2, oy + 3, 18, 2, _sh(hc, 0.85))
            cv.r(hx + 2, oy, 10, 1, (220, 38, 38, 255))
        elif hat_style == "mongolhat":
            cv.r(hx - 1, oy + 1, 16, 4, hc); cv.r(hx + 5, oy - 4, 4, 5, (220, 38, 38, 255))
            cv.r(hx + 6, oy - 5, 2, 1, (250, 204, 21, 255)); cv.r(hx - 2, oy + 4, 18, 2, _sh(hc, 0.8))

    # ---- outline ----
    a = cv.im.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(3))
    ol = ImageChops.subtract(grown, a)
    outline = Image.new("RGBA", cv.im.size, (25, 20, 35, 255))
    outline.putalpha(ol)
    outline.alpha_composite(cv.im)
    if dead:
        g = outline.convert("LA").convert("RGBA")
        g.putalpha(outline.split()[3])
        outline = g
        d = ImageDraw.Draw(outline)
        d.ellipse([hx + 1, oy - 3, hx + 13, oy], outline=(250, 250, 250, 255))
    return outline


def _background(w, h):
    bg = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(70 - 30 * t), int(90 - 30 * t), int(150 - 60 * t)))
    d.rectangle([0, int(h * 0.82), w, h], fill=(52, 98, 62))
    d.rectangle([0, int(h * 0.82), w, int(h * 0.82) + 6], fill=(72, 128, 80))
    for sx, sy in ((30, 24), (110, 50), (250, 20), (300, 66), (190, 14)):
        d.rectangle([sx, sy, sx + 2, sy + 2], fill=(255, 255, 255))
    return bg


def render_scene(gender, skin_hex, outfit, dead=False, pet_key=None, name_tag=None):
    """-> (bytes, 'gif'|'png'). outfit: {slot: (style, hex)}"""
    W, H = 300, LH * SCALE
    frames = []
    bg = _background(W, H).convert("RGBA")
    pets = [render_pet(pet_key, 92, 0), render_pet(pet_key, 92, 1)] if pet_key else None
    pet_img = pets
    n = 1 if dead else 4
    for f in range(n):
        ch = _character(f, gender, skin_hex, outfit, dead)
        big = ch.resize((LW * SCALE, LH * SCALE), Image.NEAREST)
        fr = bg.copy()
        sh = ImageDraw.Draw(fr)
        sh.ellipse([60, H - 40 - 18, 60 + 190, H - 40 + 8], fill=(0, 0, 0, 0))
        shadow = Image.new("RGBA", fr.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse([40, H - 44, 170, H - 24], fill=(0, 0, 0, 70))
        fr.alpha_composite(shadow)
        fr.alpha_composite(big, (-6, -6))
        if pet_img is not None:
            bounce = 0
            p = pet_img[f % 2 if not dead else 0]
            if dead:
                p = pet_img[0].convert("LA").convert("RGBA")
                p.putalpha(pet_img[0].split()[3])
            sh2 = Image.new("RGBA", fr.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh2).ellipse([180, H - 44, 280, H - 28], fill=(0, 0, 0, 70))
            fr.alpha_composite(sh2)
            fr.alpha_composite(p, (184, H - 108 - bounce))
        frames.append(fr.convert("RGB"))
    buf = io.BytesIO()
    if n == 1:
        frames[0].save(buf, "PNG")
        return buf.getvalue(), "png"
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    pal[0].save(buf, "GIF", save_all=True, append_images=pal[1:], duration=220, loop=0, disposal=2)
    return buf.getvalue(), "gif"
