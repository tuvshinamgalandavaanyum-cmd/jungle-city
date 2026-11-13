"""Барааны pixel art дүрс: assets/icons/<key>.png-г томруулж өгнө."""
import io
import os
import zipfile

from PIL import Image

ICON_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
PACK = os.path.join(os.path.dirname(__file__), "icons.pack")
_cache: dict = {}
_pack_names = None


def _names():
    global _pack_names
    if _pack_names is None:
        try:
            with zipfile.ZipFile(PACK) as z:
                _pack_names = set(z.namelist())
        except Exception:
            _pack_names = set()
    return _pack_names


def _open(key: str):
    """assets/icons/<key>.png эсвэл icons.pack доторх зургийг буцаана."""
    p = os.path.join(ICON_DIR, f"{key}.png")
    if os.path.exists(p):
        return Image.open(p)
    if f"{key}.png" in _names():
        with zipfile.ZipFile(PACK) as z:
            return Image.open(io.BytesIO(z.read(f"{key}.png")))
    return None


def has_icon(key: str) -> bool:
    return os.path.exists(os.path.join(ICON_DIR, f"{key}.png")) or f"{key}.png" in _names()


def icon_image(key: str, size: int = 128) -> Image.Image | None:
    k = (key, size)
    if k not in _cache:
        im = _open(key)
        if im is None:
            return None
        _cache[k] = im.convert("RGBA").resize((size, size), Image.NEAREST)
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
