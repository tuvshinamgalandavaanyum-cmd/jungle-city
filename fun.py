import math
import random

import aiohttp
import discord
from discord.ext import commands

from ui import OwnerView, nav_button
from usage import send_usage
from utils import reply

# (нэр, nekos.best төрөл, үйлдлийн текст, өөртөө хийвэл текст, өнгө, emoji[, nsfw])
ROMANCE = [
    ("hug", "hug", "{a} {b}-г тэвэрлээ", "{a} өөрийгөө тэвэрлээ", 0xF472B6, "🤗"),
    ("kiss", "kiss", "{a} {b}-г үнсэв", "{a} агаарыг үнсэв", 0xEC4899, "😘"),
    ("cuddle", "cuddle", "{a} {b}-тэй наалдан тэврэв", "{a} дэрийг тэврэв", 0xF472B6, "🥰"),
    ("pat", "pat", "{a} {b}-ийн толгойг илэв", "{a} өөрийнхөө толгойг илэв", 0xFBBF24, "🫳"),
    ("handhold", "handhold", "{a} {b}-ийн гараас барилаа", "{a} гараа атгав", 0xF472B6, "🤝"),
    ("blush", "blush", "{a} {b}-ийн өмнө улайв", "{a} улайв", 0xF472B6, "😊"),
    ("wink", "wink", "{a} {b} руу нүд ирмэв", "{a} нүд ирмэв", 0xEC4899, "😉"),
    ("peck", "peck", "{a} {b}-ийн хацрыг үнсэв", "{a} хацраа илэв", 0xEC4899, "😚"),
    ("feed", "feed", "{a} {b}-г хооллов", "{a} өөрийгөө хооллов", 0x22C55E, "🍙"),
    ("sleep", "sleep", "{a} {b}-ийн мөрөн дээр унтаж орхив", "{a} тайван унтлаа", 0x818CF8, "😴"),
]
FIGHT = [
    ("slap", "slap", "{a} {b}-г алгадлаа", "{a} өөрийгөө алгадлаа", 0xEF4444, "👋"),
    ("punch", "punch", "{a} {b}-г цохилоо", "{a} агаарыг цохилоо", 0xDC2626, "👊"),
    ("kick", "kick", "{a} {b}-г өшиглөв", "{a} өөрийгөө өшиглөв", 0xDC2626, "🦵"),
    ("bite", "bite", "{a} {b}-г зууллаа", "{a} өөрийгөө зууллаа", 0xEF4444, "😬"),
    ("poke", "poke", "{a} {b}-г хуруугаараа гэв", "{a} өөрийгөө гэв", 0x60A5FA, "👉"),
    ("shoot", "shoot", "{a} {b}-г буудав 🔫", "{a} агаар руу буудав", 0xB91C1C, "🔫"),
    ("yeet", "yeet", "{a} {b}-г холдуулан шидэв", "{a} өөрийгөө шидэв", 0xF97316, "🚀"),
    ("baka", "baka", "{a} {b}-г тэнэг гэж загнав", "{a} өөрийгөө загнав", 0xF59E0B, "💢"),
    ("stare", "stare", "{a} {b} рүү ширтэв", "{a} хоосон ширтэв", 0x6B7280, "👀"),
    ("pout", "pout", "{a} {b}-д гомдов", "{a} уруулаа цорвойлгов", 0xF59E0B, "😤"),
    ("nope", "nope", "{a} {b}-д «үгүй!» гэв", "{a} «үгүй!» гэв", 0xEF4444, "🙅"),
    ("run", "run", "{a} {b}-аас зугтав", "{a} гүйв", 0x22C55E, "🏃"),
]
LAUGH = [
    ("laugh", "laugh", "{a} {b}-ийг хараад инээв", "{a} инээв", 0xFBBF24, "😂"),
    ("smile", "smile", "{a} {b} руу инээмсэглэв", "{a} инээмсэглэв", 0xFBBF24, "😄"),
    ("happy", "happy", "{a} {b}-тэй хамт баярлав", "{a} баярлав", 0xFBBF24, "🥳"),
    ("dance", "dance", "{a} {b}-тэй бүжиглэв", "{a} бүжиглэв", 0xA855F7, "💃"),
    ("tickle", "tickle", "{a} {b}-г гижигдэв", "{a} өөрийгөө гижигдэв", 0xFBBF24, "🤭"),
    ("highfive", "highfive", "{a} {b}-тэй алгаа ташив", "{a} өөртэйгөө алгаа ташив", 0x22C55E, "🙌"),
    ("thumbsup", "thumbsup", "{a} {b}-д 👍 өгөв", "{a} 👍 үзүүлэв", 0x22C55E, "👍"),
    ("wave", "wave", "{a} {b} рүү гараа даллав", "{a} гараа даллав", 0x38BDF8, "👋"),
    ("smug", "smug", "{a} {b}-ийн өмнө бардам инээв", "{a} бардам инээв", 0xA855F7, "😏"),
    ("facepalm", "facepalm", "{a} {b}-г хараад духаа таллаа", "{a} духаа таллаа", 0xF59E0B, "🤦"),
    ("shrug", "shrug", "{a} {b}-д мөрөө хавчив", "{a} мөрөө хавчив", 0x6B7280, "🤷"),
    ("nom", "nom", "{a} {b}-тэй хамт амттан зооглов", "{a} амттан зооглов", 0x22C55E, "😋"),
    ("cry", "cry", "{a} {b}-ийн өмнө уйллаа", "{a} уйллаа", 0x3B82F6, "😭"),
]
ROMANCE += [
    ("blowkiss", "kiss", "{a} {b} рүү үнсэлт илгээв", "{a} агаарт үнсэлт илгээв", 0xEC4899, "😙"),
    ("iloveyou", "cuddle", "{a} {b}-д хайртай гэв", "{a} өөрийгөө хайрлав", 0xF472B6, "❤️"),
    ("flowers", "pat", "{a} {b}-д цэцэг барив", "{a} өөртөө цэцэг авав", 0xF472B6, "💐"),
    ("serenade", "dance", "{a} {b}-д хайрын дуу дуулав", "{a} ганцаараа дуулав", 0xEC4899, "🎤"),
    ("gaze", "stare", "{a} {b}-ийн нүд рүү удаан ширтэв", "{a} толинд ширтэв", 0xEC4899, "👁️"),
    ("tuck", "sleep", "{a} {b}-г хөнжлөөр нөмрүүлэв", "{a} хөнжилдөө ороов", 0x818CF8, "🛌"),
]
FIGHT += [
    ("angry", "pout", "{a} {b}-д ихэд ууртай байна", "{a} уурлав", 0xDC2626, "😡"),
    ("headbutt", "punch", "{a} {b}-г духаараа цохив", "{a} хананд духаараа цохив", 0xDC2626, "🤕"),
    ("throw", "yeet", "{a} {b}-г өргөж шидэв", "{a} өөрийгөө шидэв", 0xF97316, "🤾"),
    ("tackle", "kick", "{a} {b}-г унагаав", "{a} өөрөө унав", 0xEF4444, "🏉"),
    ("roast", "baka", "{a} {b}-г шоолж загнав", "{a} өөрийгөө шоолов", 0xF59E0B, "🔥"),
    ("threaten", "stare", "{a} {b}-г сүрдүүлэв", "{a} өөрийгөө сүрдүүлэв", 0xB91C1C, "😠"),
]
SOCIAL = [
    ("handshake", "handshake", "{a} {b}-тэй гар барив", "{a} гараа даллав", 0x22C55E, "🤝"),
    ("clap", "highfive", "{a} {b}-д алга ташив", "{a} алга ташив", 0x22C55E, "👏"),
    ("cheer", "happy", "{a} {b}-г хөгжөөв", "{a} баярлан хөгжив", 0xFBBF24, "📣"),
    ("bow", "wave", "{a} {b}-д мэхийн ёслов", "{a} мэхийн ёслов", 0x38BDF8, "🙇"),
    ("salute", "wave", "{a} {b}-д мэндчилэв", "{a} мэндчилэв", 0x38BDF8, "🫡"),
    ("nod", "nod", "{a} {b}-тэй санал нийлэв", "{a} толгой дохив", 0x22C55E, "🙂"),
    ("lurk", "lurk", "{a} {b}-ийг нууцаар ажиглав", "{a} нуугдав", 0x6B7280, "🫣"),
    ("think", "think", "{a} {b}-ийн тухай бодов", "{a} бодолд автав", 0x6B7280, "🤔"),
    ("yawn", "yawn", "{a} {b}-ийн өмнө эвшээв", "{a} эвшээв", 0x6B7280, "🥱"),
    ("bored", "bored", "{a} {b}-тэй уйдав", "{a} уйдав", 0x6B7280, "😑"),
]
# 🔞 насанд хүрэгчдийн сэдэвтэй (ил биш), зөвхөн NSFW (age-restricted) суваг дээр
ADULT = [
    ("flirt", "wink", "{a} {b}-тэй сээтэглэв 😏", "{a} толинд өөртэйгөө сээтэглэв", 0xEC4899, "😏", True),
    ("seduce", "smug", "{a} {b}-г уруу татав 😈", "{a} өөртөө итгэлтэй инээмсэглэв", 0xBE185D, "😈", True),
    ("lick", None, "{a} {b}-г долоов 😛", "{a} уруулаа долоов", 0xEC4899, "😛", True),
    ("spank", None, "{a} {b}-г зөөлхөн алгадав 🍑", "{a} өөрийгөө алгадав", 0xBE185D, "🍑", True),
    ("massage", None, "{a} {b}-ийн мөрийг үрж өгөв 💆", "{a} өөрийнхөө мөрийг үрлээ", 0xA855F7, "💆", True),
    ("whisper", None, "{a} {b}-ийн чихэнд сэмхэн шивнэв 🤫", "{a} өөртөө шивнэв", 0x818CF8, "🤫", True),
    ("nibble", "bite", "{a} {b}-ийн чихийг зөөлхөн мэрэв 😈", "{a} уруулаа зууав", 0xBE185D, "👄", True),
    ("lapdance", "dance", "{a} {b}-д сэтгэл татам бүжиг үзүүлэв 💃", "{a} толины өмнө бүжиглэв", 0xBE185D, "🔥", True),
    ("tease", "smug", "{a} {b}-г шоолж тоглов 😜", "{a} өөрийгөө шоолов", 0xEC4899, "😜", True),
    ("naughty", "smug", "{a} {b}-тэй дэггүй тоглов 😼", "{a} дэггүй инээв", 0xBE185D, "😼", True),
]
ADULT += [
    ("charm", "wink", "{a} {b}-г байлдан дагуулахыг оролдов 😎", "{a} өөртөө итгэлтэй байна", 0xBE185D, "😎", True),
    ("cuddlebed", "cuddle", "{a} {b}-тэй хөнжлийн дор наалдав 🛏️", "{a} дэрийг тэврэв", 0xA855F7, "🛏️", True),
    ("lipbite", "blush", "{a} {b} рүү харан уруулаа зөөлхөн хазав 😘", "{a} уруулаа хазав", 0xEC4899, "💋", True),
]
EMOTE_GROUPS = [
    ("romance", "💞", "Romance", ROMANCE),
    ("fight", "⚔️", "Fight", FIGHT),
    ("laugh", "😂", "Laugh", LAUGH),
    ("social", "🤝", "Social", SOCIAL),
    ("adult", "🔞", "+18", ADULT),
]
EMOTES = [e for _, _, _, lst in EMOTE_GROUPS for e in lst]

API = "https://nekos.best/api/v2/{}"
FALLBACK = {}  # төрөл -> бэлэн GIF холбоос (хүсвэл энд нэмж болно)


async def fetch_gif(kind: str | None) -> str | None:
    if not kind:
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(API.format(kind)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["results"][0]["url"]
    except Exception:
        pass
    return FALLBACK.get(kind)


def make_emote(name, kind, text_other, text_self, color, emoji, nsfw=False):
    @commands.command(name=name, help=f"{emoji} {name}")
    async def emote(ctx: commands.Context, member: discord.Member = None):
        if member is None:
            await send_usage(ctx)
            return
        if nsfw and not getattr(ctx.channel, "is_nsfw", lambda: False)():
            await reply(ctx, "🔞 Энэ эможи зөвхөн NSFW (насанд хүрэгчдийн) суваг дээр ажиллана.")
            return
        a, b = ctx.author.mention, member.mention
        text = text_self if member.id == ctx.author.id else text_other
        embed = discord.Embed(description=f"{emoji} **{text.format(a=a, b=b)}**", color=color)
        gif = await fetch_gif(kind)
        if gif:
            embed.set_image(url=gif)
        await ctx.send(embed=embed)

    return emote


PER = 8


class EmoteView(OwnerView):
    """Дэлгүүр шиг: ангилал сонгох, хуудаслах, эможи сонгож үзэх."""

    def __init__(self, ctx, nsfw: bool, group: str | None = None):
        super().__init__(ctx.author.id, timeout=240)
        self.ctx, self.nsfw = ctx, nsfw
        self.groups = [g for g in EMOTE_GROUPS if g[0] != "adult" or nsfw]
        keys = [g[0] for g in self.groups]
        self.gi = keys.index(group) if group in keys else 0
        self.page = 0
        self.selected = None
        self.gif = None

    @property
    def items(self):
        return self.groups[self.gi][3]

    async def build(self):
        for c in list(self.children):
            self.remove_item(c)
        key, emoji, title, lst = self.groups[self.gi]
        pages = max(1, math.ceil(len(lst) / PER))
        self.page = max(0, min(self.page, pages - 1))
        chunk = lst[self.page * PER:(self.page + 1) * PER]
        p = self.ctx.clean_prefix
        gsel = discord.ui.Select(
            placeholder="Ангилал сонгоно уу...",
            options=[discord.SelectOption(label=f"{t} ({len(l)})", value=str(n), emoji=e, default=n == self.gi)
                     for n, (k, e, t, l) in enumerate(self.groups)],
            row=0,
        )
        gsel.callback = self.on_group(gsel)
        self.add_item(gsel)
        lines = []
        for e in chunk:
            name, emo, text = e[0], e[5], e[2].format(a="Та", b="@хүн")
            mark = "👉 " if self.selected == name else ""
            lines.append(f"{mark}{emo} `{p}{name} @хүн`\n> {text}")
        embed = discord.Embed(title=f"🎭 Эможи · {emoji} {title}", description="\n".join(lines) or "—", color=0xEC4899)
        if not self.nsfw:
            embed.add_field(name="🔞 +18", value="Зөвхөн NSFW суваг дээр харагдана", inline=False)
        if chunk:
            isel = discord.ui.Select(
                placeholder="Эможи сонгож жишээ үзэх...",
                options=[discord.SelectOption(label=e[0], value=e[0], emoji=e[5], default=e[0] == self.selected) for e in chunk],
                row=1,
            )
            isel.callback = self.on_item(isel)
            self.add_item(isel)
        self.add_item(nav_button("◀", self.on_prev, disabled=self.page <= 0, row=2))
        self.add_item(nav_button(f"{self.page + 1}/{pages}", self.on_noop, disabled=True, row=2))
        self.add_item(nav_button("▶", self.on_next, disabled=self.page >= pages - 1, row=2))
        if self.gif:
            embed.set_image(url=self.gif)
        embed.set_footer(text=f"{p}<эможи> @хүн · нийт {sum(len(g[3]) for g in self.groups)} эможи")
        return embed

    def on_group(self, sel):
        async def cb(interaction):
            self.gi, self.page, self.selected, self.gif = int(sel.values[0]), 0, None, None
            await interaction.response.edit_message(embed=await self.build(), view=self)
        return cb

    def on_item(self, sel):
        async def cb(interaction):
            await interaction.response.defer()
            self.selected = sel.values[0]
            e = next(x for x in self.items if x[0] == self.selected)
            self.gif = await fetch_gif(e[1])
            await interaction.edit_original_response(embed=await self.build(), view=self)
        return cb

    async def on_prev(self, interaction):
        self.page -= 1
        self.selected = self.gif = None
        await interaction.response.edit_message(embed=await self.build(), view=self)

    async def on_next(self, interaction):
        self.page += 1
        self.selected = self.gif = None
        await interaction.response.edit_message(embed=await self.build(), view=self)

    async def on_noop(self, interaction):
        await interaction.response.defer()


@commands.command(name="emote", aliases=["emotes", "emoji"])
async def emote_list(ctx: commands.Context, group: str = None):
    """Эможи цэс (дэлгүүр шиг): emote [romance | fight | laugh | social | 18]"""
    nsfw = getattr(ctx.channel, "is_nsfw", lambda: False)()
    q = (group or "").lower().lstrip("+")
    key = {"18": "adult", "adult": "adult"}.get(q, q) or None
    view = EmoteView(ctx, nsfw, key)
    view.message = await ctx.reply(embed=await view.build(), view=view, mention_author=False)


async def setup(bot):
    for e in EMOTES:
        bot.add_command(make_emote(*e))
    bot.add_command(emote_list)
