"""qinv: 3 хэсэгтэй цүнх — Гэр (home), Халаас (halaas), Машин (mashin)."""
import discord

from houses import get_house, house_rooms
from items import ITEMS, get_item
from purchase import car_file
from ui import OwnerView, nav_button
from utils import fmt


async def owns(db, user_id: int, key: str) -> bool:
    """Цүнхэнд эсвэл байшинд (байрлуулсан) байгаа эсэх. Nokia бол утас гэж тооцогдоно."""
    keys = ("phone", "nokia") if key == "phone" else (key,)
    for k in keys:
        if await db.item_qty(user_id, k) > 0:
            return True
    key = keys[0]
    return any(r["item_key"] == key for r in await db.get_house_items(user_id))


async def placed(db, user_id: int, key: str) -> bool:
    """Байшинд байрлуулсан эсэх (шкаф, хөргөгч, компьютер)."""
    return any(r["item_key"] == key for r in await db.get_house_items(user_id))


def is_home_item(it) -> bool:
    return it is not None and it.placeable and it.kind in ("house", "digital")


class InvView(OwnerView):
    TABS = [("home", "🏠 Гэр"), ("pocket", "🎒 Халаас"), ("car", "🚗 Машин")]

    def __init__(self, cog, ctx, tab="home"):
        super().__init__(ctx.author.id, timeout=240)
        self.cog, self.ctx, self.tab = cog, ctx, tab
        self.selected = None  # байрлуулах бараа
        self.msg = ""
        self.extra = []

    # ---------- өгөгдөл ----------
    async def _data(self):
        db = self.cog.bot.db
        inv = {r["item_key"]: r["qty"] for r in await db.get_inventory(self.owner_id)}
        user = await db.get_user(self.owner_id)
        return inv, user

    def _tabs(self):
        for key, label in self.TABS:
            b = nav_button(
                label, self._tab_cb(key),
                discord.ButtonStyle.primary if key == self.tab else discord.ButtonStyle.secondary,
            )
            self.add_item(b)

    def _tab_cb(self, key):
        async def cb(interaction):
            self.tab = key
            self.selected = None
            self.msg = ""
            await self.refresh(interaction)
        return cb

    async def build(self) -> discord.Embed:
        db = self.cog.bot.db
        p = self.ctx.clean_prefix
        for c in list(self.children):
            self.remove_item(c)
        self._tabs()
        inv, user = await self._data()
        embed = discord.Embed(color=0x8B5CF6)
        if self.tab == "home":
            house = get_house(user["house"])
            embed.title = "🎒 Цүнх · 🏠 Гэр"
            unplaced = [(get_item(k), q) for k, q in inv.items() if is_home_item(get_item(k))]
            unplaced = [(i, q) for i, q in unplaced if i]
            rows = await db.get_house_items(self.owner_id)
            if house is None:
                embed.description = f"🏚️ Танд байшин алга. `{p}shop house` дээрээс авна уу."
            by_room = {}
            for r in rows:
                it = ITEMS.get(r["item_key"])
                if it:
                    by_room.setdefault(r["room"], []).append(f"{it.emoji} {it.name} ×{r['qty']}")
            if house:
                for rk, emoji, name in house_rooms(house):
                    lst = by_room.get(rk, [])
                    embed.add_field(name=f"{emoji} {name} ({sum(r['qty'] for r in rows if r['room'] == rk)}/{house.slots})",
                                    value="\n".join(lst[:10]) or "—", inline=True)
            if unplaced:
                embed.add_field(
                    name="📦 Байрлуулаагүй тавилга",
                    value="\n".join(f"{i.emoji} {i.name} ×{q}" for i, q in unplaced[:20]),
                    inline=False,
                )
                opts = [discord.SelectOption(label=i.name[:100], value=i.key, emoji=i.emoji,
                                             default=self.selected == i.key) for i, _ in unplaced[:25]]
                sel = discord.ui.Select(placeholder="1️⃣ Байрлуулах тавилгаа сонгоно уу", options=opts, row=1)
                sel.callback = self._on_item(sel)
                self.add_item(sel)
                if house and self.selected:
                    ropts = [discord.SelectOption(label=name, value=rk, emoji=emoji)
                             for rk, emoji, name in house_rooms(house)]
                    rs = discord.ui.Select(placeholder="2️⃣ Аль өрөөнд тавих вэ?", options=ropts, row=2)
                    rs.callback = self._on_room(rs, house)
                    self.add_item(rs)
            elif house:
                embed.add_field(name="📦 Байрлуулаагүй тавилга", value=f"Алга · `{p}shop home`", inline=False)
        elif self.tab == "pocket":
            embed.title = "🎒 Цүнх · Халаас"
            groups = {}
            total = 0
            for k, q in inv.items():
                it = get_item(k)
                if not it or is_home_item(it) or it.kind in ("car", "realty"):
                    continue
                total += it.sell_price * q
                groups.setdefault(it.kind, []).append(f"{it.emoji} **{it.name}** ×{q} · `{it.key}`")
            titles = {"food": "🍞 Хүнс", "tool": "🛡️ Хэрэгсэл", "box": "🎁 Хайрцаг", "clothes": "👕 Хувцас",
                      "digital": "📱 Дижитал", "jewel": "💎 Үнэт эдлэл", "metal": "⛏️ Металл", "house": "🏠 Гэр ахуй"}
            if not groups:
                embed.description = f"Халаас хоосон. `{p}shop` эсвэл `{p}steal`."
            else:
                embed.description = f"Зарвал нийт: **{fmt(total)}**"
                for kind in titles:
                    lines = groups.get(kind)
                    if not lines:
                        continue
                    for i in range(0, len(lines), 10):
                        embed.add_field(name=titles[kind] if i == 0 else "​", value="\n".join(lines[i:i + 10])[:1024], inline=False)
            embed.set_footer(text=f"{p}inv use <ID> · {p}sell <ID> · {p}wardrobe (шкаф) · {p}fridge (хөргөгч)")
        else:
            embed.title = "🎒 Цүнх · 🚗 Машин"
            cars = [get_item(k) for k in inv if get_item(k) and get_item(k).kind == "car"]
            if not cars:
                embed.description = f"Машин алга. `{p}cars` эсвэл `{p}shop car`."
            else:
                cars.sort(key=lambda c: -c.level)
                embed.description = "\n".join(f"{c.emoji} **{c.name}** — Lv {c.level} · ажлын цалин +{round(c.bonus * 100, 1)}%" for c in cars[:20])
                opts = [discord.SelectOption(label=c.name[:100], value=c.key, emoji=c.emoji, description=c.desc[:100]) for c in cars[:25]]
                sel = discord.ui.Select(placeholder="Машинаа сонгоод GIF-ийг үзнэ", options=opts, row=1)
                sel.callback = self._on_car(sel)
                self.add_item(sel)
                embed.set_footer(text="Хамгийн өндөр түвшний машины бонус ажлын цалинд нэмэгдэнэ")
        if self.msg:
            embed.add_field(name="ℹ️", value=self.msg, inline=False)
        return embed

    # ---------- callbacks ----------
    def _on_item(self, sel):
        async def cb(interaction):
            self.selected = sel.values[0]
            self.msg = ""
            await self.refresh(interaction)
        return cb

    def _on_room(self, sel, house):
        async def cb(interaction):
            db = self.cog.bot.db
            it = get_item(self.selected)
            res = await db.place_item(self.owner_id, sel.values[0], self.selected, 1, house.slots)
            if res == "ok":
                self.msg = f"✅ {it.emoji} **{it.name}** байрлууллаа."
            elif res == "full":
                self.msg = "❌ Энэ өрөө дүүрсэн байна."
            else:
                self.msg = "❌ Тавилга олдсонгүй."
            self.selected = None
            await self.refresh(interaction)
        return cb

    def _on_car(self, sel):
        async def cb(interaction):
            await interaction.response.defer()
            it = get_item(sel.values[0])
            f = await car_file(it, True, "car")
            e = discord.Embed(title=f"{it.emoji} {it.name}", description=it.desc, color=0x22D3EE)
            e.set_image(url=f"attachment://{f.filename}")
            await interaction.followup.send(embed=e, file=f, ephemeral=True)
        return cb

    async def refresh(self, interaction):
        embed = await self.build()
        await interaction.response.edit_message(embed=embed, view=self)
