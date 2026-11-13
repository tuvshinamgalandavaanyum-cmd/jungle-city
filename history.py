import asyncio
import io
import math

import discord
from discord.ext import commands
from PIL import Image

from sprite import render_preview  # noqa: F401
from ui import OwnerView, nav_button, safe_edit
from utils import reply

PER = 20
STORY_MAX = 1500
IMG_MAX_BYTES = 6 * 1024 * 1024


def make_jpeg(data: bytes) -> bytes | None:
    try:
        im = Image.open(io.BytesIO(data))
        if im.width * im.height > 40_000_000:
            return None
        im.load()
        im = im.convert("RGB")
        im.thumbnail((900, 900))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        return None


def display_name(bot, guild, uid: int) -> str:
    m = guild.get_member(uid) if guild else None
    if m is not None:
        return m.display_name
    u = bot.get_user(uid)
    return u.display_name if u is not None else f"Тоглогч {str(uid)[-4:]}"


class StoryModal(discord.ui.Modal, title="📖 Миний түүх"):
    def __init__(self, view, current: str):
        super().__init__()
        self.view = view
        self.story = discord.ui.TextInput(
            label="Өөрийнхөө тухай бич", style=discord.TextStyle.paragraph, max_length=STORY_MAX, required=True,
            placeholder="Жишээ: Би Африкийн хүн. 7 жилийн өмнө АНУ-д очсон...",
            default=current[:STORY_MAX] if current else None,
        )
        self.add_item(self.story)

    async def on_submit(self, interaction):
        text = str(self.story.value).strip()
        await self.view.cog.bot.db.set_story(self.view.owner_id, text)
        self.view.selected = self.view.owner_id
        await self.view.refresh(interaction)


class HistoryView(OwnerView):
    def __init__(self, cog, ctx, selected: int | None = None):
        super().__init__(ctx.author.id, timeout=300)
        self.cog, self.ctx = cog, ctx
        self.selected = selected
        self.page = 0
        self.users: list[tuple[int, bool]] = []

    async def build(self):
        bot = self.cog.bot
        db = bot.db
        for c in list(self.children):
            self.remove_item(c)
        self.users = await db.history_users()
        pages = max(1, math.ceil(len(self.users) / PER))
        if self.selected is not None:
            ids = [u for u, _ in self.users]
            if self.selected in ids:
                self.page = ids.index(self.selected) // PER
        self.page = max(0, min(self.page, pages - 1))
        chunk = self.users[self.page * PER:(self.page + 1) * PER]
        guild = self.ctx.guild
        if chunk:
            opts = []
            for uid, has in chunk:
                u = await db.get_user(uid)
                desc = f"{u['age']} нас · {u['country'] or '—'}" + ("" if has else " · түүх алга")
                opts.append(discord.SelectOption(
                    label=display_name(bot, guild, uid)[:100], value=str(uid), emoji="📖" if has else "▫️",
                    description=desc[:100], default=uid == self.selected))
            sel = discord.ui.Select(placeholder="👤 Хүн сонгож түүхийг нь унших...", options=opts, row=0)
            sel.callback = self.on_pick(sel)
            self.add_item(sel)
        self.add_item(nav_button("◀", self.on_prev, disabled=self.page <= 0, row=1))
        self.add_item(nav_button(f"{self.page + 1}/{pages}", self.on_noop, disabled=True, row=1))
        self.add_item(nav_button("▶", self.on_next, disabled=self.page >= pages - 1, row=1))
        self.add_item(nav_button("✏️ Миний түүх", self.on_write, discord.ButtonStyle.primary, row=1))
        self.add_item(nav_button("🗑 Зураг устгах", self.on_del_img, row=1))

        p = self.ctx.clean_prefix
        file = None
        if self.selected is None:
            embed = discord.Embed(
                title="📖 Хүмүүсийн түүх",
                description=(
                    "Бүртгэлтэй хүмүүсийн түүхийг унших жагсаалт. Нэрийг нь сонгоод түүхийг нь үзнэ.\n"
                    f"`📖` түүхтэй · `▫️` түүх бичээгүй\n\n"
                    f"✏️ **Миний түүх** товчоор өөрийнхөө түүхийг бичнэ.\n"
                    f"🖼 Зураг оруулах: зураг хавсаргаад `{p}history pic` гэж бичнэ (эсвэл зурагтай мессежид хариулна)."
                ),
                color=0x3B82F6,
            )
            embed.set_footer(text=f"Нийт {len(self.users)} хүн · {p}history @хүн")
            return embed, None
        row = await db.get_history(self.selected)
        u = await db.get_user(self.selected)
        name = display_name(bot, guild, self.selected)
        story = (row["story"] if row else "") or "*Түүх бичээгүй байна.*"
        embed = discord.Embed(title=f"📖 {name}-ийн түүх", description=story, color=0xEC4899)
        embed.add_field(name="Нас", value=str(u["age"]), inline=True)
        embed.add_field(name="Улс", value=u["country"] or "—", inline=True)
        embed.add_field(name="Хэрэглэгч", value=f"<@{self.selected}>", inline=True)
        if row and row["image"]:
            file = discord.File(io.BytesIO(bytes(row["image"])), filename="history.jpg")
            embed.set_image(url="attachment://history.jpg")
        embed.set_footer(text=f"{p}history pic — өөрийн зураг оруулах")
        return embed, file

    async def refresh(self, interaction):
        embed, file = await self.build()
        await safe_edit(interaction, embed=embed, view=self, attachments=[file] if file else [])

    def on_pick(self, sel):
        async def cb(interaction):
            self.selected = int(sel.values[0])
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

    async def on_noop(self, interaction):
        await interaction.response.defer()

    async def on_write(self, interaction):
        row = await self.cog.bot.db.get_history(self.owner_id)
        await interaction.response.send_modal(StoryModal(self, (row["story"] if row else "") or ""))

    async def on_del_img(self, interaction):
        await self.cog.bot.db.set_story_image(self.owner_id, None)
        self.selected = self.owner_id
        await self.refresh(interaction)


class History(commands.Cog):
    """Дүрийн түүх: өөрийнхөө түүхийг бичиж, бусдын түүхийг унших."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(name="history", aliases=["tuuh_ushih", "story", "түүх", "bio"])
    async def history(self, ctx: commands.Context, arg: str = None):
        """Хүмүүсийн түүх: history [@хүн] | history pic (зураг хавсаргана)"""
        if arg and arg.lower() in ("pic", "image", "zurag", "photo"):
            att = next((a for a in ctx.message.attachments if (a.content_type or "").startswith("image/")), None)
            ref = ctx.message.reference.resolved if ctx.message.reference else None
            if att is None and isinstance(ref, discord.Message):
                att = next((a for a in ref.attachments if (a.content_type or "").startswith("image/")), None)
            if att is None:
                await reply(ctx, "🖼 Зураг хавсаргаад дахин бичнэ үү (эсвэл зурагтай мессежид хариулна уу).")
                return
            if att.size > IMG_MAX_BYTES:
                await reply(ctx, "❌ Зураг 6MB-аас бага байх ёстой.")
                return
            jpg = await asyncio.to_thread(make_jpeg, await att.read())
            if jpg is None:
                await reply(ctx, "❌ Зургийг уншиж чадсангүй.")
                return
            await self.bot.db.set_story_image(ctx.author.id, jpg)
            view = HistoryView(self, ctx, ctx.author.id)
            e, f = await view.build()
            view.message = await ctx.reply(embed=e, file=f, view=view, mention_author=False) if f else await reply(ctx, embed=e, view=view)
            return
        selected = None
        if arg:
            digits = "".join(ch for ch in arg if ch.isdigit())
            if digits:
                uid = int(digits)
                if (await self.bot.db.get_user(uid))["registered"]:
                    selected = uid
                else:
                    await reply(ctx, "❌ Тэр хүн бүртгүүлээгүй байна.")
                    return
        view = HistoryView(self, ctx, selected)
        e, f = await view.build()
        if f:
            view.message = await ctx.reply(embed=e, file=f, view=view, mention_author=False)
        else:
            view.message = await reply(ctx, embed=e, view=view)


async def setup(bot):
    await bot.add_cog(History(bot))
