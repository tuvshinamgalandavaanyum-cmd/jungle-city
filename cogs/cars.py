import math

import discord
from discord.ext import commands

from carart import render_car  # noqa: F401
from items import CAR_TIERS, CARS, find_items, get_item
from purchase import car_file, purchase
from ui import OwnerView, nav_button, safe_edit
from utils import fmt, reply

PER = 8


class CarView(OwnerView):
    def __init__(self, cog, ctx):
        super().__init__(ctx.author.id, timeout=240)
        self.cog, self.ctx = cog, ctx
        self.tier = 0
        self.page = 0
        self.selected = None

    def cars(self):
        lo = CAR_TIERS[self.tier][0]
        hi = CAR_TIERS[self.tier + 1][0] if self.tier + 1 < len(CAR_TIERS) else 100
        return [c for c in CARS if lo <= c.level < hi]

    async def build(self):
        for c in list(self.children):
            self.remove_item(c)
        tsel = discord.ui.Select(
            placeholder="Түвшин сонгоно уу",
            options=[discord.SelectOption(label=f"{n} (Lv {lo}+)", value=str(i), default=i == self.tier)
                     for i, (lo, n, _) in enumerate(CAR_TIERS)],
            row=0,
        )
        tsel.callback = self.on_tier(tsel)
        self.add_item(tsel)
        cars = self.cars()
        pages = max(1, math.ceil(len(cars) / PER))
        self.page = max(0, min(self.page, pages - 1))
        chunk = cars[self.page * PER:(self.page + 1) * PER]
        name = CAR_TIERS[self.tier][1]
        embed = discord.Embed(
            title=f"🚗 Машины цэс · {name}",
            description="\n".join(
                f"{c.emoji} **{c.name}** · Lv {c.level} · {fmt(c.price)} · +{round(c.bonus * 100, 1)}% · `{c.key}`"
                for c in chunk
            ) or "—",
            color=0x22D3EE,
        )
        if chunk:
            sel = discord.ui.Select(
                placeholder="Машин сонгоно уу",
                options=[discord.SelectOption(label=c.name[:100], value=c.key, emoji=c.emoji,
                                              description=f"Lv {c.level} · {fmt(c.price)}"[:100],
                                              default=self.selected is not None and self.selected.key == c.key)
                         for c in chunk],
                row=1,
            )
            sel.callback = self.on_car(sel)
            self.add_item(sel)
        prev = nav_button("◀", self.on_prev, disabled=self.page <= 0)
        pg = nav_button(f"{self.page + 1}/{pages}", self.on_noop, disabled=True)
        nxt = nav_button("▶", self.on_next, disabled=self.page >= pages - 1)
        buy = nav_button("🛒 Авах", self.on_buy, discord.ButtonStyle.success, disabled=self.selected is None)
        for b in (prev, pg, nxt, buy):
            self.add_item(b)
        embed.set_footer(text=f"{self.ctx.clean_prefix}buy <ID> · {self.ctx.clean_prefix}car <ID> — GIF үзэх")
        if self.selected is not None:
            embed.set_image(url="attachment://preview.png")
        return embed

    async def refresh(self, interaction):
        embed = await self.build()
        files = [await car_file(self.selected, False, "preview")] if self.selected is not None else []
        await safe_edit(interaction, embed=embed, view=self, attachments=files)

    def on_tier(self, sel):
        async def cb(interaction):
            self.tier, self.page, self.selected = int(sel.values[0]), 0, None
            await self.refresh(interaction)
        return cb

    def on_car(self, sel):
        async def cb(interaction):
            self.selected = get_item(sel.values[0])
            await self.refresh(interaction)
        return cb

    async def on_prev(self, interaction):
        self.page -= 1
        self.selected = None
        await self.refresh(interaction)

    async def on_next(self, interaction):
        self.page += 1
        self.selected = None
        await self.refresh(interaction)

    async def on_buy(self, interaction):
        await interaction.response.defer()
        err, embed, file = await purchase(self.cog.bot, self.owner_id, self.selected, 1)
        if err:
            await interaction.followup.send(err, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, file=file)

    async def on_noop(self, interaction):
        await interaction.response.defer()


class Cars(commands.Cog):
    """Машины цэс (Lv 1-99)."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(name="cars", aliases=["mashin", "garage", "машин"])
    async def cars(self, ctx):
        """Машины цэс: Beginner · Hard · Expert · Legend · Impossible"""
        view = CarView(self, ctx)
        view.message = await reply(ctx, embed=await view.build(), view=view)

    @commands.command(name="car")
    async def car(self, ctx, car_id: str):
        """Машины зураг, GIF харах: car <ID>"""
        m = [i for i in find_items(car_id) if i.kind == "car"]
        if not m:
            await reply(ctx, f"❌ Машин олдсонгүй. `{ctx.clean_prefix}cars`")
            return
        it = m[0]
        f = await car_file(it, True, "car")
        e = discord.Embed(title=f"{it.emoji} {it.name}", description=f"{it.desc}\n💰 {fmt(it.price)} · ажлын цалин +{round(it.bonus * 100, 1)}%", color=0x22D3EE)
        e.set_image(url=f"attachment://{f.filename}")
        await ctx.reply(embed=e, file=f, mention_author=False)


async def setup(bot):
    await bot.add_cog(Cars(bot))
