import random
import time

import discord
from discord.ext import commands

from actions import maybe_revive_drop
from houses import comfort_pct
from items import CARS, ITEMS, get_pet
from jobs import JOBS
from ui import OwnerView, nav_button
from utils import (
    HACK_SKILL_MAX,
    HACK_SKILL_PER_LEVEL,
    MAX_STRENGTH,
    apply_tax,
    boost_mult,
    fmt,
    fmt_duration,
    hack_skill_price,
    jailed,
    reply,
)

WORK_COOLDOWN = 60 * 60  # 1 цаг
WORKOUT_COOLDOWN = 2 * 60 * 60  # 2 цаг
CAT_BONUS = 0.10  # Муур: ажлын цалин +10%
STRENGTH_BONUS = 0.01  # хүч 1 тутамд ажлын цалин +1%


def pay_status(pay: int) -> str:
    if pay < 60_000:
        return "🪙 Бага цалин"
    if pay < 80_000:
        return "💼 Дундаж цалин"
    if pay < 100_000:
        return "✨ Сайн цалинтай ажил"
    return "🔥 Маш өндөр цалин"


async def placed_value(db, user_id: int) -> int:
    rows = await db.get_house_items(user_id)
    return sum(ITEMS[r["item_key"]].price * r["qty"] for r in rows if r["item_key"] in ITEMS)


class Work(commands.Cog):
    """Санамсаргүй ажил хийх, дасгал хийх."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild is not None

    @commands.command(name="work", aliases=["w"])
    async def work(self, ctx: commands.Context):
        """Санамсаргүй ажил хийж цалин авах"""
        user = await self.bot.db.get_user(ctx.author.id)
        if await jailed(ctx, user):
            return
        now = time.time()

        left = user["last_work"] + WORK_COOLDOWN - now
        if left > 0:
            await reply(ctx, f"⏳ Та амарч байна. **{fmt_duration(left)}**-ийн дараа дахин ажиллана.")
            return

        job = random.choice(JOBS)
        base = int(job.salary * random.uniform(0.9, 1.1) / 100) * 100
        bonus_pct = user["strength"] * STRENGTH_BONUS
        comfort = comfort_pct(await placed_value(self.bot.db, ctx.author.id)) / 100
        pet = get_pet(user["pet"])
        cat = pet.work_bonus if pet else 0.0
        inv = {r["item_key"] for r in await self.bot.db.get_inventory(ctx.author.id)}
        car = max((c.bonus for c in CARS if c.key in inv), default=0.0)
        love = min(user["love"] // 10, 5) / 100 if user["spouse"] else 0.0
        gross = int(base * (1 + bonus_pct + comfort + cat + car + love) * boost_mult(user) / 100) * 100
        pay, tax = apply_tax(gross)

        ok = await self.bot.db.complete_work(ctx.author.id, pay, now, WORK_COOLDOWN)
        if not ok:
            await reply(ctx, "⏳ Та амарч байна. Дахин оролдоно уу.")
            return

        embed = discord.Embed(title="💼 Цагийн ажил хийлээ", color=0x3B82F6)
        embed.description = f"{job.emoji} **{job.name}**\n*{job.desc}*"
        embed.add_field(name="⏱️ Ажилласан хугацаа", value="1 цаг", inline=True)
        await self.bot.db.add_setting("pool", tax)
        embed.add_field(name="💵 Олсон мөнгө", value=f"**{pay:,} ₮**", inline=True)
        embed.add_field(name="🧾 Татвар (10%)", value=f"-{tax:,} ₮", inline=True)
        embed.add_field(name="📈 Статус", value=pay_status(gross), inline=False)
        extras = []
        if bonus_pct:
            extras.append(f"💪 Хүч +{int(bonus_pct * 100)}%")
        if comfort:
            extras.append(f"🏠 Байшин +{int(comfort * 100)}%")
        if cat:
            extras.append(f"{pet.emoji} {pet.name} +{round(cat * 100)}%")
        if car:
            extras.append(f"🚗 Машин +{int(car * 100)}%")
        if love:
            extras.append(f"💞 Хайр +{int(love * 100)}%")
        if boost_mult(user) > 1:
            extras.append("💰 Money potion +10%")
        if extras:
            embed.add_field(name="✨ Нэмэгдэл", value=" · ".join(extras), inline=False)
        embed.set_footer(text=f"⏰ Дараагийн ажил: 1 цагийн дараа • {ctx.clean_prefix}workout хийвэл илүү олно")
        await reply(ctx, embed=embed)
        await maybe_revive_drop(self.bot, ctx)

    @commands.command(name="jobs")
    async def jobs_list(self, ctx: commands.Context):
        """Хийж болох ажлууд ба цалингийн жагсаалт"""
        lines = [f"{j.emoji} **{j.name}** — ~{fmt(j.salary)}" for j in JOBS]
        half = len(lines) // 2
        embed = discord.Embed(
            title="💼 Ажлын жагсаалт",
            description=(
                f"`{ctx.clean_prefix}work` бүрт эдгээрээс санамсаргүй нэгийг хийнэ. "
                "Цалин ажлын газраас хамаарна."
            ),
            color=0x3B82F6,
        )
        embed.add_field(name="​", value="\n".join(lines[:half]), inline=True)
        embed.add_field(name="​", value="\n".join(lines[half:]), inline=True)
        await reply(ctx, embed=embed)

    @commands.command(name="dasgal", aliases=["skills", "huch", "power", "ur_chadvar"])
    async def dasgal(self, ctx: commands.Context):
        """Дасгал, хүч, хакерын ур чадвар (мөнгөөр худалдаж авна)"""
        view = DasgalView(self, ctx)
        embed = await view.build()
        view.message = await reply(ctx, embed=embed, view=view)

    @commands.command(name="workout", aliases=["gym"])
    async def workout(self, ctx: commands.Context):
        """Дасгал хийж хүч нэмэх (ажлын орлого, дээрэмд тусална)"""
        user = await self.bot.db.get_user(ctx.author.id)
        if await jailed(ctx, user):
            return
        now = time.time()

        if user["strength"] >= MAX_STRENGTH:
            await reply(ctx, f"💪 Таны хүч дээд түвшиндээ ({MAX_STRENGTH}) хүрсэн байна.")
            return
        left = user["last_workout"] + WORKOUT_COOLDOWN - now
        if left > 0:
            await reply(ctx, f"⏳ Булчин амарч байна. **{fmt_duration(left)}**-ийн дараа дахин дасгал хийнэ.")
            return

        ok = await self.bot.db.complete_workout(ctx.author.id, now, WORKOUT_COOLDOWN, MAX_STRENGTH)
        if not ok:
            await reply(ctx, "⏳ Булчин амарч байна. Дахин оролдоно уу.")
            return

        s = user["strength"] + 1
        embed = discord.Embed(title="🏋️ Дасгал хийлээ", color=0xF97316)
        embed.description = "💪 *Фитнесс төвд хүчтэй дасгал хийлээ*"
        embed.add_field(name="⏱️ Хугацаа", value="1 цаг", inline=True)
        embed.add_field(name="💪 Хүч", value=f"**{s}/{MAX_STRENGTH}**", inline=True)
        embed.add_field(
            name="📈 Статус",
            value=f"Ажлын орлого **+{int(s * STRENGTH_BONUS * 100)}%** · дээрэмд амжилт +{s}%",
            inline=False,
        )
        embed.set_footer(text="⏰ Дараагийн дасгал: 2 цагийн дараа • Дасгал хийх тусам ажлын орлого нэмэгдэнэ")
        await reply(ctx, embed=embed)


class DasgalView(OwnerView):
    def __init__(self, cog, ctx):
        super().__init__(ctx.author.id, timeout=180)
        self.cog, self.ctx = cog, ctx
        self.msg = ""
        self.gym_btn = nav_button("🏋️ Дасгал хийх", self.on_gym, discord.ButtonStyle.primary)
        self.hack_btn = nav_button("💻 Хакер ахиулах", self.on_hack, discord.ButtonStyle.success)
        self.add_item(self.gym_btn)
        self.add_item(self.hack_btn)

    async def build(self) -> discord.Embed:
        user = await self.cog.bot.db.get_user(self.ctx.author.id)
        lvl = user["hack_level"]
        now = time.time()
        left = user["last_workout"] + WORKOUT_COOLDOWN - now
        embed = discord.Embed(title="🏋️ Дасгал ба ур чадвар", color=0xF97316)
        embed.add_field(
            name="💪 Хүч",
            value=f"**{user['strength']}/{MAX_STRENGTH}**\nАжлын орлого +{user['strength']}% · дээрэмд амжилт +{user['strength']}%\n"
            + (f"⏳ Дараагийн дасгал: {fmt_duration(left)}" if left > 0 else "✅ Дасгал хийхэд бэлэн"),
            inline=True,
        )
        if lvl >= HACK_SKILL_MAX:
            nxt = "🏆 Дээд түвшин"
        else:
            nxt = f"Дараагийн Lv {lvl + 1}: **{fmt(hack_skill_price(lvl))}** (+5% амжилт, үнэ бүрт +30%)"
        embed.add_field(
            name="💻 Хакерын ур чадвар",
            value=f"**Lv {lvl}/{HACK_SKILL_MAX}** · хакердах амжилт +{lvl * HACK_SKILL_PER_LEVEL}%\n{nxt}",
            inline=True,
        )
        embed.add_field(name="💰 Түрийвч", value=fmt(user["balance"]), inline=False)
        if self.msg:
            embed.add_field(name="ℹ️", value=self.msg, inline=False)
        self.hack_btn.disabled = lvl >= HACK_SKILL_MAX
        self.gym_btn.disabled = user["strength"] >= MAX_STRENGTH or left > 0
        embed.set_footer(text=f"{self.ctx.clean_prefix}hack @хүн — хакердах (компьютертой байх ёстой)")
        return embed

    async def on_gym(self, interaction):
        user = await self.cog.bot.db.get_user(self.owner_id)
        now = time.time()
        ok = (
            user["strength"] < MAX_STRENGTH
            and user["last_workout"] + WORKOUT_COOLDOWN <= now
            and await self.cog.bot.db.complete_workout(self.owner_id, now, WORKOUT_COOLDOWN, MAX_STRENGTH)
        )
        self.msg = "💪 Дасгал хийлээ! Хүч +1" if ok else "❌ Одоогоор дасгал хийх боломжгүй."
        await interaction.response.edit_message(embed=await self.build(), view=self)

    async def on_hack(self, interaction):
        user = await self.cog.bot.db.get_user(self.owner_id)
        lvl = user["hack_level"]
        if lvl >= HACK_SKILL_MAX:
            self.msg = "🏆 Дээд түвшин."
        else:
            price = hack_skill_price(lvl)
            if await self.cog.bot.db.buy_hack_level(self.owner_id, lvl + 1, price):
                self.msg = f"✅ Хакер Lv {lvl + 1} боллоо! (−{fmt(price)})"
            else:
                self.msg = f"❌ Мөнгө хүрэлцэхгүй. {fmt(price)} хэрэгтэй."
        await interaction.response.edit_message(embed=await self.build(), view=self)


async def setup(bot: commands.Bot):
    await bot.add_cog(Work(bot))
