"""Барааны pixel art дүрс: assets/icons/<key>.png-г томруулж өгнө."""
import io
import os

from PIL import Image

ICON_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
_cache: dict = {}


def has_icon(key: str) -> bool:
    return os.path.exists(os.path.join(ICON_DIR, f"{key}.png"))


def icon_image(key: str, size: int = 128) -> Image.Image | None:
    p = os.path.join(ICON_DIR, f"{key}.png")
    if not os.path.exists(p):
        return None
    k = (key, size)
    if k not in _cache:
        _cache[k] = Image.open(p).convert("RGBA").resize((size, size), Image.NEAREST)
    return _cache[k].copy()


def icon_png(key: str, size: int = 128) -> bytes | None:
    im = icon_image(key, size)
    if im is None:
        return None
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def item_png(key: str, size: int = 128) -> bytes | None:
    """Нийцтэй нэр (icon_png-тэй адил)."""
    return icon_png(key, size)
