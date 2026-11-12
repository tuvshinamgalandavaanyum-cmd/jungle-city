import random

import aiohttp
import discord
from discord.ext import commands

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
EMOTE_GROUPS = [
    ("romance", "💞", "Romance", ROMANCE),
    ("fight", "⚔️", "Fight", FIGHT),
    ("laugh", "😂", "Laugh", LAUGH),
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


@commands.command(name="emote", aliases=["emotes", "emoji"])
async def emote_list(ctx: commands.Context, group: str = None):
    """Эможи жагсаалт: emote [romance | fight | laugh | 18]"""
    p = ctx.clean_prefix
    nsfw = getattr(ctx.channel, "is_nsfw", lambda: False)()
    q = (group or "").lower().lstrip("+")
    embed = discord.Embed(title="🎭 Эможи", color=0xEC4899)
    for key, emoji, title, lst in EMOTE_GROUPS:
        if q and q not in (key, title.lower().lstrip("+"), "18" if key == "adult" else key):
            continue
        if key == "adult" and not nsfw:
            embed.add_field(name=f"{emoji} {title} ({len(lst)})", value="Зөвхөн NSFW суваг дээр харагдана", inline=False)
            continue
        embed.add_field(name=f"{emoji} {title} ({len(lst)})", value=" · ".join(f"`{p}{e[0]}`" for e in lst), inline=False)
    embed.set_footer(text=f"{p}<эможи> @хүн")
    await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    for e in EMOTES:
        bot.add_command(make_emote(*e))
    bot.add_command(emote_list)
