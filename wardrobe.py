import discord
from discord.ext import commands

from actions import eat_food, wear_item
from invview import placed
from items import CLOTHES_BY_SLOT, SLOT_EMOJI, SLOT_NAMES, get_item, stars
from ui import OwnerView, nav_button
from utils import reply


class WardrobeView(OwnerView):
    def __init__(self, cog, ctx):
        super().__init__(ctx.author.id, timeout=240)
        self.cog, self.ctx = cog, ctx
        self.slot = "top"
        self.msg = ""

    async def build(self):
        db = self.cog.bot.db
        for c in list(self.children):
            self.remove_item(c)
        inv = {r["item_key"]: r["qty"] for r in await db.get_inventory(self.owner_id)}
        eq = await db.get_equipped(self.owner_id)
        slot_sel = discord.ui.Select(
            placeholder="Ангилал сонгоно уу",
            options=[discord.SelectOption(label=n, value=k, emoji=SLOT_EMOJI.get(k), default=k == self.slot)
                     for k, n in SLOT_NAMES.items()],
            row=0,
        )
        slot_sel.callback = self.on_slot(slot_sel)
        self.add_item(slot_sel)
        owned = [i for i in CLOTHES_BY_SLOT[self.slot] if inv.get(i.key, 0) > 0]
        embed = discord.Embed(title=f"🚪 Хувцасны шкаф · {SLOT_NAMES[self.slot]}", color=0xEC4899)
        cur = get_item(eq.get(self.slot, "")) if eq.get(self.slot) else None
        embed.description = f"Одоо өмссөн: {cur.emoji + ' ' + cur.name if cur else '—'}\n\n" + (
            "\n".join(f"{i.emoji} **{i.name}** · `{i.key}`" for i in owned[:20]) if owned
            else f"Энэ ангилалд хувцас алга. `shop {self.slot}`"
        )
        if owned:
            sel = discord.ui.Select(
                placeholder="Өмсөх хувцасаа сонгоно уу",
                options=[discord.SelectOption(label=i.name[:100], value=i.key, emoji=i.emoji) for i in owned[:25]],
                row=1,
            )
            sel.callback = self.on_wear(sel)
            self.add_item(sel)
        off = nav_button(f"👕 {SLOT_NAMES[self.slot]} тайлах", self.on_off, disabled=cur is None)
        self.add_item(off)
        if self.msg:
            embed.add_field(name="ℹ️", value=self.msg, inline=False)
        embed.set_footer(text=f"{self.ctx.clean_prefix}profile — дүрээ харах")
        return embed

    def on_slot(self, sel):
        async def cb(interaction):
            self.slot = sel.values[0]
            self.msg = ""
            await interaction.response.edit_message(embed=await self.build(), view=self)
        return cb

    def on_wear(self, sel):
        async def cb(interaction):
            it = get_item(sel.values[0])
            await self.cog.bot.db.equip(self.owner_id, it.slot, it.key)
            self.msg = f"✅ {it.emoji} **{it.name}** өмслөө."
            await interaction.response.edit_message(embed=await self.build(), view=self)
        return cb

    async def on_off(self, interaction):
        await self.cog.bot.db.unequip(self.owner_id, self.slot)
        self.msg = "✅ Тайллаа."
        await interaction.response.edit_message(embed=await self.build(), view=self)


class FridgeView(OwnerView):
    def __init__(self, cog, ctx):
        super().__init__(ctx.author.id, timeout=240)
        self.cog, self.ctx = cog, ctx

    async def build(self):
        for c in list(self.children):
            self.remove_item(c)
        inv = {r["item_key"]: r["qty"] for r in await self.cog.bot.db.get_inventory(self.owner_id)}
        foods = [(get_item(k), q) for k, q in inv.items() if get_item(k) and get_item(k).kind == "food"]
        foods.sort(key=lambda t: -t[0].stars)
        embed = discord.Embed(title="🧊 Хөргөгч", color=0x38BDF8)
        if not foods:
            embed.description = f"Хөргөгч хоосон. `{self.ctx.clean_prefix}shop food` дээрээс хоол аваарай."
            return embed
        embed.description = "\n".join(f"{i.emoji} **{i.name}** ×{q} · {stars(i.stars)} · {i.feeds_days:g} хоног" for i, q in foods[:25])
        sel = discord.ui.Select(
            placeholder="Идэх хоолоо сонгоно уу",
            options=[discord.SelectOption(label=i.name[:100], value=i.key, emoji=i.emoji,
                                          description=f"×{q} · {stars(i.stars)} · {i.feeds_days:g} хоног"[:100])
                     for i, q in foods[:25]],
        )
        sel.callback = self.on_eat(sel)
        self.add_item(sel)
        return embed

    def on_eat(self, sel):
        async def cb(interaction):
            await interaction.response.defer()
            await eat_food(self.cog.bot, self.ctx, get_item(sel.values[0]), 1)
            try:
                await interaction.message.edit(embed=await self.build(), view=self)
            except Exception:
                pass
        return cb


class Wardrobe(commands.Cog):
    """Хувцасны шкаф, хөргөгч (гэртээ байрлуулсан байх ёстой)."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def _need(self, ctx, key, name, cmd_item):
        if await placed(self.bot.db, ctx.author.id, key):
            return True
        await reply(
            ctx,
            f"❌ {name} гэртээ байрлаагүй байна.\n`{ctx.clean_prefix}buy {cmd_item}` → "
            f"`{ctx.clean_prefix}inv` (🏠 Гэр хэсэгт өрөөнд тавина)",
        )
        return False

    @commands.command(name="wardrobe", aliases=["shkaf", "shkav", "closet", "шкаф"])
    async def wardrobe(self, ctx):
        """Хувцасны шкаф: хувцас харах, өмсөх (шкафыг гэртээ байрлуулсан байх ёстой)"""
        if not await self._need(ctx, "wardrobe", "Хувцасны шкаф", "wardrobe"):
            return
        view = WardrobeView(self, ctx)
        view.message = await reply(ctx, embed=await view.build(), view=view)

    @commands.command(name="fridge", aliases=["hurguuch", "hurguhch", "хөргөгч"])
    async def fridge(self, ctx):
        """Хөргөгч: хоолоо харж идэх (хөргөгчийг гэртээ байрлуулсан байх ёстой)"""
        if not await self._need(ctx, "fridge", "Хөргөгч", "fridge"):
            return
        view = FridgeView(self, ctx)
        view.message = await reply(ctx, embed=await view.build(), view=view)


async def setup(bot):
    await bot.add_cog(Wardrobe(bot))
