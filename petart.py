"""Хөөрхөн (kawaii) тэжээвэр амьтны зураг. Pillow-оор кодоор зурна."""
from PIL import Image, ImageDraw

S = 160  # гаралтын хэмжээ
K = 2  # supersample


def _hex(c, a=255):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


def _darker(c, f=0.75):
    r, g, b, a = _hex(c)
    return (int(r * f), int(g * f), int(b * f), a)


# key: (body, light, ears, [extras])
# ears: round | pointy | long | floppy | big | none
SPEC = {
    "dog": ("#c8a27a", "#f3e2cc", "floppy", ["patch1"]),
    "cat": ("#f4b266", "#fff3e0", "pointy", ["stripes"]),
    "falcon": ("#8b6b4a", "#f5ebe0", "none", ["beak", "wings", "brow"]),
    "eagle": ("#5b4636", "#f8fafc", "none", ["beak", "wings", "whitehead"]),
    "chick": ("#fde047", "#fef9c3", "none", ["beak", "tuft"]),
    "duck": ("#fef3c7", "#ffffff", "none", ["flatbeak", "wings"]),
    "owl": ("#a16207", "#fde68a", "pointy", ["beak", "bigeyes", "wings"]),
    "parrot": ("#22c55e", "#fde047", "none", ["hookbeak", "wings", "tuft"]),
    "penguin": ("#1f2937", "#ffffff", "none", ["beak", "wings", "belly"]),
    "flamingo": ("#f9a8d4", "#fce7f3", "none", ["hookbeak", "wings"]),
    "swan": ("#f8fafc", "#ffffff", "none", ["flatbeak", "wings"]),
    "frog": ("#4ade80", "#bbf7d0", "none", ["bulge"]),
    "turtle": ("#65a30d", "#d9f99d", "none", ["shell"]),
    "hamster": ("#fbbf77", "#fff7ed", "round", []),
    "rabbit": ("#f1f5f9", "#fecdd3", "long", []),
    "squirrel": ("#b45309", "#fde68a", "pointy", ["tail"]),
    "pig": ("#fbcfe8", "#f9a8d4", "floppy", ["snout"]),
    "goat": ("#e5e7eb", "#ffffff", "floppy", ["horns", "beard"]),
    "sheep": ("#f8fafc", "#374151", "floppy", ["wool"]),
    "cow": ("#f8fafc", "#fbcfe8", "floppy", ["horns", "spots", "snout"]),
    "yak": ("#44403c", "#78716c", "floppy", ["longhorns", "wool"]),
    "horse": ("#92400e", "#d6a77a", "pointy", ["mane", "longface"]),
    "zebra": ("#f8fafc", "#e5e7eb", "pointy", ["zstripes", "longface"]),
    "camel": ("#d4a373", "#f5deb3", "round", ["hump"]),
    "deer": ("#c2864b", "#fde7c8", "pointy", ["antlers", "spots"]),
    "reindeer": ("#a8a29e", "#f5f5f4", "pointy", ["antlers", "rednose"]),
    "kangaroo": ("#c08457", "#f5deb3", "long", []),
    "koala": ("#94a3b8", "#e2e8f0", "big", ["darknose"]),
    "panda": ("#ffffff", "#ffffff", "blackround", ["patch"]),
    "red_panda": ("#d9480f", "#ffffff", "round", ["stripes", "patch2"]),
    "polar_bear": ("#f8fafc", "#e2e8f0", "round", []),
    "bear": ("#7c4a21", "#d6a77a", "round", []),
    "wolf": ("#94a3b8", "#e2e8f0", "pointy", ["fur"]),
    "fox": ("#f97316", "#fff7ed", "pointy", ["cheeks"]),
    "raccoon": ("#9ca3af", "#f3f4f6", "round", ["mask", "stripes"]),
    "monkey": ("#a16207", "#fde68a", "side", ["monkeyface"]),
    "gorilla": ("#374151", "#6b7280", "round", ["brow", "monkeyface"]),
    "tiger": ("#fb923c", "#fff7ed", "round", ["stripes", "cheeks"]),
    "lion": ("#f59e0b", "#fde68a", "round", ["mane"]),
    "leopard": ("#fcd34d", "#fef9c3", "round", ["spots"]),
    "snow_leopard": ("#e5e7eb", "#f8fafc", "round", ["spots"]),
    "elephant": ("#94a3b8", "#cbd5e1", "bigfloppy", ["trunk", "tusks"]),
    "giraffe": ("#fcd34d", "#fde68a", "pointy", ["spots", "ossicones", "longface"]),
    "hippo": ("#a5a1c2", "#c4b5fd", "round", ["widesnout"]),
}


def _render_smooth(key: str, size: int = S) -> Image.Image:
    body_hex, light_hex, ears, extras = SPEC.get(key, SPEC["dog"])
    W = S * K
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body, light = _hex(body_hex), _hex(light_hex)
    dark = _darker(body_hex, 0.6)
    edge = _darker(body_hex, 0.8)
    cx, cy, r = 80 * K, 72 * K, 46 * K
    ex = set(extras)

    def e(box, **kw):
        d.ellipse([v * K for v in box], **kw)

    def p(pts, **kw):
        d.polygon([(x * K, y * K) for x, y in pts], **kw)

    # сүүдэр, бие, хөл
    e((28, 140, 132, 156), fill=(0, 0, 0, 55))
    if "tail" in ex:
        e((112, 88, 150, 140), fill=body, outline=edge, width=K)
    e((46, 96, 114, 150), fill=body, outline=edge, width=K)
    if "belly" in ex or "wool" in ex:
        e((56, 104, 104, 146), fill=light if "belly" in ex else _hex("#f8fafc"))
    if "shell" in ex:
        e((38, 92, 122, 152), fill=_hex("#a16207"), outline=_darker("#a16207", 0.7), width=2 * K)
        for dx in (62, 80, 98):
            e((dx - 7, 108, dx + 7, 124), outline=_darker("#a16207", 0.7), width=K)
    if "hump" in ex:
        e((50, 66, 82, 112), fill=body, outline=edge, width=K)
        e((80, 66, 112, 112), fill=body, outline=edge, width=K)
    e((48, 138, 76, 156), fill=edge)
    e((84, 138, 112, 156), fill=edge)
    if "wings" in ex:
        e((24, 98, 54, 138), fill=_darker(body_hex, 0.85), outline=edge, width=K)
        e((106, 98, 136, 138), fill=_darker(body_hex, 0.85), outline=edge, width=K)

    # чих
    inner = _hex("#fbcfe8")
    if ears == "round":
        for x in (40, 120):
            e((x - 16, 22, x + 16, 54), fill=body, outline=edge, width=K)
            e((x - 9, 29, x + 9, 47), fill=inner)
    elif ears == "blackround":
        for x in (38, 122):
            e((x - 16, 22, x + 16, 54), fill=_hex("#111827"))
    elif ears == "side":
        for x in (30, 130):
            e((x - 18, 50, x + 18, 88), fill=body, outline=edge, width=K)
            e((x - 10, 58, x + 10, 80), fill=light)
    elif ears == "big":
        for x in (34, 126):
            e((x - 22, 18, x + 22, 62), fill=body, outline=edge, width=K)
            e((x - 13, 28, x + 13, 54), fill=_hex("#f1f5f9"))
    elif ears == "pointy":
        p([(38, 62), (44, 14), (72, 38)], fill=body, outline=edge)
        p([(122, 62), (116, 14), (88, 38)], fill=body, outline=edge)
        p([(45, 48), (47, 25), (62, 38)], fill=inner)
        p([(115, 48), (113, 25), (98, 38)], fill=inner)
    elif ears == "long":
        for x in (58, 102):
            e((x - 12, -4, x + 12, 56), fill=body, outline=edge, width=K)
            e((x - 6, 6, x + 6, 48), fill=inner)
    elif ears == "floppy":
        for x, s in ((34, -1), (126, 1)):
            e((x - 14, 38, x + 14, 92), fill=_darker(body_hex, 0.88), outline=edge, width=K)
    elif ears == "bigfloppy":
        for x in (24, 136):
            e((x - 26, 30, x + 26, 100), fill=body, outline=edge, width=K)
            e((x - 16, 42, x + 16, 90), fill=_hex("#fbcfe8"))

    # мөр, эвэр, сарвуу
    if "mane" in ex:
        for x in (50, 62, 74, 86, 98, 110):
            e((x - 10, 18, x + 10, 50), fill=_darker("#451a03", 1.0))
    if "antlers" in ex:
        for sx in (-1, 1):
            bx = 80 + sx * 22
            d.line([(bx * K, 34 * K), ((bx + sx * 10) * K, 10 * K), ((bx + sx * 22) * K, 2 * K)], fill=_hex("#92400e"), width=4 * K)
            d.line([((bx + sx * 8) * K, 18 * K), ((bx + sx * 22) * K, 14 * K)], fill=_hex("#92400e"), width=3 * K)
    if "horns" in ex or "longhorns" in ex:
        L = 22 if "longhorns" in ex else 12
        for sx in (-1, 1):
            p([(80 + sx * 26, 34), (80 + sx * (30 + L), 34 - L), (80 + sx * 18, 28)], fill=_hex("#f5f5f4"), outline=_hex("#a8a29e"))
    if "ossicones" in ex:
        for x in (66, 94):
            d.line([(x * K, 30 * K), (x * K, 12 * K)], fill=_hex("#92400e"), width=3 * K)
            e((x - 5, 6, x + 5, 16), fill=_hex("#92400e"))
    if "mane" in ex or "wool" in ex or "fur" in ex:
        pass

    # толгой
    if "wool" in ex:
        for ox, oy in ((-34, -6), (-20, -30), (0, -38), (20, -30), (34, -6), (-30, 24), (30, 24)):
            e((80 + ox - 20, 70 + oy - 18, 80 + ox + 20, 70 + oy + 18), fill=_hex("#f8fafc"), outline=_hex("#cbd5e1"), width=K)
    if "lion" in ex or "mane" in ex and key_is_lion(body_hex):
        pass
    if "mane" in ex and body_hex == "#f59e0b":  # арслангийн сэрвээ
        e((26, 18, 134, 126), fill=_hex("#b45309"), outline=_hex("#7c2d12"), width=K)
    if "fur" in ex:
        p([(40, 80), (30, 100), (50, 96)], fill=body)
        p([(120, 80), (130, 100), (110, 96)], fill=body)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=body, outline=edge, width=2 * K)

    # хэв, толбо
    if "belly" in ex or "whitehead" in ex:
        e((46, 46, 114, 112), fill=light if "belly" in ex else _hex("#ffffff"))
    if "stripes" in ex or "zstripes" in ex:
        sc = _hex("#111827", 190) if "zstripes" in ex else _darker(body_hex, 0.55)
        for x in (66, 80, 94):
            d.line([(x * K, 30 * K), (x * K, 44 * K)], fill=sc, width=3 * K)
        if "zstripes" in ex:
            for x in (46, 114):
                d.line([(x * K, 56 * K), ((x + (6 if x < 80 else -6)) * K, 74 * K)], fill=sc, width=3 * K)
    if "spots" in ex:
        sp = _hex("#78350f", 180) if body_hex not in ("#f8fafc", "#e5e7eb") else _hex("#111827", 200)
        for x, y, rr in ((54, 40, 7), (106, 46, 6), (92, 32, 5), (60, 88, 5), (112, 80, 5)):
            e((x - rr, y - rr, x + rr, y + rr), fill=sp)
    if "patch1" in ex:
        e((38, 44, 70, 76), fill=_darker(body_hex, 0.7))
    if "mask" in ex:
        e((42, 56, 118, 84), fill=_hex("#374151"))
    if "patch" in ex:
        for x in (58, 102):
            e((x - 13, 54, x + 13, 84), fill=_hex("#111827"))
    if "patch2" in ex:
        for x in (56, 104):
            e((x - 12, 58, x + 12, 82), fill=_hex("#ffffff"))
    if "cheeks" in ex:
        p([(34, 82), (52, 70), (52, 98)], fill=light)
        p([(126, 82), (108, 70), (108, 98)], fill=light)
    if "brow" in ex:
        d.line([(50 * K, 52 * K), (72 * K, 56 * K)], fill=dark, width=4 * K)
        d.line([(110 * K, 52 * K), (88 * K, 56 * K)], fill=dark, width=4 * K)

    # ам хамар (muzzle)
    if not ex & {"beak", "flatbeak", "hookbeak", "bulge", "shell"} or "shell" in ex:
        if "longface" in ex:
            e((54, 74, 106, 120), fill=light, outline=edge, width=K)
        elif "widesnout" in ex:
            e((44, 74, 116, 118), fill=light, outline=edge, width=K)
        elif "monkeyface" in ex:
            e((52, 56, 108, 112), fill=light)
        else:
            e((56, 74, 104, 104), fill=light)

    # нүд
    eye_y = 62 if "bigeyes" not in ex else 60
    er = 5 if "bigeyes" not in ex else 9
    if "bulge" in ex:
        for x in (56, 104):
            e((x - 14, 34, x + 14, 62), fill=body, outline=edge, width=K)
        eye_y = 48
    if "bigeyes" in ex:
        for x in (60, 100):
            e((x - 15, 46, x + 15, 76), fill=_hex("#fef3c7"), outline=dark, width=K)
    for x in (62, 98):
        e((x - er, eye_y - er - 2, x + er, eye_y + er + 3), fill=_hex("#111827"))
        e((x - er * 0.4 - 2, eye_y - er, x + er * 0.2, eye_y - er * 0.3), fill=(255, 255, 255, 255))
    # хацар
    for x in (50, 110):
        e((x - 9, 78, x + 9, 90), fill=(255, 140, 160, 120))

    # хамар, ам
    nose_c = _hex("#111827")
    if "darknose" in ex:
        e((68, 66, 92, 90), fill=_hex("#111827"))
    elif "rednose" in ex:
        e((70, 74, 90, 92), fill=_hex("#ef4444"))
    elif "snout" in ex:
        e((60, 76, 100, 100), fill=_hex("#f9a8d4"), outline=_hex("#ec4899"), width=K)
        e((68, 84, 74, 94), fill=_hex("#be185d"))
        e((86, 84, 92, 94), fill=_hex("#be185d"))
    elif "widesnout" in ex:
        e((60, 82, 68, 92), fill=_hex("#6d28d9", 160))
        e((92, 82, 100, 92), fill=_hex("#6d28d9", 160))
    elif ex & {"beak", "hookbeak"}:
        col = _hex("#f59e0b") if "hookbeak" not in ex else _hex("#ef4444")
        p([(68, 74), (92, 74), (80, 92)], fill=col, outline=_darker("#b45309", 1))
    elif "flatbeak" in ex:
        e((62, 76, 98, 94), fill=_hex("#fb923c"), outline=_hex("#c2410c"), width=K)
    elif "trunk" in ex:
        for i, w in enumerate((18, 16, 14, 12)):
            e((80 - w, 78 + i * 12, 80 + w, 100 + i * 12), fill=body, outline=edge, width=K)
    elif "bulge" not in ex and "shell" not in ex:
        e((72, 76, 88, 86), fill=nose_c)
        d.arc([v * K for v in (68, 82, 80, 94)], 0, 180, fill=nose_c, width=2 * K)
        d.arc([v * K for v in (80, 82, 92, 94)], 0, 180, fill=nose_c, width=2 * K)
    if "bulge" in ex or "shell" in ex:
        d.arc([v * K for v in (64, 80, 96, 100)], 10, 170, fill=nose_c, width=2 * K)
    if "tusks" in ex:
        for sx in (-1, 1):
            p([(80 + sx * 18, 96), (80 + sx * 30, 124), (80 + sx * 12, 102)], fill=_hex("#fffbeb"), outline=_hex("#d6d3d1"))
    if "beard" in ex:
        p([(72, 104), (88, 104), (80, 126)], fill=_hex("#f1f5f9"), outline=_hex("#cbd5e1"))
    if "tuft" in ex:
        for dx in (-6, 0, 6):
            d.line([((80 + dx) * K, 28 * K), ((80 + dx * 1.8) * K, 12 * K)], fill=body, width=4 * K)

    out = img.resize((size, size), Image.LANCZOS)
    return out


def key_is_lion(_hex_):  # noqa: D401 - тусгай шалгалт хэрэггүй, нийцтэй байлгахад үлдээв
    return False


PIX = 44  # pixel art-ийн логик хэмжээ


def render_pet(key: str, size: int = S, frame: int = 0) -> Image.Image:
    """16-bit pixel art хэв маяг: цөөн өнгө, 1px бараан контур, nearest-neighbor томруулалт."""
    from PIL import ImageChops, ImageFilter

    big = _render_smooth(key, 176)
    small = big.resize((PIX, PIX), Image.BOX)
    a = small.split()[3].point(lambda v: 255 if v > 110 else 0)
    rgb = Image.new("RGB", small.size, (0, 0, 0))
    rgb.paste(small.convert("RGB"), mask=a)
    rgb = rgb.quantize(colors=20, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    px = rgb.convert("RGBA")
    px.putalpha(a)
    grown = a.filter(ImageFilter.MaxFilter(3))
    ol = ImageChops.subtract(grown, a)
    outline = Image.new("RGBA", small.size, (28, 22, 36, 255))
    outline.putalpha(ol)
    outline.alpha_composite(px)
    if frame % 2:  # алхалтын 2-р фрэйм: 1px доош
        shifted = Image.new("RGBA", outline.size, (0, 0, 0, 0))
        shifted.alpha_composite(outline, (0, 1))
        outline = shifted
    return outline.resize((size, size), Image.NEAREST)
