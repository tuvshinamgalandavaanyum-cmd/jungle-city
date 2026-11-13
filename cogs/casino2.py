"""Казиногийн нэмэлт тоглоомууд: рулет, blackjack, crash, морин уралдаан (банкны данснаас, дээд 500,000₮)."""
import asyncio
import logging
import random

import discord
from discord.ext import commands

from cogs.casino import GOLD, GREEN, GREY, RED, result_embed
from ui import OwnerView, nav_button
from usage import send_usage
from utils import MAX_BET, MIN_BET, fmt, reply

log = logging.getLogger(__name__)


async def take_bet(ctx, amount):
    casino = ctx.bot.get_cog("Casino")
    return await casino._take_bet(ctx, amount)


async def bank_of(bot, uid):
    return (await bot.db.get_user(uid))["bank"]


# ================= рулет =================
RED_NUMS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


def roulette_color(n: int) -> str:
    return "🟢" if n == 0 else ("🔴" if n in RED_NUMS else "⚫")


def parse_roulette(text: str):
    """-> (түлхүүр, тайлбар, үржвэр, шалгах функц) | None"""
    t = text.strip().lower()
    simple = [
        (("red", "r", "ulaan", "улаан"), "🔴 Улаан", 2, lambda n: n in RED_NUMS),
        (("black", "b", "har", "хар"), "⚫ Хар", 2, lambda n: n != 0 and n not in RED_NUMS),
        (("even", "tegsh", "тэгш"), "Тэгш", 2, lambda n: n != 0 and n % 2 == 0),
        (("odd", "sondgoi", "сондгой"), "Сондгой", 2, lambda n: n % 2 == 1),
        (("low", "1-18"), "1-18", 2, lambda n: 1 <= n <= 18),
        (("high", "19-36"), "19-36", 2, lambda n: 19 <= n <= 36),
        (("1st", "d1", "1-12"), "1-12", 3, lambda n: 1 <= n <= 12),
        (("2nd", "d2", "13-24"), "13-24", 3, lambda n: 13 <= n <= 24),
        (("3rd", "d3", "25-36"), "25-36", 3, lambda n: 25 <= n <= 36),
    ]
    for names, label, mult, fn in simple:
        if t in names:
            return label, mult, fn
    if t.isdigit() and 0 <= int(t) <= 36:
        k = int(t)
        return f"{roulette_color(k)} {k}", 36, lambda n, k=k: n == k
    return None


# ================= blackjack =================
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]


def draw_card():
    return random.choice(RANKS), random.choice(SUITS)


def hand_value(cards) -> int:
    total = sum(11 if r == "A" else 10 if r in ("J", "Q", "K") else int(r) for r, _ in cards)
    aces = sum(1 for r, _ in cards if r == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def show(cards, hide_second=False) -> str:
    if hide_second:
        return f"`{cards[0][0]}{cards[0][1]}` `🂠`"
    return " ".join(f"`{r}{s}`" for r, s in cards)


class BlackjackView(OwnerView):
    def __init__(self, cog, ctx, bet: int):
        super().__init__(ctx.author.id, timeout=90)
        self.cog, self.ctx, self.bet = cog, ctx, bet
        self.player = [draw_card(), draw_card()]
        self.dealer = [draw_card(), draw_card()]
        self.done = False
        self.doubled = False
        self.hit_btn = nav_button("🃏 Нэмэх", self.on_hit, discord.ButtonStyle.primary)
        self.stand_btn = nav_button("✋ Зогсох", self.on_stand, discord.ButtonStyle.success)
        self.double_btn = nav_button("✖️2 Давхарлах", self.on_double)
        for b in (self.hit_btn, self.stand_btn, self.double_btn):
            self.add_item(b)

    def embed(self, reveal=False, footer="") -> discord.Embed:
        e = discord.Embed(title="🃏 Blackjack", color=GOLD)
        e.add_field(name=f"🧑 Та ({hand_value(self.player)})", value=show(self.player), inline=False)
        dv = f" ({hand_value(self.dealer)})" if reveal else ""
        e.add_field(name=f"🏦 Дилер{dv}", value=show(self.dealer, hide_second=not reveal), inline=False)
        e.add_field(name="💸 Бооцоо", value=fmt(self.bet), inline=True)
        if footer:
            e.set_footer(text=footer)
        return e

    async def settle(self, interaction=None):
        """Дилер тоглож, төлбөр тооцно."""
        if self.done:
            return
        self.done = True
        self.stop()
        pv = hand_value(self.player)
        natural = len(self.player) == 2 and pv == 21 and not self.doubled
        if pv <= 21:
            while hand_value(self.dealer) < 17:
                self.dealer.append(draw_card())
        dv = hand_value(self.dealer)
        dealer_nat = len(self.dealer) == 2 and dv == 21
        if pv > 21:
            payout, note = 0, "💥 Хэтэрлээ (bust)!"
        elif natural and not dealer_nat:
            payout, note = int(self.bet * 2.5), "🎉 Blackjack! (3:2)"
        elif dv > 21:
            payout, note = self.bet * 2, "Дилер хэтэрлээ!"
        elif pv > dv:
            payout, note = self.bet * 2, "Та хожлоо!"
        elif pv == dv:
            payout, note = self.bet, "Тэнцлээ (бооцоо буцна)"
        else:
            payout, note = 0, "Дилер хожлоо"
        if payout:
            await self.cog.bot.db.bank_add(self.owner_id, payout)
        self.disable_all()
        bank = await bank_of(self.cog.bot, self.owner_id)
        e = result_embed("🃏 Blackjack", f"{note}\n🧑 {show(self.player)} = **{pv}**\n🏦 {show(self.dealer)} = **{dv}**", self.bet, payout, bank)
        if interaction is not None:
            await interaction.response.edit_message(embed=e, view=self)
        elif self.message is not None:
            try:
                await self.message.edit(embed=e, view=self)
            except Exception:
                pass

    async def on_hit(self, interaction):
        if self.done:
            await interaction.response.defer()
            return
        self.double_btn.disabled = True
        self.player.append(draw_card())
        v = hand_value(self.player)
        if v >= 21:
            await self.settle(interaction)
        else:
            await interaction.response.edit_message(embed=self.embed(), view=self)

    async def on_stand(self, interaction):
        await self.settle(interaction)

    async def on_double(self, interaction):
        if self.done:
            await interaction.response.defer()
            return
        if not await self.cog.bot.db.bank_spend(self.owner_id, self.bet):
            await interaction.response.send_message("❌ Банкны дансанд давхарлах мөнгө алга.", ephemeral=True)
            return
        self.bet *= 2
        self.doubled = True
        self.player.append(draw_card())
        await self.settle(interaction)

    async def on_timeout(self):
        await self.settle(None)


# ================= crash =================
def crash_mult(step: int) -> float:
    return round(1.09 ** step, 2)


class CrashView(OwnerView):
    def __init__(self, cog, ctx, bet: int):
        super().__init__(ctx.author.id, timeout=150)
        self.cog, self.ctx, self.bet = cog, ctx, bet
        u = random.random()
        self.crash_point = min(50.0, max(1.0, 0.96 / max(u, 1e-9)))
        self.step = 0
        self.mult = 1.0
        self.done = False
        self.task = None
        self.cash_btn = nav_button("💰 Мөнгө авах", self.on_cash, discord.ButtonStyle.success)
        self.add_item(self.cash_btn)

    def embed(self, crashed=False) -> discord.Embed:
        if crashed:
            e = discord.Embed(title="💥 Crash!", description=f"Ракет **×{self.crash_point:.2f}** дээр дэглэв.", color=RED)
        else:
            e = discord.Embed(title="🚀 Crash", description=f"# ×{self.mult:.2f}\nАвах дүн: **{fmt(int(self.bet * self.mult))}**", color=GOLD)
        e.add_field(name="💸 Бооцоо", value=fmt(self.bet), inline=True)
        return e

    def start(self):
        self.task = asyncio.create_task(self._run())

    async def _run(self):
        try:
            if self.crash_point <= 1.0:
                await asyncio.sleep(1.2)
                await self._crash()
                return
            while not self.done:
                await asyncio.sleep(1.2)
                if self.done:
                    return
                self.step += 1
                nxt = crash_mult(self.step)
                if nxt >= self.crash_point:
                    await self._crash()
                    return
                self.mult = nxt
                if self.message is not None:
                    try:
                        await self.message.edit(embed=self.embed(), view=self)
                    except Exception:
                        pass
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("Crash алдаа")

    async def _crash(self):
        if self.done:
            return
        self.done = True
        self.stop()
        self.disable_all()
        bank = await bank_of(self.cog.bot, self.owner_id)
        e = result_embed("💥 Crash!", f"Ракет **×{self.crash_point:.2f}** дээр дэглэв. Та мөнгөө аваагүй.", self.bet, 0, bank)
        if self.message is not None:
            try:
                await self.message.edit(embed=e, view=self)
            except Exception:
                pass

    async def on_cash(self, interaction):
        if self.done:
            await interaction.response.defer()
            return
        self.done = True
        if self.task is not None:
            self.task.cancel()
        self.stop()
        payout = int(self.bet * self.mult)
        await self.cog.bot.db.bank_add(self.owner_id, payout)
        self.disable_all()
        bank = await bank_of(self.cog.bot, self.owner_id)
        e = result_embed("💰 Crash: амжилттай авлаа", f"**×{self.mult:.2f}** дээр мөнгөө авлаа! (Ракет ×{self.crash_point:.2f} дээр дэглэх байсан)", self.bet, payout, bank)
        await interaction.response.edit_message(embed=e, view=self)

    async def on_timeout(self):
        if not self.done:
            self.done = True
            if self.task is not None:
                self.task.cancel()
            payout = int(self.bet * self.mult)
            await self.cog.bot.db.bank_add(self.owner_id, payout)


# ================= морин уралдаан =================
HORSES = [  # (нэр, emoji, магадлал)
    ("Хүрэн", "🟤", 0.30), ("Хул", "🟡", 0.25), ("Цоохор", "⚪", 0.18),
    ("Шарга", "🟠", 0.12), ("Хар", "⚫", 0.09), ("Халзан", "🔴", 0.06),
]
HORSE_EDGE = 0.95
TRACK = 18


def horse_mult(i: int) -> float:
    return round(HORSE_EDGE / HORSES[i][2], 2)


def track_frame(pos: list[int], title: str) -> str:
    lines = []
    for i, (name, emo, _) in enumerate(HORSES):
        p = min(TRACK, pos[i])
        lines.append(f"`{i + 1}` {emo} {'·' * p}🐎{'·' * (TRACK - p)}🏁 {name}")
    return f"**{title}**\n" + "\n".join(lines)


class HorseView(OwnerView):
    def __init__(self, cog, ctx, bet: int):
        super().__init__(ctx.author.id, timeout=60)
        self.cog, self.ctx, self.bet = cog, ctx, bet
        sel = discord.ui.Select(
            placeholder="🐎 Морьдоо сонгоно уу...",
            options=[discord.SelectOption(label=f"{i + 1}. {n}", value=str(i), emoji=None,
                                          description=f"Ялбал ×{horse_mult(i)}")
                     for i, (n, _, _) in enumerate(HORSES)],
        )
        sel.callback = self.on_pick
        self.add_item(sel)
        self.sel = sel
        self.started = False

    def embed(self) -> discord.Embed:
        e = discord.Embed(title="🐎 Морин уралдаан", color=GOLD)
        e.description = "\n".join(
            f"`{i + 1}` {emo} **{n}** — ялбал **×{horse_mult(i)}**" for i, (n, emo, _) in enumerate(HORSES)
        )
        e.add_field(name="💸 Бооцоо", value=fmt(self.bet), inline=True)
        e.set_footer(text="Морьдоо сонгосны дараа бооцоо банкнаас хасагдана")
        return e

    async def on_pick(self, interaction, pick: int | None = None):
        if self.started:
            await interaction.response.defer()
            return
        self.started = True
        if pick is None:
            pick = int(self.sel.values[0])
        if not await self.cog.bot.db.bank_spend(self.owner_id, self.bet):
            self.disable_all()
            await interaction.response.edit_message(
                embed=discord.Embed(title="❌ Банкны дансанд мөнгө хүрэлцэхгүй", color=RED), view=self)
            self.stop()
            return
        self.stop()
        self.disable_all()
        winner = random.choices(range(len(HORSES)), weights=[h[2] for h in HORSES])[0]
        await interaction.response.edit_message(embed=discord.Embed(description="🏇 Уралдаан эхэллээ...", color=GOLD), view=None)
        msg = interaction.message
        frames = 5
        pos = [0] * len(HORSES)
        for f in range(1, frames + 1):
            frac = f / frames
            for i in range(len(HORSES)):
                if i == winner:
                    pos[i] = int(TRACK * frac) if f < frames else TRACK
                else:
                    cap = TRACK - 1 if f == frames else int(TRACK * frac)
                    pos[i] = max(pos[i], min(cap, random.randint(max(0, int(TRACK * frac) - 5), max(1, int(TRACK * frac) + 1))))
            try:
                await msg.edit(content=track_frame(pos, f"Уралдаан: {f}/{frames}"), embed=None)
            except Exception:
                pass
            await asyncio.sleep(1.2)
        win = pick == winner
        payout = int(self.bet * horse_mult(pick)) if win else 0
        if payout:
            await self.cog.bot.db.bank_add(self.owner_id, payout)
        bank = await bank_of(self.cog.bot, self.owner_id)
        wname, wemo, _ = HORSES[winner]
        pname = HORSES[pick][0]
        desc = f"🏆 Түрүүлсэн: {wemo} **{winner + 1}. {wname}**\nТаны морь: **{pick + 1}. {pname}**"
        e = result_embed("🐎 Морин уралдаан", desc, self.bet, payout, bank)
        try:
            await msg.edit(content=track_frame([TRACK if i == winner else pos[i] for i in range(len(HORSES))], "Дууслаа"), embed=e)
        except Exception:
            await msg.channel.send(embed=e)


class Casino2(commands.Cog):
    """Казино: рулет, blackjack, crash, морин уралдаан."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(name="roulette", aliases=["rl", "rulet", "рулет"])
    async def roulette(self, ctx: commands.Context, amount: str, bet_on: str):
        """Рулет: roulette <дүн> <red|black|even|odd|low|high|1st|2nd|3rd|0-36>"""
        parsed = parse_roulette(bet_on)
        if parsed is None:
            await send_usage(ctx)
            return
        label, mult, fn = parsed
        bet = await take_bet(ctx, amount)
        if bet is None:
            return
        msg = await ctx.reply("🎡 Дугуй эргэж байна...", mention_author=False)
        await asyncio.sleep(1.5)
        n = random.randint(0, 36)
        win = fn(n)
        payout = bet * mult if win else 0
        if payout:
            await self.bot.db.bank_add(ctx.author.id, payout)
        desc = f"🎡 Бөмбөг: {roulette_color(n)} **{n}**\nТаны сонголт: **{label}** (×{mult})"
        e = result_embed("🎡 Рулет", desc, bet, payout, await bank_of(self.bot, ctx.author.id))
        try:
            await msg.edit(content=None, embed=e)
        except Exception:
            await ctx.send(embed=e)

    @commands.command(name="blackjack", aliases=["bj", "21"])
    async def blackjack(self, ctx: commands.Context, amount: str):
        """Blackjack: blackjack <дүн> (Blackjack 3:2, давхарлах боломжтой)"""
        bet = await take_bet(ctx, amount)
        if bet is None:
            return
        view = BlackjackView(self, ctx, bet)
        if hand_value(view.player) == 21:
            view.message = await ctx.reply("🃏 ...", mention_author=False)
            await view.settle(None)
            return
        view.message = await reply(ctx, embed=view.embed(), view=view)

    @commands.command(name="crash")
    async def crash(self, ctx: commands.Context, amount: str):
        """Crash: crash <дүн> (ракет дэглэхээс өмнө мөнгөө аваарай)"""
        bet = await take_bet(ctx, amount)
        if bet is None:
            return
        view = CrashView(self, ctx, bet)
        view.message = await reply(ctx, embed=view.embed(), view=view)
        view.start()

    @commands.command(name="horse", aliases=["morin", "uraldaan", "мори"])
    async def horse(self, ctx: commands.Context, amount: str, horse_no: str = None):
        """Морин уралдаан: horse <дүн> [1-6]"""
        user = await self.bot.db.get_user(ctx.author.id)
        from utils import jailed, parse_amount
        if await jailed(ctx, user):
            return
        bet = parse_amount(amount, min(user["bank"], MAX_BET))
        if bet is None or bet < MIN_BET or bet > MAX_BET:
            await send_usage(ctx)
            return
        if user["bank"] < bet:
            await reply(ctx, f"❌ Банкны дансанд мөнгө хүрэлцэхгүй байна. `{ctx.clean_prefix}dep`")
            return
        if horse_no is not None and horse_no.isdigit() and 1 <= int(horse_no) <= len(HORSES):
            view = HorseView(self, ctx, bet)
            view.message = await ctx.reply("🏇 ...", mention_author=False)
            fake = _Fake(ctx, view.message)
            await view.on_pick(fake, int(horse_no) - 1)
            return
        view = HorseView(self, ctx, bet)
        view.message = await reply(ctx, embed=view.embed(), view=view)


class _Fake:
    """horse <дүн> <№> бичихэд цэсгүйгээр шууд эхлүүлэхэд зориулсан interaction хуурамч."""

    class _Resp:
        def __init__(self, msg):
            self.msg = msg

        async def edit_message(self, **kw):
            kw.pop("view", None)
            await self.msg.edit(**kw)

    def __init__(self, ctx, msg):
        self.user = ctx.author
        self.message = msg
        self.response = self._Resp(msg)


async def setup(bot):
    await bot.add_cog(Casino2(bot))
