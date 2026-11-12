"""Худалдан авалтын нийтлэг логик (команд ба цэснээс хоёуланд нь ашиглана)."""
import asyncio
import io

import discord

from carart import render_car
from itemart import icon_png
from itemart import item_png
from items import get_pet
from utils import fmt, shop_day


async def car_file(item, animated: bool = True, name: str = "car") -> discord.File:
    data, ext = await asyncio.to_thread(render_car, item.key, item.level, item.price, animated)
    return discord.File(io.BytesIO(data), filename=f"{name}.{ext}")


def icon_file(key: str, name: str = "icon"):
    data = item_png(key)
    return discord.File(io.BytesIO(data), filename=f"{name}.png") if data else None


async def purchase(bot, user_id: int, item, n: int = 1):
    """-> (алдаа | None, embed | None, file | None)"""
    db = bot.db
    if item.kind == "realty":
        return "🏘️ Байшинг `buy <ID>` командаар авна.", None, None
    if item.kind == "car":
        if await db.item_qty(user_id, item.key) > 0:
            return f"🚗 Танд аль хэдийн **{item.name}** байна.", None, None
        n = 1
    day = shop_day()
    reserved = False
    if item.stock is not None:
        sold = (await db.shop_sold(day)).get(item.key, 0)
        left = max(0, item.stock - sold)
        if left < n or not await db.buy_stock(item.key, day, n, item.stock):
            msg = "[ДУУССАН] Өнөөдрийн нөөц дууссан." if left == 0 else f"Нөөц хүрэлцэхгүй, үлдсэн: {left}."
            return f"❌ {item.name}: {msg} Нөөц шөнө дундад шинэчлэгдэнэ.", None, None
        reserved = True
    total = item.price * n
    if not await db.spend(user_id, total):
        if reserved:
            await db.release_stock(item.key, day, n)
        return f"❌ Мөнгө хүрэлцэхгүй байна. Нийт **{fmt(total)}** шаардлагатай.", None, None
    await db.add_item(user_id, item.key, n)
    await db.log_purchase(user_id, item.key, item.price, n, "shop")

    embed = discord.Embed(title="🛒 Худалдан авалт амжилттай", color=0x22C55E)
    embed.add_field(name="Бараа", value=f"{item.emoji} **{item.name}** × {n}", inline=True)
    embed.add_field(name="💸 Төлсөн", value=fmt(total), inline=True)
    file = None
    if item.kind == "car":
        file = await car_file(item, True, "car")
        embed.description = f"🎉 {item.desc}\nАжлын цалин **+{round(item.bonus * 100, 1)}%**"
        embed.set_image(url=f"attachment://{file.filename}")
    else:
        file = icon_file(item.key, "icon")
        if file is not None:
            embed.set_thumbnail(url="attachment://icon.png")
    if item.kind == "food":
        embed.add_field(name="⭐", value="⭐" * item.stars or "—", inline=True)
    elif item.kind == "clothes":
        embed.set_footer(text="Өмсөх: wear <ID> эсвэл шкафнаас сонгоно")
    elif item.key == "wardrobe":
        embed.set_footer(text="Шкафаа гэртээ байрлуулаад `wardrobe` гэж нээнэ")
    return None, embed, file
