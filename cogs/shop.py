import asyncio
import io
import math
from collections import defaultdict

from PIL import Image

import discord
from discord.ext import commands

from actions import activate_shield, eat_food, open_box, revive_player, use_potion, wear_item
from items import (
    CATEGORIES,
    CATEGORY_BY_KEY,
    PETS,
    find_items,
    get_item,
    get_pet,
    stars,
)
from carart import render_car  # noqa: F401
from petart import render_pet
from invview import InvView
from purchase import car_file, icon_file, purchase
from ui import OwnerView, nav_button, safe_edit
from usage import send_usage
from utils import fmt, hint_shop, hint_use, parse_qty, reply, shop_day

PER_PAGE = {"home": 10, "digital": 8, "house": 5, "car": 6, "food": 5,
            "top": 8, "bottom": 8, "shoes": 8, "hat": 8, "acc": 8}
DEFAULT_PER_PAGE = 6

CATEGORY_ALIASES = {
    "food": ["food", "хоол", "хүнс", "hunus", "hool"],
    "digital": ["digital", "dijital", "дижитал", "utas", "phone", "tech"],
    "home": ["home", "furniture", "гэр", "ахуй", "тавилга", "ger"],
    "house": ["house", "байшин", "baishin", "realty"],
    "car": ["car", "cars", "машин", "mashin"],
    "top": ["top", "tops", "tsamts", "цамц", "clothes", "cloth", "хувцас", "huvtsas", "brand"],
    "bottom": ["bottom", "pants", "umd", "өмд"],
    "shoes": ["shoes", "shoe", "gutal", "гутал"],
    "hat": ["hat", "hats", "malgai", "малгай"],
    "acc": ["acc", "accessory", "goyl", "гоёл", "chimeglel"],
    "box": ["box", "case", "chest", "хайрцаг", "кейс"],
    "jewel": ["jewel", "jewelry", "үнэт", "эдлэл", "gem"],
    "metal": ["metal", "металл", "ore"],
    "tool": ["tool", "tools", "хэрэгсэл", "shield"],
}


def find_category(query: str) -> str | None:
    q = query.strip().casefold()
    for key, aliases in CATEGORY_ALIASES.items():
        if q == key or q in aliases:
            return key
    for key, _, name, _ in CATEGORIES:
        if name.casefold().startswith(q):
            return key
    return None


async def resolve_item(ctx, query: str, pool=None):
    """ID эсвэл нэрээр бараа олно. Олдохгүй/олон байвал мэдэгдээд None."""
    matches = find_items(query, pool)
    if not matches:
        await reply(ctx, f"❌ `{query}` гэсэн бараа олдсонгүй. `{ctx.clean_prefix}shop` дээрх ID-г ашиглана уу.")
        return None
    if len(matches) > 1:
        names = ", ".join(f"`{m.key}`" for m in matches[:8])
        await reply(ctx, f"🔎 Олон бараа таарч байна: {names}. Яг ID-г бичнэ үү.")
        return None
    return matches[0]


class ShopView(OwnerView):
    def __init__(self, cog, ctx, category: str | None = None):
        super().__init__(ctx.author.id, timeout=240)
        self.cog, self.ctx = cog, ctx
        self.category = category
        self.page = 0
        self.pages = 1
        self.selected = None
        self.chunk = []
        self.select = discord.ui.Select(
            placeholder="Ангилал сонгоно уу...",
            options=[
                discord.SelectOption(label=name, value=key, emoji=emoji, description=f"{len(items)} бараа")
                for key, emoji, name, items in CATEGORIES
            ],
            row=0,
        )
        self.select.callback = self.on_select
        self.add_item(self.select)
        self.item_select = None
        self.prev_btn = nav_button("◀", self.on_prev, row=2)
        self.page_btn = nav_button("1/1", self.on_noop, disabled=True, row=2)
        self.next_btn = nav_button("▶", self.on_next, row=2)
        self.back_btn = nav_button("Буцах", self.on_back, discord.ButtonStyle.primary, row=2)
        self.buy_btn = nav_button("🛒 Авах", self.on_buy, discord.ButtonStyle.success, disabled=True, row=2)
        for b in (self.prev_btn, self.page_btn, self.next_btn, self.back_btn, self.buy_btn):
            self.add_item(b)

    def _sync(self):
        menu = self.category is None
        self.prev_btn.disabled = menu or self.page <= 0
        self.next_btn.disabled = menu or self.page >= self.pages - 1
        self.back_btn.disabled = menu
        self.page_btn.label = "—" if menu else f"{self.page + 1}/{self.pages}"
        self.buy_btn.disabled = self.selected is None
        if self.item_select is not None:
            self.remove_item(self.item_select)
            self.item_select = None
        if not menu and self.chunk:
            opts = []
            for it in self.chunk:
                if it.kind == "food":
                    d = f"{stars(it.stars)} · {it.feeds_days:g} хоног · {fmt(it.price)}"
                elif it.kind == "car":
                    d = f"Lv {it.level} · {fmt(it.price)}"
                else:
                    d = fmt(it.price)
                opts.append(
                    discord.SelectOption(
                        label=it.name[:100], value=it.key, emoji=it.emoji, description=d[:100],
                        default=(self.selected is not None and self.selected.key == it.key),
                    )
                )
            self.item_select = discord.ui.Select(placeholder="Бараа сонгоно уу...", options=opts, row=1)
            self.item_select.callback = self.on_item
            self.add_item(self.item_select)

    async def build(self) -> discord.Embed:
        p = self.ctx.clean_prefix
        if self.category is None:
            embed = discord.Embed(
                title="🛍️ Дэлгүүр",
                description=f"Доорх цэснээс ангилал сонгоно уу. Хоол: ⭐ 1-5 одтой.\n`{p}buy <ID>` эсвэл цэснээс сонгоод **🛒 Авах** дарна.",
                color=0xFFC933,
            )
            for key, emoji, name, items in CATEGORIES:
                embed.add_field(name=f"{emoji} {name}", value=f"{len(items)} бараа", inline=True)
            embed.set_footer(text=hint_shop(p))
            self.pages = 1
            self.chunk = []
            self.selected = None
            self._sync()
            return embed

        _, emoji, name, items = CATEGORY_BY_KEY[self.category]
        per = PER_PAGE.get(self.category, DEFAULT_PER_PAGE)
        self.pages = max(1, math.ceil(len(items) / per))
        self.page = max(0, min(self.page, self.pages - 1))
        self.chunk = items[self.page * per : (self.page + 1) * per]
        sold = await self.cog.bot.db.shop_sold(shop_day())

        lines = []
        for it in self.chunk:
            stock_txt = ""
            if it.stock is not None:
                left = max(0, it.stock - sold.get(it.key, 0))
                stock_txt = " **[ДУУССАН]**" if left == 0 else f" (Нөөц: {left}/{it.stock})"
            mark = "👉 " if self.selected is not None and self.selected.key == it.key else ""
            if self.category == "home":
                lines.append(f"{mark}{it.emoji} **{it.name}** — {fmt(it.price)}{stock_txt} · `{it.key}`")
            else:
                if it.kind == "food":
                    desc = f"{stars(it.stars)} · {it.feeds_days:g} хоногийн хоол"
                    if it.strength:
                        desc += f" · хүч +{it.strength}"
                else:
                    desc = it.desc
                lines.append(f"{mark}{it.emoji} **{it.name}** - {fmt(it.price)}{stock_txt}\n> {desc} · `{it.key}`")
        sep = "\n" if self.category == "home" else "\n"
        embed = discord.Embed(
            title=f"🛍️{emoji} {name}",
            description="Доорх жагсаалтаас бараагаа сонгоод **🛒 Авах** дарна.\n\n" + sep.join(lines),
            color=0xFFC933,
        )
        if self.selected is not None and self.selected.kind == "car":
            embed.set_image(url="attachment://preview.png")
        elif self.selected is not None:
            embed.set_thumbnail(url="attachment://icon.png")
        embed.set_footer(text=f"{hint_shop(p)} · Хуудас {self.page + 1}/{self.pages}")
        self._sync()
        return embed

    async def refresh(self, interaction):
        embed = await self.build()
        files = []
        if self.category and self.selected is not None and self.selected.kind == "car":
            files = [await car_file(self.selected, False, "preview")]
        elif self.category and self.selected is not None:
            f = icon_file(self.selected.key, "icon")
            files = [f] if f else []
        await safe_edit(interaction, embed=embed, view=self, attachments=files)

    async def on_select(self, interaction):
        self.category = self.select.values[0]
        self.page = 0
        self.selected = None
        await self.refresh(interaction)

    async def on_item(self, interaction):
        self.selected = get_item(self.item_select.values[0])
        await self.refresh(interaction)

    async def on_prev(self, interaction):
        self.page -= 1
        self.selected = None
        await self.refresh(interaction)

    async def on_next(self, interaction):
        self.page += 1
        self.selected = None
        await self.refresh(interaction)

    async def on_back(self, interaction):
        self.category = None
        self.page = 0
        self.selected = None
        await self.refresh(interaction)

    async def on_buy(self, interaction):
        if self.selected is None:
            await interaction.response.defer()
            return
        await interaction.response.defer()
        err, embed, file = await purchase(self.cog.bot, self.owner_id, self.selected, 1)
        if err:
            await interaction.followup.send(err, ephemeral=True)
            return
        if file is not None:
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)

    async def on_noop(self, interaction):
        await interaction.response.defer()


class PetView(OwnerView):
    def __init__(self, cog, ctx):
        super().__init__(ctx.author.id, timeout=240)
        self.cog, self.ctx = cog, ctx
        self.pets = sorted(PETS, key=lambda p: p.price)
        self.i = 0
        self.btns = [
            nav_button("⏪", self.on_first),
            nav_button("◀", self.on_prev),
            nav_button("1/1", self.on_noop, disabled=True),
            nav_button("▶", self.on_next),
            nav_button("⏩", self.on_last),
        ]
        for b in self.btns:
            self.add_item(b)
        self.buy_btn = nav_button("🛒 Авах", self.on_buy, discord.ButtonStyle.success)
        self.add_item(self.buy_btn)

    async def build(self):
        pet = self.pets[self.i]
        data = await asyncio.to_thread(lambda: _pet_png(pet.key))
        file = discord.File(io.BytesIO(data), filename="pet.png")
        embed = discord.Embed(
            title=f"🐾 {pet.emoji} {pet.name}",
            description=f"**{fmt(pet.price)}**\n✨ {pet.perk}\n`{self.ctx.clean_prefix}buypet {pet.key}`",
            color=0xF97316,
        )
        embed.set_image(url="attachment://pet.png")
        embed.set_footer(text=f"Амьтан {self.i + 1}/{len(self.pets)} · профайл дээр дүртэйгээ хамт алхана")
        self.btns[2].label = f"{self.i + 1}/{len(self.pets)}"
        self.btns[0].disabled = self.btns[1].disabled = self.i == 0
        self.btns[3].disabled = self.btns[4].disabled = self.i >= len(self.pets) - 1
        return embed, file

    async def refresh(self, interaction):
        embed, file = await self.build()
        await safe_edit(interaction, embed=embed, view=self, attachments=[file])

    async def on_first(self, interaction):
        self.i = 0
        await self.refresh(interaction)

    async def on_prev(self, interaction):
        self.i = max(0, self.i - 1)
        await self.refresh(interaction)

    async def on_next(self, interaction):
        self.i = min(len(self.pets) - 1, self.i + 1)
        await self.refresh(interaction)

    async def on_last(self, interaction):
        self.i = len(self.pets) - 1
        await self.refresh(interaction)

    async def on_buy(self, interaction):
        await interaction.response.defer()
        msg = await self.cog.buy_pet_for(self.owner_id, self.pets[self.i])
        await interaction.followup.send(msg)

    async def on_noop(self, interaction):
        await interaction.response.defer()


def _pet_png(key: str) -> bytes:
    buf = io.BytesIO()
    bg = Image.new("RGBA", (200, 200), (36, 40, 68, 255))
    bg.alpha_composite(render_pet(key, 180), (10, 10))
    bg.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


class Shop(commands.Cog):
    """Дэлгүүр, цүнх, хоол, амьтны дэлгүүр."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild is not None

    async def _inventory(self, user_id: int) -> dict[str, int]:
        rows = await self.bot.db.get_inventory(user_id)
        return {r["item_key"]: r["qty"] for r in rows}

    # ---------- дэлгүүр ----------
    @commands.command(name="shop")
    async def shop(self, ctx: commands.Context, category: str = None):
        """Дэлгүүр: shop [food | digital | home | house | car | top | bottom | shoes | hat | acc | jewel | metal | box | tool]"""
        cat = None
        if category is not None:
            cat = find_category(category)
            if cat is None:
                await send_usage(ctx)
                return
        view = ShopView(self, ctx, cat)
        embed = await view.build()
        view.message = await reply(ctx, embed=embed, view=view)

    @commands.command(name="buy", aliases=["purchase"])
    async def buy(self, ctx: commands.Context, item_id: str, qty: str = "1"):
        """Бараа худалдаж авах: buy <ID> [тоо]"""
        n = parse_qty(qty, 1, 100)
        if n is None:
            await reply(ctx, "❌ Тоо 1-ээс 100 хооронд байх ёстой.")
            return
        item = await resolve_item(ctx, item_id)
        if item is None:
            return

        if item.kind == "realty":
            house_cog = self.bot.get_cog("House")
            await house_cog._buy(ctx, item.key)
            return
        err, embed, file = await purchase(self.bot, ctx.author.id, item, n)
        if err:
            await reply(ctx, err)
            return
        embed.set_footer(text=hint_use(ctx.clean_prefix))
        if file is not None:
            await ctx.reply(embed=embed, file=file, mention_author=False)
        else:
            await reply(ctx, embed=embed)

    # ---------- цүнх ----------
    @commands.command(name="inv", aliases=["inventory", "bag"])
    async def inventory(self, ctx: commands.Context, action: str = None, item_id: str = None, qty: str = None):
        """Цүнх (🏠 Гэр · 🎒 Халаас · 🚗 Машин): inv [home|pocket|car] | inv use <ID> [тоо]"""
        p = ctx.clean_prefix
        inv = await self._inventory(ctx.author.id)

        if action is not None and action.lower() in ("use", "ашиглах"):
            if item_id is None:
                await send_usage(ctx)
                return
            n = parse_qty(qty, 1, 100)
            if n is None:
                await reply(ctx, "❌ Тоо 1-ээс 100 хооронд байх ёстой.")
                return
            pool = [it for it in (get_item(k) for k in inv) if it]
            item = await resolve_item(ctx, item_id, pool)
            if item is None:
                return
            if item.kind == "food":
                await eat_food(self.bot, ctx, item, n)
            elif item.key == "shield":
                await activate_shield(self.bot, ctx)
            elif item.key in ("luck_potion", "money_potion"):
                await use_potion(self.bot, ctx, item)
            elif item.key == "revive":
                await revive_player(self.bot, ctx, ctx.author)
            elif item.kind == "box":
                await open_box(self.bot, ctx, item, n)
            elif item.kind == "clothes":
                await wear_item(self.bot, ctx, item)
            else:
                await reply(
                    ctx,
                    f"ℹ️ **{item.name}**-г шууд ашиглах боломжгүй. "
                    f"Байшинд байрлуулах: `{p}house bedroom use {item.key}` · зарах: `{p}sell {item.key}`",
                )
            return
        if action is not None and action.lower() in ("home", "ger", "гэр", "pocket", "halaas", "халаас", "car", "mashin", "машин"):
            tab = {"home": "home", "ger": "home", "гэр": "home", "car": "car", "mashin": "car", "машин": "car"}.get(action.lower(), "pocket")
        elif action is not None:
            await send_usage(ctx)
            return
        else:
            tab = "home"
        view = InvView(self, ctx, tab)
        embed = await view.build()
        view.message = await reply(ctx, embed=embed, view=view)

    @commands.command(name="sell")
    async def sell(self, ctx: commands.Context, item_id: str, qty: str = None):
        """Цүнхний барааг зарах: sell <ID | all> [тоо]"""
        inv = await self._inventory(ctx.author.id)

        if item_id.lower() in ("all", "бүгд"):
            earned = 0
            count = 0
            for key, have in inv.items():
                it = get_item(key)
                if it and it.kind in ("house", "digital", "jewel", "metal") and await self.bot.db.remove_item(
                    ctx.author.id, key, have
                ):
                    earned += it.sell_price * have
                    count += have
            if earned == 0:
                await reply(ctx, "❌ Зарах гэр ахуй, дижитал, үнэт эдлэл, металл алга.")
                return
            await self.bot.db.add_balance(ctx.author.id, earned)
            await reply(ctx, f"💰 Нийт **{count}** бараа зарж **{fmt(earned)}** авлаа.")
            return

        pool = [it for it in (get_item(k) for k in inv) if it]
        item = await resolve_item(ctx, item_id, pool)
        if item is None:
            return
        have = inv[item.key]
        n = have if qty is not None and qty.lower() in ("all", "бүгд") else parse_qty(qty, 1, 100000)
        if n is None or n > have:
            await reply(ctx, f"❌ Тоо буруу. Танд {have} ширхэг байна.")
            return
        if not await self.bot.db.remove_item(ctx.author.id, item.key, n):
            await reply(ctx, "❌ Танд хангалттай бараа алга.")
            return
        earned = item.sell_price * n
        await self.bot.db.add_balance(ctx.author.id, earned)
        await reply(ctx, f"💰 **{item.name} × {n}** зарж **{fmt(earned)}** авлаа.")

    @commands.command(name="gift")
    async def gift(self, ctx: commands.Context, item_id: str, member: discord.Member, qty: str = "1"):
        """Бусдад бэлэглэх: gift <ID> @хүн [тоо]"""
        if member.id == ctx.author.id or member.bot:
            await reply(ctx, "❌ Энэ хүнд бэлэглэх боломжгүй.")
            return
        n = parse_qty(qty, 1, 100000)
        if n is None:
            await reply(ctx, "❌ Тоо буруу байна.")
            return
        inv = await self._inventory(ctx.author.id)
        pool = [it for it in (get_item(k) for k in inv) if it]
        item = await resolve_item(ctx, item_id, pool)
        if item is None:
            return
        if not await self.bot.db.remove_item(ctx.author.id, item.key, n):
            await reply(ctx, "❌ Танд хангалттай бараа алга.")
            return
        await self.bot.db.add_item(member.id, item.key, n)
        await reply(
            ctx,
            f"🎁 {ctx.author.mention} → {member.mention}: **{item.name} × {n}** бэлэглэлээ.",
        )

    # ---------- хоол ----------
    @commands.command(name="eat")
    async def eat(self, ctx: commands.Context, item_id: str, qty: str = "1"):
        """Хоол идэх: eat <ID> [тоо]"""
        n = parse_qty(qty, 1, 100)
        if n is None:
            await reply(ctx, "❌ Тоо 1-ээс 100 хооронд байх ёстой.")
            return
        inv = await self._inventory(ctx.author.id)
        pool = [it for it in (get_item(k) for k in inv) if it and it.kind == "food"]
        if not pool:
            await reply(ctx, f"❌ Танд хоол алга. `{ctx.clean_prefix}shop food` дээрээс аваарай.")
            return
        item = await resolve_item(ctx, item_id, pool)
        if item is None:
            return
        await eat_food(self.bot, ctx, item, n)

    # ---------- амьтны дэлгүүр ----------
    @commands.command(name="petshop", aliases=["pets", "zoo"])
    async def pet_shop(self, ctx: commands.Context):
        """Тэжээвэр амьтны дэлгүүр (зураг, ◀ ▶, 🛒 Авах)"""
        view = PetView(self, ctx)
        embed, file = await view.build()
        view.message = await ctx.reply(embed=embed, file=file, view=view, mention_author=False)

    async def buy_pet_for(self, user_id: int, pet) -> str:
        user = await self.bot.db.get_user(user_id)
        if user["pet"]:
            current = get_pet(user["pet"])
            return f"❌ Танд аль хэдийн {current.emoji} **{current.name}** байна."
        if not await self.bot.db.spend(user_id, pet.price):
            return f"❌ Мөнгө хүрэлцэхгүй байна. **{fmt(pet.price)}** хэрэгтэй."
        await self.bot.db.set_pet(user_id, pet.key)
        return f"{pet.emoji} **{pet.name}** авлаа! Онцлог: {pet.perk}\n🐾 Профайл дээр таны дүртэй хамт харагдана."

    @commands.command(name="buypet")
    async def buy_pet(self, ctx: commands.Context, pet_name: str):
        """Амьтан худалдаж авах: buypet <ID>  (жагсаалт: petshop)"""
        q = pet_name.lower()
        pet = get_pet(q) or next((p for p in PETS if p.name.lower().startswith(q) or p.key.startswith(q)), None)
        if pet is None:
            await reply(ctx, f"❌ Ийм амьтан алга. `{ctx.clean_prefix}petshop` командаар харна уу.")
            return
        await reply(ctx, await self.buy_pet_for(ctx.author.id, pet))


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
