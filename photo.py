import asyncio
import io
import ipaddress
import logging
import socket

import aiohttp
import discord
from aiohttp.abc import AbstractResolver
from discord.ext import commands
from PIL import Image

import photostudio as ps
from cogs.profile import SKIN_HEX
from items import CARS, get_pet
from ui import OwnerView, nav_button, safe_edit
from utils import reply

log = logging.getLogger(__name__)
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 40_000_000
STEP = 20


class SafeResolver(AbstractResolver):
    """Дотоод/хувийн хаяг руу холбогдохоос сэргийлнэ (SSRF)."""

    async def resolve(self, host, port=0, family=socket.AF_INET):
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(host, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
        out = []
        for fam, _, _, _, addr in infos:
            ip = ipaddress.ip_address(addr[0])
            if ip.is_global:
                out.append({"hostname": host, "host": addr[0], "port": port, "family": fam, "proto": 0, "flags": 0})
        if not out:
            raise OSError("Зөвшөөрөөгүй хаяг")
        return out

    async def close(self):
        pass


async def fetch_image_url(url: str) -> Image.Image | None:
    if not url.lower().startswith("https://"):
        return None
    try:
        conn = aiohttp.TCPConnector(resolver=SafeResolver())
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as sess:
            async with sess.get(url, allow_redirects=True, max_redirects=3) as r:
                if r.status != 200 or not r.headers.get("Content-Type", "").lower().startswith("image/"):
                    return None
                if int(r.headers.get("Content-Length", "0") or 0) > MAX_BYTES:
                    return None
                data = await r.content.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return None
        return _open(data)
    except Exception:
        log.info("Зураг татаж чадсангүй", exc_info=True)
        return None


def _open(data: bytes) -> Image.Image | None:
    try:
        im = Image.open(io.BytesIO(data))
        if im.width * im.height > MAX_PIXELS:
            return None
        im.load()
        return im.convert("RGB")
    except Exception:
        return None


class PhotoView(OwnerView):
    def __init__(self, cog, ctx, assets, available, custom):
        super().__init__(ctx.author.id, timeout=600)
        self.cog, self.ctx = cog, ctx
        self.assets, self.custom = assets, custom
        self.state = ps.default_state(available)
        self.available = available
        self.bg_i = 0
        self.sel = available[0]
        self.n_bg = len(ps.PRESET_NAMES) + (1 if custom is not None else 0)
        sel = discord.ui.Select(
            placeholder="Аль давхаргыг хөдөлгөх вэ?",
            options=[discord.SelectOption(label=ps.LAYER_NAMES[k].split(" ", 1)[1], value=k, emoji=ps.LAYER_NAMES[k].split(" ")[0],
                                          default=k == self.sel) for k in available],
            row=0,
        )
        sel.callback = self.on_layer
        self.layer_select = sel
        self.add_item(sel)
        for label, cb in (("◀", self.left), ("▲", self.up), ("▼", self.down), ("▶", self.right), ("↔", self.flip)):
            self.add_item(nav_button(label, cb, row=1))
        for label, cb in (("➖", self.smaller), ("➕", self.bigger), ("👁", self.toggle), ("🖼", self.next_bg)):
            self.add_item(nav_button(label, cb, row=2))
        self.add_item(nav_button("📸 Дуусгах", self.done, discord.ButtonStyle.success, row=2))

    def render(self) -> bytes:
        bg = ps.make_background(self.bg_i, self.custom)
        return ps.compose(bg, self.state, self.assets)

    async def build(self):
        data = await asyncio.to_thread(self.render)
        f = discord.File(io.BytesIO(data), filename="photo.jpg")
        bg_name = "🖼 Өөрийн зураг" if (self.custom is not None and self.bg_i == 0) else ps.PRESET_NAMES[(self.bg_i - (1 if self.custom is not None else 0)) % len(ps.PRESET_NAMES)]
        e = discord.Embed(title="📸 Зургийн студи", description=f"Сонгосон: **{ps.LAYER_NAMES[self.sel]}** · Арын зураг: {bg_name}\n"
                          "◀ ▲ ▼ ▶ зөөх · ↔ эргүүлэх · ➖ ➕ хэмжээ · 👁 нуух/харуулах · 🖼 арын зураг солих", color=0xEC4899)
        e.set_image(url="attachment://photo.jpg")
        return e, f

    async def refresh(self, interaction):
        e, f = await self.build()
        await safe_edit(interaction, embed=e, view=self, attachments=[f])

    async def on_layer(self, interaction):
        self.sel = self.layer_select.values[0]
        for o in self.layer_select.options:
            o.default = o.value == self.sel
        await self.refresh(interaction)

    def _move(self, dx=0, dy=0):
        st = self.state[self.sel]
        st["x"] = max(0, min(ps.W, st["x"] + dx))
        st["y"] = max(60, min(ps.H + 40, st["y"] + dy))

    async def left(self, i): self._move(dx=-STEP); await self.refresh(i)
    async def right(self, i): self._move(dx=STEP); await self.refresh(i)
    async def up(self, i): self._move(dy=-STEP); await self.refresh(i)
    async def down(self, i): self._move(dy=STEP); await self.refresh(i)

    async def flip(self, i):
        self.state[self.sel]["flip"] = not self.state[self.sel]["flip"]
        await self.refresh(i)

    async def smaller(self, i):
        st = self.state[self.sel]
        st["scale"] = max(0.2, round(st["scale"] - 0.1, 2))
        await self.refresh(i)

    async def bigger(self, i):
        st = self.state[self.sel]
        st["scale"] = min(3.0, round(st["scale"] + 0.1, 2))
        await self.refresh(i)

    async def toggle(self, i):
        st = self.state[self.sel]
        st["visible"] = not st["visible"]
        await self.refresh(i)

    async def next_bg(self, i):
        self.bg_i = (self.bg_i + 1) % self.n_bg
        await self.refresh(i)

    async def done(self, interaction):
        await interaction.response.defer()
        data = await asyncio.to_thread(self.render)
        f = discord.File(io.BytesIO(data), filename="photo.jpg")
        e = discord.Embed(title=f"📸 {interaction.user.display_name}-ийн зураг", color=0xEC4899)
        e.set_image(url="attachment://photo.jpg")
        await interaction.followup.send(embed=e, file=f)
        self.disable_all()
        try:
            await interaction.edit_original_response(view=self)
        except Exception:
            pass
        self.stop()


class Photo(commands.Cog):
    """Зургийн студи."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def _look(self, uid: int):
        db = self.bot.db
        u = await db.get_user(uid)
        profile = self.bot.get_cog("Profile")
        outfit, _ = await profile.outfit_colors(uid)
        return u, dict(gender=u["gender"], skin=SKIN_HEX.get(u["skin"], "#e8be98"), outfit=outfit)

    @commands.command(name="photo", aliases=["zurag", "studio", "selfie"])
    async def photo(self, ctx: commands.Context, url: str = None):
        """Зураг авах: photo [арын зургийн https:// холбоос] — эсвэл зураг хавсаргаж бичнэ"""
        db = self.bot.db
        async with ctx.typing():
            custom = None
            att = next((a for a in ctx.message.attachments if (a.content_type or "").startswith("image/")), None)
            ref = ctx.message.reference.resolved if ctx.message.reference else None
            if att is None and isinstance(ref, discord.Message):
                att = next((a for a in ref.attachments if (a.content_type or "").startswith("image/")), None)
            if att is not None:
                if att.size > MAX_BYTES:
                    await reply(ctx, "❌ Зураг 8MB-аас бага байх ёстой.")
                    return
                custom = _open(await att.read())
            elif url:
                custom = await fetch_image_url(url.strip("<>"))
                if custom is None:
                    await reply(ctx, "❌ Зургийг татаж чадсангүй. https:// холбоос эсвэл зураг хавсарган оруулна уу.")
                    return
            u, me = await self._look(ctx.author.id)
            assets = {"me": await asyncio.to_thread(ps.layer_image, "me", me)}
            avail = ["me"]
            if u["spouse"]:
                pu, partner = await self._look(u["spouse"])
                if pu["registered"]:
                    assets["partner"] = await asyncio.to_thread(ps.layer_image, "partner", partner)
                    avail.append("partner")
            inv = {r["item_key"] for r in await db.get_inventory(ctx.author.id)}
            cars = sorted((c for c in CARS if c.key in inv), key=lambda c: -c.level)
            if cars:
                assets["car"] = await asyncio.to_thread(ps.layer_image, "car", dict(key=cars[0].key))
                avail.append("car")
            pet = get_pet(u["pet"])
            if pet:
                assets["pet"] = await asyncio.to_thread(ps.layer_image, "pet", dict(key=pet.key))
                avail.append("pet")
            if u["house"]:
                img = await asyncio.to_thread(ps.layer_image, "house", dict(key=u["house"]))
                if img is not None:
                    assets["house"] = img
                    avail.append("house")
            view = PhotoView(self, ctx, assets, avail, custom)
            e, f = await view.build()
        view.message = await ctx.reply(embed=e, file=f, view=view, mention_author=False)
        miss = [ps.LAYER_NAMES[k] for k in ("partner", "car", "pet", "house") if k not in avail]
        if miss:
            await ctx.send(f"ℹ️ Нэмэх боломжтой: {', '.join(miss)} (авбал зурагт орно).", delete_after=20)


async def setup(bot):
    await bot.add_cog(Photo(bot))
