"""Staff: админаас доогуур, татварын сангаас giveaway/event зохион байгуулах эрхтэй хүмүүс."""
import time

import discord
from discord.ext import commands

from perms import STAFF_CAP, is_admin, is_staff
from usage import send_usage
from utils import fmt, parse_amount, reply

MAX_WINNERS = 25
PODIUM = {1: [1.0], 2: [0.6, 0.4], 3: [0.5, 0.3, 0.2]}
ACTION_NAME = {"giveaway": "🎉 Giveaway", "event": "🎪 Event", "podium": "🏆 Podium", "donate": "💝 Хандив"}


async def staff_limit(bot, member, pool: int) -> int:
    """Нэг удаад тараах дээд дүн: админд сангийн бүгд, staff-д STAFF_CAP хувь."""
    return pool if await is_admin(bot, member) else int(pool * STAFF_CAP)


class Staff(commands.Cog):
    """Staff: сангаас event/giveaway зохион байгуулна."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    # ---------- staff жагсаалт ----------
    @commands.group(name="staff", invoke_without_command=True)
    async def staff(self, ctx: commands.Context):
        """Staff: жагсаалт, эрх, татварын сан"""
        p = ctx.clean_prefix
        pool = await self.bot.db.get_setting("pool")
        ids = await self.bot.db.list_staff()
        e = discord.Embed(title="🎖️ Staff", color=0xF59E0B)
        e.description = (
            "Staff бол админаас доогуур түвшний эрхтэй хүн. Тэд **татварын сангаас** giveaway болон event зохион байгуулж, "
            f"мөнгийг хүмүүст тараана. Нэг удаад сангийн хамгийн ихдээ **{int(STAFF_CAP * 100)}%**-ийг тарааж болно.\n\n"
            f"🏛️ Сан: **{fmt(pool)}**"
        )
        e.add_field(name=f"👥 Staff ({len(ids)})", value="\n".join(f"<@{i}>" for i in ids) or "*Одоогоор алга*", inline=False)
        e.add_field(
            name="📋 Командууд",
            value=(
                f"`{p}giveaway <дүн|pool> <10m|2h|1d> [ялагч]`: товчоор оролцдог giveaway\n"
                f"`{p}event give <дүн|pool> @хүн @хүн ... [нэр]`: тэнцүү хуваан өгөх\n"
                f"`{p}event podium <дүн|pool> @1-р @2-р @3-р [нэр]`: 50/30/20 хуваалт\n"
                f"`{p}event log`: сүүлийн үйлдлүүд\n"
                f"`{p}donate <дүн>`: хэн ч санд хандивлаж болно\n"
                f"`{p}staff add|remove @хүн`: staff томилох (админ)"
            ),
            inline=False,
        )
        await reply(ctx, embed=e)

    @staff.command(name="add", aliases=["op"])
    async def staff_add(self, ctx: commands.Context, member: discord.Member):
        """Staff томилох (админ)"""
        if not await is_admin(self.bot, ctx.author):
            await reply(ctx, "🚫 Staff-ийг зөвхөн админ томилно.")
            return
        if member.bot:
            await reply(ctx, "❌ Ботыг staff болгох боломжгүй.")
            return
        ok = await self.bot.db.add_staff(member.id, ctx.author.id)
        if ok:
            await self.bot.db.log_staff(ctx.author.id, "staff+", 0, f"<@{member.id}>")
        await reply(ctx, f"🎖️ {member.mention} staff боллоо." if ok else "ℹ️ Энэ хүн аль хэдийн staff байна.")

    @staff.command(name="remove", aliases=["del", "deop", "rm"])
    async def staff_remove(self, ctx: commands.Context, member: discord.Member):
        """Staff эрх хасах (админ)"""
        if not await is_admin(self.bot, ctx.author):
            await reply(ctx, "🚫 Staff эрхийг зөвхөн админ хасна.")
            return
        ok = await self.bot.db.remove_staff(member.id)
        if ok:
            await self.bot.db.log_staff(ctx.author.id, "staff-", 0, f"<@{member.id}>")
        await reply(ctx, f"✅ {member.mention}-ийн staff эрх хасагдлаа." if ok else "ℹ️ Энэ хүн staff биш байна.")

    # ---------- event ----------
    async def _recipients(self, ctx, members):
        out, seen = [], set()
        for m in members:
            if m.bot or m.id in seen:
                continue
            seen.add(m.id)
            if not (await self.bot.db.get_user(m.id))["registered"]:
                await reply(ctx, f"❌ {m.mention} бүртгүүлээгүй байна.")
                return None
            out.append(m)
        if not out:
            await send_usage(ctx)
            return None
        if len(out) > MAX_WINNERS:
            await reply(ctx, f"❌ Нэг удаад дээд тал нь {MAX_WINNERS} хүнд өгнө.")
            return None
        return out

    async def _payout(self, ctx, amount: str, members, name: str, podium: bool):
        if not await is_staff(self.bot, ctx.author):
            await reply(ctx, "🚫 Энэ командыг зөвхөн staff эсвэл админ ашиглана.")
            return
        db = self.bot.db
        pool = await db.get_setting("pool")
        total = parse_amount(amount, pool)
        if total is None or total < 1:
            await send_usage(ctx)
            return
        people = await self._recipients(ctx, members)
        if people is None:
            return
        if podium:
            if len(people) > 3:
                await reply(ctx, "❌ Podium дээд тал нь 3 хүн (1, 2, 3-р байр).")
                return
            weights = PODIUM[len(people)]
            shares = {m.id: int(total * w) for m, w in zip(people, weights)}
        else:
            each = total // len(people)
            shares = {m.id: each for m in people}
        paid = sum(shares.values())
        if paid < len(people):
            await reply(ctx, "❌ Дүн хэт бага байна.")
            return
        limit = await staff_limit(self.bot, ctx.author, pool)
        if paid > limit:
            await reply(
                ctx,
                f"❌ Нэг удаад дээд тал нь **{fmt(limit)}** тарааж болно "
                f"(сангийн {int(STAFF_CAP * 100)}%). Сан: **{fmt(pool)}**",
            )
            return
        name = name.strip() or "Event"
        action = "podium" if podium else "event"
        if not await db.pool_payout(shares, ctx.author.id, action, name):
            await reply(ctx, f"❌ Татварын сан хүрэлцэхгүй байна. Сан: **{fmt(await db.get_setting('pool'))}**")
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, m in enumerate(people):
            tag = medals[i] if podium else "🎁"
            lines.append(f"{tag} {m.mention}: **{fmt(shares[m.id])}**")
        e = discord.Embed(title=f"🎪 {name}", description="\n".join(lines), color=0x22C55E)
        e.add_field(name="💸 Нийт", value=fmt(paid), inline=True)
        e.add_field(name="🏛️ Санд үлдсэн", value=fmt(await db.get_setting("pool")), inline=True)
        e.set_footer(text=f"Зохион байгуулагч: {ctx.author.display_name}")
        await ctx.send(
            embed=e,
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    @commands.group(name="event", aliases=["ev"], invoke_without_command=True)
    async def event(self, ctx: commands.Context):
        """Event: staff сангаас шагнал тараана (event give | podium | log)"""
        await send_usage(ctx)

    @event.command(name="give", aliases=["pay", "reward"])
    async def event_give(self, ctx: commands.Context, amount: str, members: commands.Greedy[discord.Member], *, name: str = "Event"):
        """Event шагнал: event give <дүн|pool> @хүн @хүн ... [нэр]"""
        await self._payout(ctx, amount, members, name, podium=False)

    @event.command(name="podium", aliases=["top", "rank"])
    async def event_podium(self, ctx: commands.Context, amount: str, members: commands.Greedy[discord.Member], *, name: str = "Event"):
        """Event podium: event podium <дүн|pool> @1-р @2-р @3-р [нэр]"""
        await self._payout(ctx, amount, members, name, podium=True)

    @event.command(name="log", aliases=["history", "logs"])
    async def event_log(self, ctx: commands.Context):
        """Staff-ийн сүүлийн үйлдлүүд"""
        rows = await self.bot.db.staff_log_recent(10)
        if not rows:
            await reply(ctx, "📭 Одоогоор бүртгэл алга.")
            return
        lines = []
        for r in rows:
            when = f"<t:{int(r['at'])}:R>"
            kind = ACTION_NAME.get(r["action"], r["action"])
            amt = f" · **{fmt(r['amount'])}**" if r["amount"] else ""
            note = f" · {r['note']}" if r["note"] else ""
            lines.append(f"{kind} <@{r['user_id']}>{amt}{note} {when}")
        await reply(ctx, embed=discord.Embed(title="📜 Staff бүртгэл", description="\n".join(lines), color=0x3B82F6))

    # ---------- хандив ----------
    @commands.command(name="donate", aliases=["pooladd", "hand"])
    async def donate(self, ctx: commands.Context, amount: str):
        """Татварын санд хандивлах: donate <дүн>"""
        user = await self.bot.db.get_user(ctx.author.id)
        if not user["registered"]:
            await reply(ctx, f"❌ Эхлээд `{ctx.clean_prefix}register` хийнэ үү.")
            return
        amt = parse_amount(amount, user["balance"])
        if amt is None or amt < 1_000:
            await send_usage(ctx)
            return
        if not await self.bot.db.donate_pool(ctx.author.id, amt):
            await reply(ctx, "❌ Хэтэвчинд мөнгө хүрэлцэхгүй байна.")
            return
        pool = await self.bot.db.get_setting("pool")
        await reply(ctx, f"💝 Санд **{fmt(amt)}** хандивлалаа. Сангийн үлдэгдэл: **{fmt(pool)}**")


async def setup(bot):
    await bot.add_cog(Staff(bot))
