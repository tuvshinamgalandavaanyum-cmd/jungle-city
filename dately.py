import math
import time

import discord
from gameart import art_file, stamp
from discord.ext import commands

from invview import owns
from ui import OwnerView, nav_button, safe_edit
from utils import reply

PER = 20
REQUEST_COOLDOWN = 5 * 60
GENDER = {"male": "👨", "female": "👩"}


def name_of(bot, guild, uid: int) -> str:
    m = guild.get_member(uid) if guild else None
    if m is not None:
        return m.display_name
    u = bot.get_user(uid)
    return u.display_name if u is not None else f"Тоглогч {str(uid)[-4:]}"


class RequestView(discord.ui.View):
    """Dately хүсэлт: зөвхөн хүлээн авагч «ok» эсвэл «nahh» дарна."""

    def __init__(self, bot, a: discord.abc.User, b_id: int):
        super().__init__(timeout=600)
        self.bot, self.a, self.b_id = bot, a, b_id
        self.resolved = False
        self.message = None
        self.add_item(nav_button("✅ ok", self.on_ok, discord.ButtonStyle.success))
        self.add_item(nav_button("❌ nahh", self.on_no, discord.ButtonStyle.danger))

    async def interaction_check(self, interaction) -> bool:
        if interaction.user.id != self.b_id:
            await interaction.response.send_message("❌ Энэ хүсэлт танд ирээгүй.", ephemeral=True)
            return False
        return True

    def _off(self):
        for c in self.children:
            c.disabled = True
        self.stop()

    async def on_ok(self, interaction):
        if self.resolved:
            await interaction.response.defer()
            return
        self.resolved = True
        self._off()
        new = await self.bot.db.add_match(self.a.id, self.b_id)
        e = discord.Embed(
            title="💘 Match!",
            description=f"{self.a.mention} 💞 <@{self.b_id}>\n" + ("Хоёулаа санал нийллээ. Танилцаарай!" if new else "Та нар өмнө нь match болсон байна."),
            color=0xEC4899,
        )
        await interaction.response.edit_message(embed=e, view=self)

    async def on_no(self, interaction):
        if self.resolved:
            await interaction.response.defer()
            return
        self.resolved = True
        self._off()
        e = discord.Embed(title="💔 nahh", description=f"<@{self.b_id}> хүсэлтийг зөвшөөрсөнгүй.", color=0x6B7280)
        await interaction.response.edit_message(embed=e, view=self)

    async def on_timeout(self):
        if self.resolved:
            return
        self._off()
        if self.message is not None:
            try:
                await self.message.edit(embed=discord.Embed(title="⌛ Хариу ирсэнгүй", color=0x6B7280), view=self)
            except Exception:
                pass


class DatelyView(OwnerView):
    def __init__(self, cog, owner, channel, guild, prefix: str):
        super().__init__(owner.id, timeout=300)
        self.cog, self.owner, self.channel, self.guild, self.prefix = cog, owner, channel, guild, prefix
        self.page = 0
        self.selected = None
        self.msg = ""

    async def build(self):
        bot = self.cog.bot
        db = bot.db
        for c in list(self.children):
            self.remove_item(c)
        users = [(u, h) for u, h in await db.history_users() if u != self.owner_id]
        pages = max(1, math.ceil(len(users) / PER))
        self.page = max(0, min(self.page, pages - 1))
        chunk = users[self.page * PER:(self.page + 1) * PER]
        if chunk:
            opts = []
            for uid, has in chunk:
                u = await db.get_user(uid)
                matched = await db.is_match(self.owner_id, uid)
                desc = f"{u['age']} нас · {u['country'] or '—'}" + (" · 💘 match" if matched else "")
                opts.append(discord.SelectOption(
                    label=name_of(bot, self.guild, uid)[:100], value=str(uid), emoji=GENDER.get(u["gender"], "🧑"),
                    description=desc[:100], default=uid == self.selected))
            sel = discord.ui.Select(placeholder="💘 Хүн сонгох...", options=opts, row=0)
            sel.callback = self.on_pick(sel)
            self.add_item(sel)
        self.add_item(nav_button("◀", self.on_prev, disabled=self.page <= 0, row=1))
        self.add_item(nav_button(f"{self.page + 1}/{pages}", self.on_noop, disabled=True, row=1))
        self.add_item(nav_button("▶", self.on_next, disabled=self.page >= pages - 1, row=1))
        self.add_item(nav_button("💌 Хүсэлт илгээх", self.on_send, discord.ButtonStyle.success, disabled=self.selected is None, row=1))
        self.add_item(nav_button("💞 Match-ууд", self.on_matches, row=1))

        embed = stamp(discord.Embed(title="💘 Dately", color=0xEC4899), "dately")
        if self.selected is None:
            embed.description = "Бүртгэлтэй хүмүүсээс нэгийг сонгоод **💌 Хүсэлт илгээх** дарна.\nТэр хүн **ok** дарвал match болно, **nahh** дарвал татгалзана."
        else:
            u = await db.get_user(self.selected)
            row = await db.get_history(self.selected)
            story = ((row["story"] if row else "") or "")[:300]
            embed.description = f"{GENDER.get(u['gender'], '🧑')} <@{self.selected}> · {u['age']} нас · {u['country'] or '—'}"
            if story:
                embed.add_field(name="📖 Түүх", value=story + ("…" if len(row["story"]) > 300 else ""), inline=False)
        if self.msg:
            embed.add_field(name="ℹ️", value=self.msg, inline=False)
        embed.set_footer(text=f"{len(users)} хүн · {self.prefix}history — түүх унших")
        return embed

    async def refresh(self, interaction):
        await safe_edit(interaction, embed=await self.build(), view=self)

    def on_pick(self, sel):
        async def cb(interaction):
            self.selected = int(sel.values[0])
            self.msg = ""
            await self.refresh(interaction)
        return cb

    async def on_prev(self, interaction):
        self.page -= 1
        await self.refresh(interaction)

    async def on_next(self, interaction):
        self.page += 1
        await self.refresh(interaction)

    async def on_noop(self, interaction):
        await interaction.response.defer()

    async def on_send(self, interaction):
        db = self.cog.bot.db
        if self.selected is None:
            await interaction.response.defer()
            return
        now = time.time()
        last = self.cog.last.get(self.owner_id, 0)
        if now - last < REQUEST_COOLDOWN:
            self.msg = f"⏳ Дараагийн хүсэлтээ {int(REQUEST_COOLDOWN - (now - last))} секундийн дараа илгээнэ."
        elif await db.is_match(self.owner_id, self.selected):
            self.msg = "💘 Та нар аль хэдийн match болсон байна."
        else:
            self.cog.last[self.owner_id] = now
            req = RequestView(self.cog.bot, self.owner, self.selected)
            e = discord.Embed(
                title="💘 Dately хүсэлт",
                description=f"<@{self.selected}>, {self.owner.mention} тантай Dately-ээр танилцахыг хүсэж байна!\n"
                "**ok** дарвал зөвшөөрнө, **nahh** дарвал татгалзана.",
                color=0xEC4899,
            )
            stamp(e, "dately")
            try:
                req.message = await self.channel.send(
                    f"<@{self.selected}>", embed=e, view=req, file=art_file("dately"),
                    allowed_mentions=discord.AllowedMentions(users=True))
                self.msg = "✅ Хүсэлт илгээгдлээ."
            except Exception:
                self.msg = "❌ Хүсэлт илгээж чадсангүй."
        await self.refresh(interaction)

    async def on_matches(self, interaction):
        rows = await self.cog.bot.db.matches(self.owner_id)
        if not rows:
            await interaction.response.send_message("💔 Одоогоор match алга.", ephemeral=True)
            return
        text = "\n".join(f"💘 <@{r['other']}> · <t:{int(r['ts'])}:R>" for r in rows[:25])
        await interaction.response.send_message(embed=discord.Embed(title="💞 Миний match-ууд", description=text, color=0xEC4899), ephemeral=True)


class Dately(commands.Cog):
    """Утасны Dately апп: танилцах хүсэлт илгээх."""

    def __init__(self, bot):
        self.bot = bot
        self.last: dict[int, float] = {}

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def open_for(self, owner, channel, guild, prefix):
        view = DatelyView(self, owner, channel, guild, prefix)
        return view, await view.build()

    @commands.command(name="dately", aliases=["dating", "tinder", "датели"])
    async def dately(self, ctx: commands.Context):
        """📱 Dately апп: хүн сонгож танилцах хүсэлт илгээх (утас хэрэгтэй)"""
        if not await owns(self.bot.db, ctx.author.id, "phone"):
            await reply(ctx, f"📵 Dately-д утас хэрэгтэй. `{ctx.clean_prefix}buy nokia` эсвэл `{ctx.clean_prefix}buy phone`")
            return
        view, embed = await self.open_for(ctx.author, ctx.channel, ctx.guild, ctx.clean_prefix)
        view.message = await reply(ctx, embed=embed, view=view, file=art_file("dately"))


async def setup(bot):
    await bot.add_cog(Dately(bot))
