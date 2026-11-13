import io
import logging
import time

import discord
from discord.ext import commands, tasks

from itemart import item_png
from items import get_item
from utils import TAX_RATE, fmt, fmt_duration, parse_amount, reply

log = logging.getLogger(__name__)
MIN_MIN, MAX_MIN = 5, 1440
MIN_START = 100


def _icon(key: str):
    data = item_png(key, 128)
    return discord.File(io.BytesIO(data), filename="icon.png") if data else None


class Auction(commands.Cog):
    """Дуудлага худалдаа: бараагаа дуудлагаар зарж, зарагдсан үнийг харах."""

    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @tasks.loop(seconds=20)
    async def loop(self):
        try:
            for a, tax in await self.bot.db.finish_due_auctions(TAX_RATE):
                await self.announce(a, tax)
        except Exception:
            log.exception("Дуудлага шалгахад алдаа")

    @loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    async def announce(self, a: dict, tax: int):
        it = get_item(a["item_key"])
        ch = self.bot.get_channel(a["channel_id"]) if a["channel_id"] else None
        if ch is None or it is None:
            return
        if a["status"] == "sold":
            e = discord.Embed(
                title=f"🔨 Дуудлага #{a['id']} дууслаа",
                description=f"{it.emoji} **{it.name}** — <@{a['bidder_id']}> **{fmt(a['final_price'])}**-өөр авлаа!\n"
                f"Худалдагч <@{a['seller_id']}> {fmt(a['final_price'] - tax)} авсан (татвар {fmt(tax)}).",
                color=0x22C55E,
            )
        else:
            e = discord.Embed(
                title=f"🔨 Дуудлага #{a['id']} зарагдсангүй",
                description=f"{it.emoji} **{it.name}** — үнэ санал болгосон хүн байсангүй. <@{a['seller_id']}>-д буцаалаа.",
                color=0x6B7280,
            )
        f = _icon(it.key)
        if f:
            e.set_thumbnail(url="attachment://icon.png")
        try:
            await ch.send(embed=e, file=f) if f else await ch.send(embed=e)
        except Exception:
            log.exception("Дуудлагын мэдэгдэл илгээж чадсангүй")

    def _line(self, a: dict) -> str:
        it = get_item(a["item_key"])
        cur = fmt(a["bid"]) if a["bidder_id"] else f"эхлэх {fmt(a['start_price'])}"
        left = fmt_duration(max(0, a["ends_at"] - time.time()))
        return f"`#{a['id']}` {it.emoji} **{it.name}** · {cur} · ⏳ {left} · <@{a['seller_id']}>"

    @commands.command(name="auction", aliases=["auc", "duudlaga", "дуудлага"])
    async def auction(self, ctx: commands.Context):
        """Идэвхтэй дуудлага худалдааны жагсаалт"""
        rows = await self.bot.db.open_auctions(20)
        p = ctx.clean_prefix
        e = discord.Embed(title="🔨 Дуудлага худалдаа", color=0xF59E0B)
        e.description = "\n".join(self._line(a) for a in rows) if rows else "Одоогоор идэвхтэй дуудлага алга."
        e.add_field(
            name="Хэрхэн ашиглах вэ",
            value=f"`{p}aucsell <ID> <эхлэх үнэ> [минут]` — бараагаа дуудлагад тавих\n"
            f"`{p}bid <дуудлагын №> <дүн>` — үнэ санал болгох\n"
            f"`{p}auchistory [ID]` — зарагдсан үнийн түүх\n`{p}purchases` — миний худалдан авалт",
            inline=False,
        )
        e.set_footer(text=f"Зарагдахад {int(TAX_RATE * 100)}% татвар · сүүлийн минутад үнэ нэмбэл +1 минут")
        await reply(ctx, embed=e)

    @commands.command(name="aucsell", aliases=["aucadd", "duudlagatavih"])
    async def aucsell(self, ctx: commands.Context, item_id: str, start_price: str, minutes: int = 60):
        """Бараагаа дуудлагад тавих: aucsell <ID> <эхлэх үнэ> [минут 5-1440]"""
        start_price = parse_amount(start_price, 0)
        if not start_price:
            await reply(ctx, "❌ Эхлэх үнийг зөв оруулна уу (жишээ: 50000, 50k).")
            return
        it = get_item(item_id.lower())
        if it is None:
            await reply(ctx, f"❌ Бараа олдсонгүй. `{ctx.clean_prefix}inv` дээрээс ID-аа харна уу.")
            return
        if not (MIN_MIN <= minutes <= MAX_MIN):
            await reply(ctx, f"❌ Хугацаа {MIN_MIN}-{MAX_MIN} минутын хооронд байна.")
            return
        if start_price < MIN_START or start_price > 10_000_000_000:
            await reply(ctx, f"❌ Эхлэх үнэ хамгийн багадаа {fmt(MIN_START)}.")
            return
        aid = await self.bot.db.create_auction(ctx.author.id, it.key, start_price, time.time() + minutes * 60, ctx.channel.id)
        if aid is None:
            await reply(ctx, "❌ Энэ бараа таны цүнхэнд алга (байшинд тавьсан бол эхлээд буцааж аваарай).")
            return
        e = discord.Embed(
            title=f"🔨 Дуудлага #{aid} эхэллээ",
            description=f"{it.emoji} **{it.name}**\nЭхлэх үнэ: **{fmt(start_price)}** · ⏳ {minutes} минут\n"
            f"`{ctx.clean_prefix}bid {aid} <дүн>`",
            color=0xF59E0B,
        )
        f = _icon(it.key)
        if f:
            e.set_thumbnail(url="attachment://icon.png")
            await ctx.reply(embed=e, file=f, mention_author=False)
        else:
            await reply(ctx, embed=e)

    @commands.command(name="bid")
    async def bid(self, ctx: commands.Context, auction_id: int, amount: str):
        """Дуудлагад үнэ санал болгох: bid <№> <дүн> (мөнгө хэтэвчнээс барьцаалагдана)"""
        amount = parse_amount(amount, 0)
        if not amount:
            await reply(ctx, "❌ Дүнг зөв оруулна уу (жишээ: 50000, 50k).")
            return
        ok, msg, prev = await self.bot.db.place_bid(auction_id, ctx.author.id, amount)
        if not ok:
            await reply(ctx, f"❌ {msg}")
            return
        a = await self.bot.db.get_auction(auction_id)
        it = get_item(a["item_key"])
        txt = f"✅ {it.emoji} **{it.name}** (#{auction_id}) — таны санал **{fmt(amount)}**. ⏳ {fmt_duration(a['ends_at'] - time.time())}"
        if prev:
            txt += f"\n<@{prev}> таны санал давагдлаа, мөнгөө буцаан авлаа."
        await reply(ctx, txt)

    @commands.command(name="auchistory", aliases=["aucdone", "duudlagatuuh"])
    async def auchistory(self, ctx: commands.Context, item_id: str = None):
        """Дуудлагаар зарагдсан үнэ: auchistory [ID]"""
        key = None
        if item_id:
            it = get_item(item_id.lower())
            if it is None:
                await reply(ctx, "❌ Бараа олдсонгүй.")
                return
            key = it.key
        rows = await self.bot.db.auction_history(key, 15)
        if not rows:
            await reply(ctx, "Зарагдсан дуудлага хараахан алга.")
            return
        lines = []
        for a in rows:
            it = get_item(a["item_key"])
            lines.append(f"`#{a['id']}` {it.emoji} **{it.name}** — **{fmt(a['final_price'])}** · <@{a['bidder_id']}> авсан")
        e = discord.Embed(title="🔨 Зарагдсан дуудлагууд" + (f" · {get_item(key).name}" if key else ""),
                          description="\n".join(lines), color=0x22C55E)
        if key:
            prices = [a["final_price"] for a in rows]
            e.set_footer(text=f"Дундаж {fmt(sum(prices) // len(prices))} · хамгийн өндөр {fmt(max(prices))}")
        await reply(ctx, embed=e)

    @commands.command(name="purchases", aliases=["buyhistory", "худалдан_авалт"])
    async def purchases(self, ctx: commands.Context):
        """Миний худалдан авалтын түүх: ямар бараа хэдэн ₮-өөр авсан"""
        rows = await self.bot.db.recent_purchases(ctx.author.id, 15)
        if not rows:
            await reply(ctx, "Танд худалдан авалтын түүх алга.")
            return
        src = {"shop": "🛍️ дэлгүүр", "auction": "🔨 дуудлага"}
        lines = []
        for r in rows:
            it = get_item(r["item_key"])
            if it is None:
                continue
            lines.append(f"{it.emoji} **{it.name}** ×{r['qty']} — **{fmt(r['price'] * r['qty'])}** · {src.get(r['source'], r['source'])} · <t:{int(r['ts'])}:R>")
        await reply(ctx, embed=discord.Embed(title="🧾 Худалдан авалтын түүх", description="\n".join(lines), color=0x3B82F6))


async def setup(bot):
    await bot.add_cog(Auction(bot))
