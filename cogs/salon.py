import asyncio
import io

import discord
from discord.ext import commands

from cogs.profile import SKIN_HEX
from sprite import (
    HAIR_COLORS, HAIR_HEX, HAIR_STYLES, MAKEUP_BLUSH, MAKEUP_EXTRAS, MAKEUP_EYES, MAKEUP_LIPS,
    dump_makeup, parse_makeup, render_preview,
)
from ui import OwnerView, nav_button, safe_edit
from utils import fmt, reply

HAIR_PRICE = 15_000
MAKEUP_PRICE = 10_000
STYLE_NAME = {k: n for k, n, _ in HAIR_STYLES}
COLOR_NAME = {k: n for k, n, _ in HAIR_COLORS}
LIP_NAME = {k: n for k, n, _ in MAKEUP_LIPS}
EYE_NAME = {k: n for k, n, _ in MAKEUP_EYES}
BLUSH_NAME = {k: n for k, n, _ in MAKEUP_BLUSH}
EXTRA_NAME = {k: n for k, n, _ in MAKEUP_EXTRAS}


class HairView(OwnerView):
    """Үсчин + Makeup: хоёр таб."""

    def __init__(self, cog, ctx, user, mode: str = "hair"):
        super().__init__(ctx.author.id, timeout=300)
        self.cog, self.ctx = cog, ctx
        self.gender = user["gender"]
        self.skin = SKIN_HEX.get(user["skin"], "#e8be98")
        self.style = user["hair_style"] or "default"
        self.color = user["hair_color"] or ""
        self.mk = parse_makeup(user["makeup"])
        self.old_hair = (self.style, self.color)
        self.old_mk = dump_makeup(self.mk)
        self.mode = mode
        self.msg = ""
        self._layout()

    # ---------- төлбөр ----------
    def cost(self) -> int:
        c = 0
        if (self.style, self.color) != self.old_hair:
            c += HAIR_PRICE
        if dump_makeup(self.mk) != self.old_mk:
            c += MAKEUP_PRICE
        return c

    # ---------- бүтэц ----------
    def _opts(self, rows, current, none_label):
        opts = [discord.SelectOption(label=none_label, value="none", emoji="🚫", default=not current)]
        opts += [discord.SelectOption(label=n, value=k, default=k == current) for k, n, *_ in rows]
        return opts

    def _layout(self):
        self.clear_items()
        self.add_item(nav_button("💇 Үс", self.on_tab_hair, discord.ButtonStyle.primary if self.mode == "hair" else discord.ButtonStyle.secondary, row=0))
        self.add_item(nav_button("💄 Makeup", self.on_tab_mk, discord.ButtonStyle.primary if self.mode == "mk" else discord.ButtonStyle.secondary, row=0))
        cost = self.cost()
        save = nav_button(f"✅ Хадгалах ({fmt(cost)})" if cost else "✅ Хадгалах", self.on_save, discord.ButtonStyle.success, disabled=cost == 0, row=0)
        self.add_item(save)
        self.add_item(nav_button("🧼 Makeup арилгах", self.on_clear_mk, row=0) if self.mode == "mk" else nav_button("❌ Хаах", self.on_close, row=0))
        if self.mode == "hair":
            sel = discord.ui.Select(
                placeholder="💇 Үсний хэв маяг сонгох...",
                options=[discord.SelectOption(label=n, value=k, emoji=e, default=k == self.style) for k, n, e in HAIR_STYLES],
                row=1,
            )
            sel.callback = self.on_style
            self.add_item(sel)
            opts = [discord.SelectOption(label="Анхны өнгө", value="default", emoji="🎨", default=not self.color)]
            opts += [discord.SelectOption(label=n, value=k, default=k == self.color) for k, n, _ in HAIR_COLORS]
            sel2 = discord.ui.Select(placeholder="🎨 Үсний өнгө сонгох...", options=opts, row=2)
            sel2.callback = self.on_color
            self.add_item(sel2)
        else:
            for row, (key, ph, rows, none_label) in enumerate((
                ("lips", "💋 Уруулын будаг...", MAKEUP_LIPS, "Уруулын будаггүй"),
                ("eyes", "👁️ Нүдний сүүдэр...", MAKEUP_EYES, "Нүдний сүүдэргүй"),
                ("blush", "🌸 Хацрын будаг...", MAKEUP_BLUSH, "Хацрын будаггүй"),
            ), start=1):
                sel = discord.ui.Select(placeholder=ph, options=self._opts(rows, self.mk.get(key), none_label), row=row)
                sel.callback = self._make_mk_cb(key, sel)
                self.add_item(sel)
            cur = self.mk.get("extra") or []
            sel = discord.ui.Select(
                placeholder="✨ Нэмэлт (олныг сонгож болно)...",
                min_values=0,
                max_values=len(MAKEUP_EXTRAS),
                options=[discord.SelectOption(label=n, value=k, emoji=e, default=k in cur) for k, n, e in MAKEUP_EXTRAS],
                row=4,
            )
            sel.callback = self._make_extra_cb(sel)
            self.add_item(sel)

    def _make_mk_cb(self, key, sel):
        async def cb(interaction):
            v = sel.values[0]
            if v == "none":
                self.mk.pop(key, None)
            else:
                self.mk[key] = v
            self.msg = ""
            await self.refresh(interaction)
        return cb

    def _make_extra_cb(self, sel):
        async def cb(interaction):
            if sel.values:
                self.mk["extra"] = list(sel.values)
            else:
                self.mk.pop("extra", None)
            self.msg = ""
            await self.refresh(interaction)
        return cb

    # ---------- зураг ----------
    def _png(self) -> bytes:
        outfit = {"hair": (self.style, HAIR_HEX.get(self.color)), "makeup": self.mk}
        return render_preview(self.gender, self.skin, outfit)

    def _mk_text(self) -> str:
        bits = []
        if self.mk.get("lips"):
            bits.append(f"💋 {LIP_NAME[self.mk['lips']]}")
        if self.mk.get("eyes"):
            bits.append(f"👁️ {EYE_NAME[self.mk['eyes']]}")
        if self.mk.get("blush"):
            bits.append(f"🌸 {BLUSH_NAME[self.mk['blush']]}")
        for x in self.mk.get("extra") or []:
            bits.append(EXTRA_NAME[x])
        return " · ".join(bits) if bits else "Будалтгүй"

    async def build(self):
        data = await asyncio.to_thread(self._png)
        f = discord.File(io.BytesIO(data), filename="hair.png")
        e = discord.Embed(title="💇 Үсчин & 💄 Makeup", color=0xEC4899)
        e.description = (
            f"💇 Хэв маяг: **{STYLE_NAME.get(self.style, '—')}** · Өнгө: **{COLOR_NAME.get(self.color, 'Анхны')}**\n"
            f"💄 Makeup: **{self._mk_text()}**\n\n"
            f"Үс **{fmt(HAIR_PRICE)}** · Makeup **{fmt(MAKEUP_PRICE)}** (өөрчилсөн зүйлийн үнийг л төлнө)"
        )
        if self.msg:
            e.add_field(name="ℹ️", value=self.msg, inline=False)
        e.set_image(url="attachment://hair.png")
        return e, f

    async def refresh(self, interaction):
        self._layout()
        e, f = await self.build()
        await safe_edit(interaction, embed=e, view=self, attachments=[f])

    # ---------- товчнууд ----------
    async def on_tab_hair(self, interaction):
        self.mode = "hair"
        await self.refresh(interaction)

    async def on_tab_mk(self, interaction):
        self.mode = "mk"
        await self.refresh(interaction)

    async def on_style(self, interaction):
        self.style = interaction.data["values"][0]
        self.msg = ""
        await self.refresh(interaction)

    async def on_color(self, interaction):
        v = interaction.data["values"][0]
        self.color = "" if v == "default" else v
        self.msg = ""
        await self.refresh(interaction)

    async def on_clear_mk(self, interaction):
        self.mk = {}
        self.msg = ""
        await self.refresh(interaction)

    async def on_save(self, interaction):
        price = self.cost()
        ok = await self.cog.bot.db.set_look(
            self.owner_id, self.style, self.color or None, dump_makeup(self.mk), price,
        )
        if ok:
            self.old_hair = (self.style, self.color)
            self.old_mk = dump_makeup(self.mk)
            self.msg = f"✅ Хадгаллаа! (**{fmt(price)}**) `{self.ctx.clean_prefix}profile` дээр харна уу."
        else:
            self.msg = f"❌ Хэтэвчинд {fmt(price)} хүрэлцэхгүй байна."
        await self.refresh(interaction)

    async def on_close(self, interaction):
        self.disable_all()
        self.stop()
        await interaction.response.edit_message(view=self)


class Salon(commands.Cog):
    """Үсчин ба Makeup: дүрийн үс, будалт."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(name="hair", aliases=["salon", "uschin", "us", "үс", "makeup", "mk", "budalt"])
    async def hair(self, ctx: commands.Context):
        """Үсчин ба Makeup: үс (16 хэв, 14 өнгө), уруул, нүд, хацар, нэмэлт будалт сонгох"""
        user = await self.bot.db.get_user(ctx.author.id)
        mode = "mk" if (ctx.invoked_with or "").lower() in ("makeup", "mk", "budalt") else "hair"
        view = HairView(self, ctx, user, mode)
        e, f = await view.build()
        view.message = await ctx.reply(embed=e, file=f, view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Salon(bot))
