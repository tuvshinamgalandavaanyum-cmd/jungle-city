import asyncio
import io

import discord
from discord.ext import commands

from cogs.profile import SKIN_HEX
from sprite import HAIR_COLORS, HAIR_HEX, HAIR_STYLES, render_preview
from ui import OwnerView, nav_button, safe_edit
from utils import fmt, reply

HAIR_PRICE = 15_000
STYLE_NAME = {k: n for k, n, _ in HAIR_STYLES}
COLOR_NAME = {k: n for k, n, _ in HAIR_COLORS}


class HairView(OwnerView):
    def __init__(self, cog, ctx, user):
        super().__init__(ctx.author.id, timeout=300)
        self.cog, self.ctx = cog, ctx
        self.gender = user["gender"]
        self.skin = SKIN_HEX.get(user["skin"], "#e8be98")
        self.style = user["hair_style"] or "default"
        self.color = user["hair_color"] or ""
        self.old = (self.style, self.color)
        self.style_sel = discord.ui.Select(
            placeholder="💇 Үсний хэв маяг сонгох...",
            options=[discord.SelectOption(label=n, value=k, emoji=e, default=k == self.style) for k, n, e in HAIR_STYLES],
            row=0,
        )
        self.style_sel.callback = self.on_style
        self.add_item(self.style_sel)
        opts = [discord.SelectOption(label="Анхны өнгө", value="default", emoji="🎨", default=not self.color)]
        opts += [discord.SelectOption(label=n, value=k, default=k == self.color) for k, n, _ in HAIR_COLORS]
        self.color_sel = discord.ui.Select(placeholder="🎨 Үсний өнгө сонгох...", options=opts, row=1)
        self.color_sel.callback = self.on_color
        self.add_item(self.color_sel)
        self.save_btn = nav_button(f"✅ Хадгалах ({fmt(HAIR_PRICE)})", self.on_save, discord.ButtonStyle.success, row=2)
        self.add_item(self.save_btn)
        self.add_item(nav_button("❌ Хаах", self.on_close, row=2))
        self.msg = ""

    def _png(self) -> bytes:
        outfit = {"hair": (self.style, HAIR_HEX.get(self.color))}
        return render_preview(self.gender, self.skin, outfit)

    async def build(self):
        data = await asyncio.to_thread(self._png)
        f = discord.File(io.BytesIO(data), filename="hair.png")
        e = discord.Embed(title="💇 Үсчин", color=0xEC4899)
        e.description = (
            f"Хэв маяг: **{STYLE_NAME.get(self.style, '—')}** · Өнгө: **{COLOR_NAME.get(self.color, 'Анхны')}**\n"
            f"Үс засуулах: **{fmt(HAIR_PRICE)}** (хэтэвчнээс)"
        )
        if self.msg:
            e.add_field(name="ℹ️", value=self.msg, inline=False)
        e.set_image(url="attachment://hair.png")
        self.save_btn.disabled = (self.style, self.color) == self.old
        return e, f

    async def refresh(self, interaction):
        e, f = await self.build()
        await safe_edit(interaction, embed=e, view=self, attachments=[f])

    async def on_style(self, interaction):
        self.style = self.style_sel.values[0]
        self.msg = ""
        for o in self.style_sel.options:
            o.default = o.value == self.style
        await self.refresh(interaction)

    async def on_color(self, interaction):
        self.color = self.color_sel.values[0]
        self.color = "" if self.color == "default" else self.color
        self.msg = ""
        for o in self.color_sel.options:
            o.default = o.value == self.color
        await self.refresh(interaction)

    async def on_save(self, interaction):
        ok = await self.cog.bot.db.set_hair(self.owner_id, self.style, self.color or None, HAIR_PRICE)
        if ok:
            self.old = (self.style, self.color)
            self.msg = f"✅ Үс засууллаа! `{self.ctx.clean_prefix}profile` дээр харна уу."
        else:
            self.msg = f"❌ Хэтэвчинд {fmt(HAIR_PRICE)} хүрэлцэхгүй байна."
        await self.refresh(interaction)

    async def on_close(self, interaction):
        self.disable_all()
        self.stop()
        await interaction.response.edit_message(view=self)


class Salon(commands.Cog):
    """Үсчин: дүрийн үс засах."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(name="hair", aliases=["salon", "uschin", "us", "үс"])
    async def hair(self, ctx: commands.Context):
        """Үсчин: үсний хэв маяг (16), өнгө (14) сонгож засуулах (15,000₮)"""
        user = await self.bot.db.get_user(ctx.author.id)
        view = HairView(self, ctx, user)
        e, f = await view.build()
        view.message = await ctx.reply(embed=e, file=f, view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Salon(bot))
