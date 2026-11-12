"""Барааны pixel art дүрсийг (assets/icons/<key>.png) урьдчилан үүсгэнэ.
Noto Color Emoji фонтыг pixel болгон хувиргана. Ботыг ажиллуулахад энэ скрипт хэрэггүй,
зөвхөн бэлэн PNG-үүдийг уншина.  Ажиллуулах: python3 tools/make_icons.py"""
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import items  # noqa: E402

FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
N = 32  # логик pixel хэмжээ

from itememoji import EMO  # noqa: E402

STYLE_EMO = {
    "beanie": "🧢", "bucket": "👒", "cap": "🧢", "fedora": "🎩", "mongolhat": "🪖", "tophat": "🎩",
    "coat": "🧥", "deel": "🥋", "dress": "👗", "hoodie": "🧥", "jacket": "🧥", "suit": "🤵", "sweater": "🧶", "tee": "👕",
    "jeans": "👖", "pants": "👖", "shorts": "🩳", "skirt": "👗",
    "boot": "🥾", "mongolboot": "🥾", "sandal": "🩴", "sneaker": "👟",
    "bag": "👜", "belt": "➰", "glasses": "🕶️", "necklace": "📿", "scarf": "🧣", "watch": "⌚",
}
DRESS_SHOE = "👞"


def render_emoji(ch: str) -> Image.Image:
    font = ImageFont.truetype(FONT, 109)
    im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=font, embedded_color=True)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    side = max(im.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    return sq


def pixelate(im: Image.Image, tint: str | None = None) -> Image.Image:
    inner = N - 4
    small = im.resize((inner, inner), Image.BOX)
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    canvas.alpha_composite(small, (2, 2))
    a = canvas.split()[3].point(lambda v: 255 if v > 90 else 0)
    rgb = Image.new("RGB", canvas.size, (0, 0, 0))
    if tint:
        g = canvas.convert("L")
        c = tuple(int(tint.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        lo = tuple(int(v * 0.35) for v in c)
        hi = tuple(min(255, int(v * 1.25) + 25) for v in c)
        g = g.point(lambda v: int(255 * min(1, max(0, (v - 40) / 190))))
        rgb = Image.merge("RGB", [g.point(lambda v, k=k: int(lo[k] + (hi[k] - lo[k]) * v / 255)) for k in range(3)])
    else:
        rgb.paste(canvas.convert("RGB"), mask=a)
    rgb = rgb.quantize(colors=14, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    out = rgb.convert("RGBA")
    out.putalpha(a)
    ol = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)), a)
    edge = Image.new("RGBA", canvas.size, (24, 18, 32, 255))
    edge.putalpha(ol)
    edge.alpha_composite(out)
    return edge


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for it in items.ALL_ITEMS:
        if it.kind == "car":
            continue
        tint = None
        if it.kind == "clothes":
            ch = STYLE_EMO.get(it.style, "👕")
            if it.slot == "shoes" and it.style == "dress":
                ch = DRESS_SHOE
            tint = it.color if isinstance(it.color, str) and it.color.startswith("#") else None
        else:
            ch = EMO.get(it.key) or it.emoji
        pixelate(render_emoji(ch), tint).save(os.path.join(OUT, f"{it.key}.png"))
        n += 1
    print("icons:", n)


if __name__ == "__main__":
    main()
