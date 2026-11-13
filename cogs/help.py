import time
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from invview import owns
from ui import OwnerView, nav_button
from utils import reply

UB = timezone(timedelta(hours=8))

# (түлхүүр, emoji, нэр, тайлбар, [(команд, тайлбар)])
APPS = [
    ("bank", "🏦", "Банк", "Мөнгө, данс", [
        ("bal [@хүн]", "Хэтэвч, банк, хөрөнгө"),
        ("daily", "Өдрийн цалин (10% татвартай)"),
        ("dep / with <дүн|all>", "Банкинд хийх / авах (шимтгэл 200₮)"),
        ("give <@хүн> <дүн>", "Мөнгө шилжүүлэх"),
        ("lb [bank|wallet|total]", "Тэргүүлэгчид"),
        ("pool", "Татварын сан"),
    ]),
    ("work", "💼", "Ажил", "Ажил, дасгал, малтлага", [
        ("work", "Ажил хийх (1 цаг, 10% татвар)"),
        ("jobs", "Ажлын жагсаалт"),
        ("dasgal", "💪 Хүч + 💻 хакерын ур чадвар худалдаж авах цэс"),
        ("workout", "Дасгал хийх (хүч +1)"),
        ("mine", "Алт малтах (40%)"),
    ]),
    ("shop", "🛍️", "Дэлгүүр", "Хоол, тавилга, хувцас", [
        ("shop [ангилал]", "food, digital, home, house, car, top, bottom, shoes, hat, acc, jewel, metal, box, tool"),
        ("buy <ID> [тоо]", "Авах (цэснээс 🛒 товчоор ч болно)"),
        ("sell <ID|all>", "Зарах (70%)"),
        ("gift <ID> <@хүн>", "Бэлэглэх"),
        ("open <box|case|chest>", "Хайрцаг нээх"),
    ]),
    ("bag", "🎒", "Цүнх", "Гэр · Халаас · Машин", [
        ("inv", "3 хэсэгтэй цүнх (🏠 Гэр · 🎒 Халаас · 🚗 Машин)"),
        ("inv use <ID>", "Хоол, бамбай, potion ашиглах"),
        ("wardrobe", "🚪 Хувцасны шкаф (гэртээ байрлуулсан байх ёстой)"),
        ("fridge", "🧊 Хөргөгч: хоол харж идэх (гэртээ байрлуулсан байх ёстой)"),
    ]),
    ("car", "🚗", "Машин", "Lv 1-99 · Beginner → Impossible", [
        ("cars", "Машины цэс (түвшингээр, зурагтай)"),
        ("car <ID>", "Машины GIF харах"),
        ("buy <ID>", "Худалдаж авах → ажлын цалин +%"),
    ]),
    ("auction", "🔨", "Дуудлага", "Дуудлага худалдаа, худалдан авалтын түүх", [
        ("auction", "Идэвхтэй дуудлагууд"),
        ("aucsell <ID> <үнэ> [минут]", "Бараагаа дуудлагад тавих"),
        ("bid <№> <дүн>", "Үнэ санал болгох"),
        ("auchistory [ID]", "Зарагдсан үнийн түүх"),
        ("purchases", "Миний худалдан авалт (хэдэн ₮-өөр авсан)"),
    ]),
    ("hair", "💇", "Үсчин", "Үсний засалт (16 хэв маяг, 14 өнгө)", [
        ("hair", "Үсчинд очиж үсээ засуулах (15,000₮)"),
    ]),
    ("history", "📖", "Түүх", "Өөрийнхөө түүхийг бичих, бусдынхыг унших", [
        ("history", "Бүртгэлтэй хүмүүсийн жагсаалт → сонгож түүхийг унших"),
        ("history @хүн", "Тухайн хүний түүх"),
        ("history pic", "Зураг хавсаргаад түүхдээ зураг оруулах"),
    ]),
    ("dately", "💘", "Dately", "Утасны апп: танилцах хүсэлт", [
        ("dately", "Хүн сонгож хүсэлт илгээх (утас хэрэгтэй, 📱 утасны цэснээс ч нээнэ)"),
        ("—", "Хүлээн авагч **ok** дарвал match, **nahh** дарвал татгалзана"),
    ]),
    ("photo", "📸", "Зураг", "Машин, амьтан, байшин, хайртай хүнтэйгээ зураг", [
        ("photo [URL]", "Зургийн студи: арын зураг (attachment/URL), давхарга зөөх"),
    ]),
    ("pet", "🐾", "Амьтан", "44 төрлийн хөөрхөн амьтан", [
        ("petshop", "Амьтны дэлгүүр (зурагтай, ◀ ▶)"),
        ("buypet <ID>", "Амьтан авах → профайл дээр дүртэйгээ хамт харагдана"),
    ]),
    ("casino", "🎰", "Казино", "⚠️ Казино зөвхөн банкны данснаас тоглоно (дээд 500,000₮)", [
        ("cf <дүн> [сүүл|тоо]", "Зоос шидэх"),
        ("dice <дүн> <1-6>", "Шоо"),
        ("slots <дүн>", "Слот"),
        ("mf <дүн>", "Minefield"),
        ("roulette <дүн> <red|black|even|odd|low|high|0-36>", "Рулет"),
        ("blackjack <дүн>", "Blackjack (3:2, давхарлах)"),
        ("crash <дүн>", "Crash: ракет дэглэхээс өмнө мөнгөө ав"),
        ("horse <дүн> [1-6]", "Морин уралдаан"),
        ("duel <@хүн> <дүн>", "Чулуу-хайч-даавуу"),
        ("draw <@хүн> <дүн>", "Quick Draw"),
    ]),
    ("house", "🏠", "Байшин", "Байшин, сейф", [
        ("house", "Байшингаа харах"),
        ("house shop / buy <ID>", "Байшин авах"),
        ("house <өрөө> use|unuse <ID>", "Эд зүйл байрлуулах"),
        ("safe [buy|put|take]", "Сейф"),
    ]),
    ("crime", "🥷", "Гэмт хэрэг", "Хулгай, дээрэм, хакер", [
        ("steal [1-5]", "Байшин руу хулгай"),
        ("rob <@хүн>", "💵 Түрийвчний мөнгийг дээрэмдэнэ"),
        ("hack <@хүн>", "🏦 Банкны мөнгийг хакердана (компьютер + хакер Lv)"),
        ("block", "🛡️ Бамбай 2.5 цаг: дээрэм, хакерээс хамгаална"),
        ("bail", "Шоронгоос гарах"),
    ]),
    ("profile", "👤", "Дүр", "Профайл, хувцас", [
        ("profile [@хүн]", "Pixel дүр + амьтан (алхаж буй GIF)"),
        ("wear <ID> / undress <slot>", "Өмсөх / тайлах"),
        ("wardrobe", "Шкафнаас хувцас сонгох"),
    ]),
    ("love", "💞", "Харилцаа", "Гэр бүл, романс", [
        ("marry <@хүн>", "Гэрлэх санал (бөгж)"),
        ("couple", "Гэр бүлийн мэдээлэл"),
        ("date", "Болзоо"),
        ("divorce", "Салах"),
    ]),
    ("emote", "🎭", "Эможи", "Romance · Fight · Laugh · Social · +18", [
        ("emote [ангилал]", "Эможигийн цэс (дэлгүүр шиг, ◀ ▶, жишээ GIF)"),
        ("hug, kiss, cuddle, pat ...", "💞 Romance (10)"),
        ("slap, punch, kick, bite ...", "⚔️ Fight (12)"),
        ("laugh, smile, dance, tickle ...", "😂 Laugh (13)"),
        ("flirt, seduce, tease ...", "🔞 +18 — зөвхөн NSFW суваг (ил биш)"),
    ]),
    ("life", "💖", "Амьдрал", "Хоол, үхэл, Revive", [
        ("eat <ID>", "3 хоног хоолгүй бол 2 цаг тутам хэтэвчний 2.5% хасагдана"),
        ("revive [@хүн]", "7 хоног хоолгүй бол үхнэ. Revive Active амилуулна"),
        ("inv use luck_potion / money_potion", "Аз, орлого +10% (1 цаг)"),
    ]),
    ("info", "ℹ️", "Мэдээлэл", "Бот, сервер", [
        ("info", "Ping, сервер, статистик"),
        ("help", "Энэ цэс (мэдээлэл + хэрэглээ)"),
        ("phone", "📱 Утас: нууц мессеж, цэнэг"),
        ("register", "Бүртгүүлэх"),
    ]),
]
APP_BY_KEY = {a[0]: a for a in APPS}

PHONE_COST = 10  # нэг нууц мессеж = 10% цэнэг
SECRET_MAX = 300


def battery_bar(pct: int) -> str:
    n = max(0, min(10, round(pct / 10)))
    return "🟩" * n + "⬛" * (10 - n) if pct > 20 else "🟥" * n + "⬛" * (10 - n)


# ---------------- qhelp: цэс (мэдээлэл + хэрэглээ) ----------------
def help_home(prefix: str) -> discord.Embed:
    embed = discord.Embed(
        title="📖 Тусламжийн цэс",
        description=(
            f"Доорх цэснээс ангилал сонгож командын **мэдээлэл ба хэрэглээг** үзнэ.\n"
            f"Эсвэл ◀ ▶ товчоор хуудаслана.  `{prefix}help <ангилал>`\n\n"
            + "\n".join(f"{e} **{t}** — {d}" for _, e, t, d, _ in APPS)
        ),
        color=0x3B82F6,
    )
    embed.set_footer(text=f"Утас: {prefix}phone")
    return embed


def help_page(key: str, prefix: str) -> discord.Embed:
    _, emoji, title, desc, cmds = APP_BY_KEY[key]
    lines = [f"`{prefix}{c}`\n└ {d}" for c, d in cmds]
    embed = discord.Embed(title=f"{emoji} {title}", description=f"*{desc}*\n\n" + "\n".join(lines), color=0x3B82F6)
    embed.set_footer(text="<> заавал, [] заавал биш · команд бүрийн дэлгэрэнгүй: командыг параметргүй бичнэ")
    return embed


class HelpView(OwnerView):
    def __init__(self, owner_id: int, prefix: str, index: int = -1):
        super().__init__(owner_id, timeout=240)
        self.prefix = prefix
        self.i = index  # -1 = нүүр
        self.sel = discord.ui.Select(
            placeholder="📂 Ангилал сонгох...",
            options=[discord.SelectOption(label=t, value=k, emoji=e, description=d[:100]) for k, e, t, d, _ in APPS],
        )
        self.sel.callback = self.on_sel
        self.prev = nav_button("◀", self.on_prev)
        self.home = nav_button("🏠", self.on_home, discord.ButtonStyle.primary)
        self.nxt = nav_button("▶", self.on_next)
        for c in (self.sel, self.prev, self.home, self.nxt):
            self.add_item(c)

    def embed(self):
        return help_home(self.prefix) if self.i < 0 else help_page(APPS[self.i][0], self.prefix)

    async def _show(self, interaction):
        self.prev.disabled = self.i < 0
        self.nxt.disabled = self.i >= len(APPS) - 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def on_sel(self, interaction):
        self.i = [a[0] for a in APPS].index(self.sel.values[0])
        await self._show(interaction)

    async def on_prev(self, interaction):
        self.i = max(-1, self.i - 1)
        await self._show(interaction)

    async def on_next(self, interaction):
        self.i = min(len(APPS) - 1, self.i + 1)
        await self._show(interaction)

    async def on_home(self, interaction):
        self.i = -1
        await self._show(interaction)


# ---------------- qphone: утас (цэнэг + нууц мессеж) ----------------
class SecretModal(discord.ui.Modal, title="📩 Нууц мессеж"):
    to = discord.ui.TextInput(label="Хэнд? (@дурдах эсвэл ID)", placeholder="@Bat эсвэл 1234567890", max_length=40)
    text = discord.ui.TextInput(label="Мессеж", style=discord.TextStyle.paragraph, max_length=SECRET_MAX)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction):
        digits = "".join(ch for ch in str(self.to.value) if ch.isdigit())
        if not digits:
            await interaction.response.send_message("❌ Хүнийг зөв оруулна уу.", ephemeral=True)
            return
        member = interaction.guild.get_member(int(digits)) if interaction.guild else None
        msg = await self.cog.send_secret(interaction.user, member, str(self.text.value))
        await interaction.response.send_message(msg, ephemeral=True)


class PhoneView(OwnerView):
    def __init__(self, cog, ctx):
        super().__init__(ctx.author.id, timeout=180)
        self.cog, self.ctx = cog, ctx
        self.add_item(nav_button("📩 Нууц мессеж", self.on_msg, discord.ButtonStyle.primary))
        self.add_item(nav_button("🔌 Цэнэглэх", self.on_charge, discord.ButtonStyle.success))
        self.add_item(nav_button("💘 Dately", self.on_dately))
        self.add_item(nav_button("🔄", self.on_refresh))

    async def build(self):
        db = self.cog.bot.db
        user = await db.get_user(self.owner_id)
        has = await owns(db, self.owner_id, "phone")
        charger = await db.item_qty(self.owner_id, "charger")
        now = datetime.now(UB)
        days = ["Даваа", "Мягмар", "Лхагва", "Пүрэв", "Баасан", "Бямба", "Ням"]
        bat = user["phone_battery"]
        embed = discord.Embed(title="📱 Утас", color=0x111827)
        if not has:
            embed.description = f"📵 Танд утас алга. `{self.ctx.clean_prefix}buy phone` (Дижитал)"
        else:
            embed.description = (
                f"🕒 **{now:%H:%M}** · {days[now.weekday()]}\n\n"
                f"🔋 **{bat}%**\n{battery_bar(bat)}\n\n"
                f"📩 Нууц мессеж: 1 мессеж = **{PHONE_COST}%** цэнэг\n"
                f"🔌 Цэнэглэгч: **{charger}** ширхэг (цэнэг 100% болгоно)"
            )
        embed.set_footer(text=f"{self.ctx.clean_prefix}msg @хүн <текст> · {self.ctx.clean_prefix}help — тусламж")
        return embed

    async def on_msg(self, interaction):
        await interaction.response.send_modal(SecretModal(self.cog))

    async def on_charge(self, interaction):
        msg = await self.cog.charge(self.owner_id)
        await interaction.response.send_message(msg, ephemeral=True)
        try:
            await self.message.edit(embed=await self.build(), view=self)
        except Exception:
            pass

    async def on_dately(self, interaction):
        cog = self.cog.bot.get_cog("Dately")
        if cog is None:
            await interaction.response.send_message("❌ Dately апп одоогоор унтраалттай байна.", ephemeral=True)
            return
        if not await owns(self.cog.bot.db, self.owner_id, "phone"):
            await interaction.response.send_message("📵 Танд утас алга.", ephemeral=True)
            return
        view, embed = await cog.open_for(interaction.user, interaction.channel, interaction.guild, self.ctx.clean_prefix)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def on_refresh(self, interaction):
        await interaction.response.edit_message(embed=await self.build(), view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands", "menu"])
    async def help(self, ctx: commands.Context, app: str = None):
        """Тусламжийн цэс (мэдээлэл + хэрэглээ): help [ангилал]"""
        index = -1
        if app:
            q = app.lower()
            for n, (key, _, title, _, _) in enumerate(APPS):
                if q in (key, title.lower()):
                    index = n
                    break
        view = HelpView(ctx.author.id, ctx.clean_prefix, index)
        view.prev.disabled = index < 0
        view.nxt.disabled = index >= len(APPS) - 1
        view.message = await reply(ctx, embed=view.embed(), view=view)

    @commands.command(name="phone", aliases=["utas", "tel", "телефон"])
    async def phone(self, ctx: commands.Context):
        """📱 Утас: цэнэг, нууц мессеж илгээх"""
        view = PhoneView(self, ctx)
        view.message = await reply(ctx, embed=await view.build(), view=view)

    @commands.command(name="msg", aliases=["secret", "nuuts", "dm"])
    async def msg(self, ctx: commands.Context, member: discord.Member, *, text: str):
        """Нууц мессеж илгээх (утас + цэнэг хэрэгтэй): msg @хүн <текст>"""
        await reply(ctx, await self.send_secret(ctx.author, member, text))

    @commands.command(name="charge", aliases=["tseneg", "цэнэглэх"])
    async def charge_cmd(self, ctx: commands.Context):
        """Утсаа цэнэглэх (Charger хэрэгтэй)"""
        await reply(ctx, await self.charge(ctx.author.id))

    async def charge(self, user_id: int) -> str:
        db = self.bot.db
        if not await owns(db, user_id, "phone"):
            return "📵 Танд утас алга."
        user = await db.get_user(user_id)
        if user["phone_battery"] >= 100:
            return "🔋 Утас аль хэдийн 100%."
        if not await db.remove_item(user_id, "charger", 1):
            return "❌ Танд цэнэглэгч алга. `buy charger`"
        await db.set_battery(user_id, 100)
        return "🔌 Утас 100% цэнэглэгдлээ!"

    async def send_secret(self, sender, member, text: str) -> str:
        db = self.bot.db
        text = text.strip()
        if member is None or member.bot or member.id == sender.id:
            return "❌ Энэ хүн рүү илгээх боломжгүй."
        if not text or len(text) > SECRET_MAX:
            return f"❌ Мессеж 1-{SECRET_MAX} тэмдэгт байх ёстой."
        if not await owns(db, sender.id, "phone"):
            return "📵 Танд утас алга. `buy phone`"
        if not (await db.get_user(member.id))["registered"]:
            return "❌ Тэр хүн бүртгүүлээгүй байна."
        user = await db.get_user(sender.id)
        if user["phone_battery"] < PHONE_COST:
            return "🪫 Утасны цэнэг дууссан. `charge` (Charger хэрэгтэй)"
        embed = discord.Embed(title="📩 Нууц мессеж", description=text, color=0x6366F1)
        embed.set_author(name=f"{sender.display_name}-аас")
        embed.set_footer(text="Энэ мессеж бот дамжуулан ирсэн. Хэн нэгэн таныг дарамталж байвал админд мэдэгдээрэй.")
        try:
            await member.send(embed=embed)
        except Exception:
            return "❌ Тэр хүн DM хаасан тул илгээж чадсангүй. (Цэнэг хасагдаагүй)"
        await db.use_battery(sender.id, PHONE_COST)
        return f"✅ Нууц мессеж илгээгдлээ. 🔋 {user['phone_battery'] - PHONE_COST}%"

    @commands.command(name="info", aliases=["ping", "stats", "server"])
    async def info(self, ctx: commands.Context):
        """Бот ба серверийн мэдээлэл"""
        db = self.bot.db
        stats = await db.stats()
        top = await db.top("total", 1, 0)
        started = getattr(self.bot, "started_at", time.time())
        up = int(time.time() - started)
        d, rem = divmod(up, 86400)
        h, rem = divmod(rem, 3600)
        ping = round(self.bot.latency * 1000) if self.bot.latency == self.bot.latency else 0

        embed = discord.Embed(title="ℹ️ Мэдээлэл", color=0x3B82F6)
        embed.add_field(name="🏓 Ping", value=f"{ping} ms", inline=True)
        embed.add_field(name="⏱️ Ажилласан", value=f"{d}ө {h}ц {rem // 60}м", inline=True)
        embed.add_field(name="🌐 Сервер", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Гишүүд", value=str(ctx.guild.member_count), inline=True)
        embed.add_field(name="🎮 Тоглогч", value=str(stats["players"]), inline=True)
        embed.add_field(name="💞 Гэрлэсэн хос", value=str(stats["married"]), inline=True)
        embed.add_field(name="💰 Нийт мөнгө", value=f"{stats['money']:,}₮", inline=True)
        embed.add_field(name="🏛️ Татварын сан", value=f"{stats['pool']:,}₮", inline=True)
        embed.add_field(name="⛓️ Шоронд", value=str(stats["jailed"]), inline=True)
        embed.add_field(name="💀 Үхсэн", value=str(stats["dead"]), inline=True)
        if top:
            t = top[0]
            embed.add_field(name="👑 Хамгийн баян", value=f"<@{t['user_id']}>", inline=True)
        embed.set_footer(text=f"{ctx.clean_prefix}help — утас")
        await reply(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
