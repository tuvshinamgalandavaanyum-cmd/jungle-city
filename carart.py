"""Машины зураг (1-99 түвшин): neon, градиент бичигтэй PNG / GIF."""
import colorsys
import io
import zlib
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from items import CAR_TIERS, car_tier

W, H = 640, 360
FONT_PATHS = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
GRADS = [
    [(34, 197, 94), (34, 211, 238)],  # Beginner
    [(249, 115, 22), (250, 204, 21)],  # Hard
    [(139, 92, 246), (236, 72, 153)],  # Expert
    [(245, 158, 11), (239, 68, 68), (250, 204, 21)],  # Legend
    [(34, 211, 238), (168, 85, 247), (244, 63, 94)],  # Impossible
]
SUV = ("RAV4", "CR-V", "Tucson", "Sportage", "CX-5", "Forester", "Highlander", "Explorer", "Prado", "Pajero",
       "RX", "Q7", "X5", "XC60", "Qashqai", "Cruiser", "LX", "Macan", "Range", "G63")
SPORT = ("911", "Ferrari", "Lamborghini", "McLaren", "Aston", "Bugatti", "Koenigsegg", "M5", "RS6", "Model S")


def _font(size):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _lerp_grad(stops, t):
    t = t % 1.0
    n = len(stops)
    pos = t * n
    i = int(pos) % n
    f = pos - int(pos)
    a, b = stops[i], stops[(i + 1) % n]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


def gradient_text(text, size, stops, shift=0.0):
    """Градиент өнгөтэй, glow-той бичвэр (RGBA)."""
    f = _font(size)
    tmp = Image.new("L", (10, 10))
    l, t, r, b = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=f)
    w, h = r - l + 40, b - t + 40
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((20 - l, 20 - t), text, font=f, fill=255)
    grad = Image.new("RGB", (w, h))
    gd = ImageDraw.Draw(grad)
    for x in range(w):
        gd.line([(x, 0), (x, h)], fill=_lerp_grad(stops, x / max(1, w) + shift))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = grad.copy().convert("RGBA")
    glow.putalpha(mask.filter(ImageFilter.GaussianBlur(7)))
    out.alpha_composite(glow)
    out.alpha_composite(glow)
    body = grad.convert("RGBA")
    body.putalpha(mask)
    out.alpha_composite(body)
    return out


SHAPES = {
    # жижиг, өндөр "kei" машин (богино)
    "kei": dict(body=[(70,134),(70,70),(86,50),(110,36),(300,36),(330,60),(384,92),(402,134),(398,146),(74,146)],
                cab=[(116,44),(296,44),(318,64),(112,84),(84,84),(88,56)], wheels=(124, 346, 26)),
    # хэчбек: босоо арын хаалга
    "hatch": dict(body=[(34,134),(34,70),(50,56),(110,44),(262,44),(330,90),(412,100),(434,134),(430,146),(36,146)],
                  cab=[(116,52),(256,52),(310,90),(60,90),(54,62)], wheels=(112, 352, 28)),
    # седан: 3 хайрцаг (ачаа тээшний тавцан тод)
    "sedan": dict(body=[(18,128),(18,96),(110,94),(146,48),(290,48),(340,92),(430,98),(446,128),(442,144),(22,144)],
                  cab=[(152,56),(286,56),(324,92),(122,92)], wheels=(98, 372, 29)),
    # SUV: өндөр, том дугуй
    "suv": dict(body=[(26,136),(26,70),(46,34),(354,30),(386,78),(432,88),(446,136),(442,152),(30,152)],
                cab=[(56,42),(348,38),(374,78),(40,78)], wheels=(110, 366, 36)),
    # boxy: хавтгай дээвэр, босоо цонх (G-класс, Prado)
    "boxy": dict(body=[(26,138),(26,24),(40,18),(344,18),(360,84),(436,90),(446,138),(442,152),(30,152)],
                 cab=[(46,28),(338,28),(352,80),(40,80)], wheels=(110, 368, 36)),
    # вагон: урт дээвэр
    "wagon": dict(body=[(18,132),(18,92),(50,56),(310,50),(356,92),(432,98),(446,132),(442,144),(22,144)],
                  cab=[(56,64),(304,58),(342,92),(40,92)], wheels=(100, 368, 29)),
    # fastback
    "fastback": dict(body=[(18,132),(22,110),(70,100),(160,62),(280,54),(344,92),(430,104),(446,130),(442,142),(22,142)],
                     cab=[(166,70),(276,62),(320,94),(130,98)], wheels=(104, 368, 28)),
    # coupe: урт хоншоортой
    "coupe": dict(body=[(18,134),(24,106),(76,96),(170,66),(250,64),(330,100),(440,110),(448,132),(444,142),(22,142)],
                  cab=[(176,72),(246,70),(300,100),(136,100)], wheels=(104, 372, 28)),
    # limo/ур өргөн Rolls
    "limo": dict(body=[(14,132),(14,84),(54,80),(84,40),(320,40),(362,84),(436,88),(452,132),(448,146),(18,146)],
                 cab=[(90,48),(314,48),(348,84),(62,84)], wheels=(98, 380, 31)),
    # wedge: нам, өнцөгтэй суперкар
    "wedge": dict(body=[(26,134),(34,122),(130,112),(210,82),(272,80),(338,106),(424,114),(448,130),(442,142),(32,142)],
                  cab=[(214,88),(268,86),(316,108),(174,110)], wheels=(112, 362, 27)),
    # hyper: Chiron/Jesko
    "hyper": dict(body=[(18,136),(22,118),(110,108),(188,76),(258,70),(326,98),(424,114),(450,132),(444,142),(24,142)],
                  cab=[(194,82),(254,76),(302,100),(158,104)], wheels=(110, 364, 28)),
}

# нэрийн хэсэг -> (хэлбэр, өнгө, онцлог). Машин бүр өөр хэлбэр/өнгө/онцлогтой (prompt-ийн дагуу).
CAR_SPEC = [
    ("Matiz", "kei", "#f97316", ("roundlight", "stripe")),
    ("i10", "kei", "#a3e635", ("grillebar", "twotone")),
    ("Picanto", "kei", "#f43f5e", ("ledstrip",)),
    ("Alto", "kei", "#e5e7eb", ("twotone", "roundlight")),
    ("Vitz", "hatch", "#38bdf8", ("roundlight",)),
    ("March", "hatch", "#fbbf24", ("roundlight", "twotone")),
    ("Fit", "hatch", "#22c55e", ("grillebar",)),
    ("Mazda 2", "hatch", "#dc2626", ("chrome", "stripe")),
    ("Aqua", "hatch", "#06b6d4", ("ledstrip", "stripe")),
    ("Prius", "fastback", "#d1d5db", ("glassroof", "tallrear")),
    ("Civic", "hatch", "#1d4ed8", ("spoiler", "grillebar")),
    ("Corolla", "sedan", "#f1f5f9", ("chrome",)),
    ("Elantra", "sedan", "#475569", ("ledstrip", "boomerang")),
    ("Rio", "sedan", "#ef4444", ("grillebar",)),
    ("Mazda 3", "hatch", "#991b1b", ("chrome", "stripe")),
    ("Impreza", "hatch", "#2563eb", ("spoiler", "scoop")),
    ("Golf", "hatch", "#9ca3af", ("stripe", "grillebar")),
    ("Focus", "hatch", "#7c3aed", ("ledstrip",)),
    ("Qashqai", "suv", "#f97316", ("rails", "blackroof", "cladding")),
    ("RAV4", "suv", "#f1f5f9", ("rails", "cladding", "flares")),
    ("CR-V", "suv", "#cbd5e1", ("rails", "grillebar", "chrome")),
    ("Tucson", "suv", "#4b5563", ("ledstrip", "cladding", "rails")),
    ("Sportage", "suv", "#2563eb", ("boomerang", "cladding", "rails")),
    ("CX-5", "suv", "#dc2626", ("chrome", "cladding")),
    ("Forester", "suv", "#15803d", ("rails", "cladding", "tallglass")),
    ("Camry", "sedan", "#1e293b", ("chrome", "grillebar")),
    ("Accord", "sedan", "#94a3b8", ("chrome",)),
    ("Sonata", "fastback", "#0f766e", ("ledstrip", "chrome")),
    ("Octavia", "wagon", "#65a30d", ("rails",)),
    ("Highlander", "suv", "#111827", ("rails", "chrome", "longwin")),
    ("Explorer", "suv", "#1e3a8a", ("rails", "twotone", "longwin")),
    ("Prado", "boxy", "#f8fafc", ("spare", "rack", "rugged", "flares")),
    ("Pajero", "boxy", "#cbd5e1", ("steps", "flares", "rugged", "cladding")),
    ("RX", "suv", "#f5f5f4", ("spindle", "floating", "chrome")),
    ("Q7", "suv", "#6b7280", ("bigGrille", "rails", "charline")),
    ("A4", "sedan", "#6b7280", ("bigGrille", "stripe")),
    ("3 Series", "sedan", "#0369a1", ("kidney", "chrome")),
    ("C-Class", "sedan", "#cbd5e1", ("chrome", "twotone")),
    ("XC60", "suv", "#cbd5e1", ("tallrear", "rails", "thor")),
    ("Model 3", "fastback", "#f8fafc", ("glassroof",)),
    ("Land Cruiser 200", "boxy", "#0b0b0f", ("rack", "chrome", "rugged")),
    ("LX 570", "boxy", "#0b0b0f", ("spindle", "chrome", "rails")),
    ("X5", "suv", "#0b0b0f", ("kidney", "rails", "hofmeister")),
    ("E-Class", "sedan", "#111827", ("chrome", "twotone")),
    ("Macan", "suv", "#6b7280", ("spoiler", "scoop", "sloped")),
    ("Range Rover", "suv", "#14532d", ("floating", "chrome", "flat")),
    ("Model S", "fastback", "#f8fafc", ("glassroof", "flush")),
    ("M5", "fastback", "#1e3a8a", ("kidney", "spoiler", "flares")),
    ("RS6", "wagon", "#4b5563", ("bigGrille", "flares", "scoop")),
    ("G63", "boxy", "#0b0b0f", ("spare", "hinges", "flat", "rugged")),
    ("911", "coupe", "#cbd5e1", ("roundlight", "spoiler", "flares")),
    ("Continental", "coupe", "#7c2d12", ("chrome", "twotone")),
    ("Ghost", "limo", "#f8fafc", ("chrome", "twotone", "spirit")),
    ("488", "wedge", "#dc2626", ("scoop", "spoiler", "ventsblack")),
    ("Huracan", "wedge", "#facc15", ("scoop", "ventsblack", "angular")),
    ("720S", "wedge", "#f97316", ("scoop", "ventsblack", "wing")),
    ("DB11", "coupe", "#14532d", ("chrome", "strake", "bigGrille")),
    ("Chiron", "hyper", "#1d4ed8", ("cline", "twotone", "horseshoe")),
    ("Jesko", "hyper", "#fafafa", ("scoop", "wing", "carbon")),
]


def _spec_for(name, level):
    for sub, shape, color, extras in CAR_SPEC:
        if sub in name:
            return shape, color, set(extras)
    shape = "wedge" if level >= 80 else "suv" if level >= 40 else "hatch"
    return shape, "#64748b", set()


def _hexc(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def _pixelate(im, px=4):
    """Pixel art: жижиг торонд буулгаж, өнгө цөөлж, 1px контур хийгээд томруулна."""
    from PIL import ImageChops
    w, h = im.size
    small = im.resize((w // px, h // px), Image.BOX)
    a = small.split()[3].point(lambda v: 255 if v > 110 else 0)
    rgb = Image.new("RGB", small.size, (0, 0, 0))
    rgb.paste(small.convert("RGB"), mask=a)
    rgb = rgb.quantize(colors=24, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    out = rgb.convert("RGBA")
    out.putalpha(a)
    ol = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)), a)
    edge = Image.new("RGBA", small.size, (20, 16, 30, 255))
    edge.putalpha(ol)
    edge.alpha_composite(out)
    return edge.resize((w, h), Image.NEAREST)


def _jitter(name):
    """Машин бүрийн хэлбэрийг өөр болгох тогтмол (нэрээс хамаарсан) өөрчлөлт."""
    h = zlib.crc32(name.encode())
    f = lambda n, lo, hi: lo + ((h >> n) & 255) / 255 * (hi - lo)  # noqa: E731
    return f(0, 0.93, 1.07), f(8, 0.90, 1.10), f(16, -3, 3)  # урт, дээврийн өндөр, дугуйн радиус


def _car_layer(name, level, tier_idx, frame, nframes):
    S = 2
    w, h = 460 * S, 190 * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shape, color, ex = _spec_for(name, level)
    sp = SHAPES[shape]
    sx, sy, dr = _jitter(name)
    GY = 144  # суурь шугам

    def T(pts):
        return [(230 + (x - 230) * sx, GY - (GY - y) * (sy if y < GY - 12 else 1.0)) for x, y in pts]

    base = _hexc(color)
    dark = tuple(int(c * 0.6) for c in base[:3]) + (255,)
    light = tuple(min(255, int(c * 1.25) + 18) for c in base[:3]) + (255,)
    black = (22, 20, 30, 255)
    chrome = (226, 232, 242, 255)

    def P(pts):
        return [(x * S, y * S) for x, y in pts]

    def R(x0, y0, x1, y1, fill, r=0):
        if r:
            d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], r * S, fill=fill)
        else:
            d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=fill)

    body, cab = T(sp["body"]), T(sp["cab"])
    xw1, xw2, wr = sp["wheels"]
    xw1, xw2 = 230 + (xw1 - 230) * sx, 230 + (xw2 - 230) * sx
    wr = max(24, wr + dr)
    rx0, fx = body[0][0], body[-3][0]  # ар, урд
    top_y = min(p[1] for p in body)

    d.polygon(P(body), fill=base)
    if "twotone" in ex:
        R(rx0 - 2, 120, fx + 8, GY + 4, dark)
        d.polygon(P(body), outline=dark)
    if "cladding" in ex:  # хар доод хэсэг
        R(rx0 - 2, 122, fx + 6, GY + 6, (38, 36, 46, 255))
    if "stripe" in ex:
        d.line(P([(rx0 + 16, 112), (fx - 6, 112)]), fill=(250, 250, 250, 255), width=5 * S)
    if "carbon" in ex:
        R(rx0, 124, fx, GY, (44, 46, 56, 255))
    if "blackroof" in ex:
        d.line(P(body[2:6]), fill=(25, 25, 30, 255), width=8 * S)
    d.line(P(body[2:6]), fill=light, width=3 * S)
    d.line(P(body + [body[0]]), fill=dark, width=3 * S)

    # цонх
    glass = (150, 220, 255, 255)
    if "glassroof" in ex:
        glass = (110, 190, 240, 255)
    if tier_idx == 4:
        glass = (90, 40, 140, 255)
    d.polygon(P(cab), fill=glass)
    if "floating" in ex:  # хар багана — "хөвж буй дээвэр"
        d.line(P(cab + [cab[0]]), fill=black, width=5 * S)
    mid = (cab[0][0] + cab[1][0]) / 2
    d.line(P([(mid, cab[0][1]), (mid + 4, cab[3][1])]), fill=dark, width=3 * S)
    if "longwin" in ex or "tallglass" in ex:
        q = cab[0][0] + (cab[1][0] - cab[0][0]) * 0.75
        d.line(P([(q, cab[0][1]), (q + 4, cab[3][1])]), fill=dark, width=3 * S)
    if "hofmeister" in ex:
        d.line(P([(cab[3][0] + 6, cab[3][1]), (cab[0][0] + 6, cab[3][1] - 10)]), fill=dark, width=2 * S)
    # хаалганы шугам
    d.line(P([(mid + 4, cab[3][1] + 2), (mid + 6, 134)]), fill=dark, width=2 * S)
    if "charline" in ex:
        d.line(P([(rx0 + 20, 108), (fx - 20, 104)]), fill=light, width=2 * S)

    # урд / хойд
    R(fx - 28, 104, fx + 4, 116, (255, 245, 160, 255), 4)  # гэрэл
    if "roundlight" in ex:
        d.ellipse([(fx - 24) * S, 100 * S, (fx + 2) * S, 124 * S], fill=(255, 250, 200, 255), outline=dark)
    if "ledstrip" in ex:
        R(fx - 36, 100, fx + 2, 103, (120, 235, 255, 255))
    if "thor" in ex:
        R(fx - 30, 100, fx - 6, 103, chrome); R(fx - 18, 100, fx - 15, 112, chrome)
    R(rx0 + 2, 104, rx0 + 18, 116, (239, 68, 68, 255), 4)  # хойд гэрэл
    if "boomerang" in ex:
        d.line(P([(rx0 + 4, 100), (rx0 + 16, 108), (rx0 + 4, 116)]), fill=(255, 90, 90, 255), width=3 * S)
    if "tallrear" in ex:
        R(rx0 + 2, 84, rx0 + 9, 120, (239, 68, 68, 255), 2)
    R(rx0 + 6, 128, fx, 134, dark)  # бампер
    if "chrome" in ex or "grillebar" in ex:
        R(fx - 8, 118, fx + 3, 122, chrome)
    if "chrome" in ex:
        d.line(P([(cab[3][0], cab[3][1] + 2), (cab[2][0], cab[2][1] + 2)]), fill=chrome, width=2 * S)
    if "spindle" in ex:
        d.polygon(P([(fx - 12, 112), (fx + 3, 110), (fx + 3, 134), (fx - 8, 134)]), fill=black, outline=chrome)
    if "bigGrille" in ex or "horseshoe" in ex:
        R(fx - 12, 108, fx + 3, 132, black, 3)
        R(fx - 10, 112, fx + 1, 114, chrome); R(fx - 10, 118, fx + 1, 120, chrome)
    if "kidney" in ex:
        d.ellipse([(fx - 14) * S, 112 * S, (fx - 6) * S, 128 * S], fill=black, outline=chrome)
        d.ellipse([(fx - 4) * S, 112 * S, (fx + 4) * S, 128 * S], fill=black, outline=chrome)
    if "spirit" in ex:
        R(fx - 14, 100, fx - 6, 134, chrome); R(fx - 12, 94, fx - 8, 100, chrome)

    # дээвэр, бусад
    if "rails" in ex:
        d.line(P([(cab[0][0] + 6, cab[0][1] - 5), (cab[1][0] - 6, cab[1][1] - 5)]), fill=black, width=3 * S)
        for x in (cab[0][0] + 12, cab[1][0] - 12):
            d.line(P([(x, cab[0][1] - 5), (x, cab[0][1])]), fill=black, width=2 * S)
    if "rack" in ex:
        for k in range(3):
            xx = cab[0][0] + 14 + k * (cab[1][0] - cab[0][0] - 28) / 2
            d.line(P([(xx, cab[0][1] - 9), (xx, cab[0][1])]), fill=black, width=2 * S)
        d.line(P([(cab[0][0] + 6, cab[0][1] - 9), (cab[1][0] - 6, cab[1][1] - 9)]), fill=black, width=3 * S)
    if "spoiler" in ex:
        R(rx0, 90, rx0 + 34, 94, dark); R(rx0 + 8, 94, rx0 + 12, 106, dark)
    if "wing" in ex:
        R(rx0 - 6, 66, rx0 + 50, 72, dark); R(rx0 + 14, 72, rx0 + 20, 104, dark); R(rx0 - 6, 66, rx0 + 50, 68, light)
    if "scoop" in ex or "ventsblack" in ex:
        d.polygon(P([(190, 112), (250, 112), (240, 126), (182, 126)]), fill=black)
    if "strake" in ex:
        for k in range(3):
            d.line(P([(fx - 80 + k * 5, 112), (fx - 76 + k * 5, 124)]), fill=black, width=2 * S)
    if "cline" in ex:
        d.line(P([(170, 110), (200, 100), (240, 100), (270, 116)]), fill=black, width=4 * S)
    if "angular" in ex:
        d.line(P([(fx - 70, 104), (fx - 20, 118)]), fill=dark, width=3 * S)
    if "steps" in ex:
        R(xw1 + wr - 6, 140, xw2 - wr + 6, 146, black)
    if "hinges" in ex:
        for yy in (92, 118):
            R(mid - 3, yy, mid + 1, yy + 6, black)
    if "flush" in ex:
        R(mid + 14, 104, mid + 22, 106, dark)
    if "spare" in ex:
        r2 = 17
        cx2, cy2 = rx0 - 1 - r2, 84
        d.ellipse([(cx2 - r2) * S, (cy2 - r2) * S, (cx2 + r2) * S, (cy2 + r2) * S], fill=(25, 25, 32, 255), outline=dark)
        d.ellipse([(cx2 - 8) * S, (cy2 - 8) * S, (cx2 + 8) * S, (cy2 + 8) * S], fill=(120, 124, 136, 255))

    # дугуй: хар нуман, 5 хошуутай обуд
    for cx in (xw1, xw2):
        cy = GY - wr + 14 if wr < 30 else 142
        cy = 142
        r = wr
        arch = r + (10 if ("flares" in ex or "cladding" in ex) else 7)
        d.pieslice([(cx - arch) * S, (cy - arch) * S, (cx + arch) * S, (cy + arch) * S], 180, 360, fill=black)
        if "flares" in ex:
            d.arc([(cx - arch - 3) * S, (cy - arch - 3) * S, (cx + arch + 3) * S, (cy + arch + 3) * S], 180, 360, fill=dark, width=4 * S)
        tire = 7 if "rugged" in ex else 5
        d.ellipse([(cx - r - tire) * S, (cy - r - tire) * S, (cx + r + tire) * S, (cy + r + tire) * S], fill=(20, 22, 30, 255))
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=(40, 44, 56, 255))
        rim = (180, 190, 205, 255) if tier_idx < 3 else (34, 211, 238, 255)
        ri = int(r * 0.62)
        d.ellipse([(cx - ri) * S, (cy - ri) * S, (cx + ri) * S, (cy + ri) * S], fill=rim)
        ang0 = math.radians((0, 22, 45, 67)[frame % 4])
        for k in range(5):
            ang = ang0 + k * 2 * math.pi / 5
            d.line([cx * S, cy * S, (cx + ri * math.cos(ang)) * S, (cy + ri * math.sin(ang)) * S], fill=(30, 30, 40, 255), width=3 * S)
        d.ellipse([(cx - 4) * S, (cy - 4) * S, (cx + 4) * S, (cy + 4) * S], fill=(30, 30, 40, 255))
    return _pixelate(im.resize((460, 190), Image.LANCZOS))


def _background(frame, nframes, tier_idx):
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 25 * t), int(8 + 10 * t), int(30 + 40 * t), 255))
    col = GRADS[tier_idx][0]
    # neon шугам
    hy = 262
    d.rectangle([0, hy, W, H], fill=(14, 12, 28, 255))
    off = (frame / max(1, nframes)) * 60
    for i in range(-2, 14):
        x0 = W / 2 + (i - 5.5) * 12
        x1 = W / 2 + (i - 5.5) * 130
        d.line([(x0, hy), (x1, H)], fill=col + (140,), width=2)
    for k in range(6):
        y = hy + ((k * 18 + off * 0.3) % 100) * 1.0
        if y < H:
            d.line([(0, y), (W, y)], fill=col + (90,), width=1)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line([(0, hy), (W, hy)], fill=col + (255,), width=4)
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6)))
    bg.alpha_composite(glow)
    return bg


def _fx_layer(frame, bob, ti):
    """Жолоодох эффект (pixel): хурдны шугам, утаа, тоос, урд гэрлийн цацраг."""
    q = 4
    fx = Image.new("RGBA", (W // q, H // q), (0, 0, 0, 0))
    d = ImageDraw.Draw(fx)
    base_y = (120 + bob) // q
    white = (245, 245, 255, 235)
    lens = (14, 22, 30, 38)
    L = lens[frame % 4]
    for k, yy in enumerate((base_y + 14, base_y + 22, base_y + 31)):
        ln = L - k * 4
        x_end = 28  # машины ар талд
        d.rectangle([x_end - ln, yy, x_end, yy], fill=white)
    # утаа
    sizes = (0, 2, 4, 3)
    sz = sizes[frame % 4]
    if sz:
        a = 235 if frame != 3 else 140
        for i in range(2):
            d.rectangle([30 - i * 3 - sz, base_y + 31 - i * 2 - sz, 30 - i * 3, base_y + 31 - i * 2], fill=(150, 150, 158, a))
    if frame % 4 == 3:  # тоос
        for i, (dx, dy, r) in enumerate(((20, 0, 2), (15, 1, 1), (24, 2, 1))):
            d.rectangle([dx - r, base_y + 37 - dy - r, dx + r, base_y + 37 - dy + r], fill=(176, 150, 112, 190))
    # урд гэрлийн цацраг
    bx = (110 + 448) // q
    by = base_y + 28
    for i in range(0, 20):
        d.line([(bx + i, by - i // 5), (bx + i, by + 3 + i // 3)], fill=(255, 250, 200, max(40, 210 - i * 8)))
    return fx.resize((W, H), Image.NEAREST)


def render_car(name: str, level: int, price: int | None = None, animated: bool = True) -> tuple[bytes, str]:
    tier, ti = car_tier(level)
    words = CAR_TIERS[ti][2]
    word = words[(level) % len(words)]
    from items import ITEMS
    it = ITEMS.get(name)  # name -> key байж болно
    car_name = it.name if it else name
    nframes = 4 if animated else 1
    frames = []
    for f in range(nframes):
        bg = _background(f, nframes, ti)
        shift = f / nframes
        title = gradient_text(f"LV {level} · {tier.upper()}", 40, GRADS[ti], shift)
        neon = gradient_text(f"NEON {word.upper()}", 30, GRADS[ti][::-1], -shift)
        bg.alpha_composite(title, ((W - title.width) // 2, 6))
        bg.alpha_composite(neon, ((W - neon.width) // 2, 52))
        car = _car_layer(car_name, level, ti, f, nframes)
        bob = 4 if f in (1, 3) else 0  # 1 pixel (x4) доош: түдгэлзүүр
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([110, 292, 580, 322], fill=(0, 0, 0, 120))
        bg.alpha_composite(sh)
        if animated:
            bg.alpha_composite(_fx_layer(f, bob, ti))
        bg.alpha_composite(car, (110, 120 + bob))
        d = ImageDraw.Draw(bg)
        d.text((W // 2, H - 26), car_name, font=_font(18), fill=(230, 232, 245, 255), anchor="mm")
        frames.append(bg.convert("RGB"))
    buf = io.BytesIO()
    if nframes == 1:
        frames[0].save(buf, "PNG")
        return buf.getvalue(), "png"
    pal = [fr.convert("P", palette=Image.ADAPTIVE, colors=128) for fr in frames]
    pal[0].save(buf, "GIF", save_all=True, append_images=pal[1:], duration=130, loop=0, disposal=2)
    return buf.getvalue(), "gif"
