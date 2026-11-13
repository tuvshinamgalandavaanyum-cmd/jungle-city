from dataclasses import dataclass

# (ID, emoji, нэр)
ROOMS = [
    ("living", "🛋️", "Зочны өрөө"),
    ("bedroom", "🛏️", "Унтлагын өрөө"),
    ("kitchen", "🍳", "Гал тогоо"),
    ("bathroom", "🚿", "Угаалгын өрөө"),
    ("office", "💻", "Ажлын өрөө"),
]
ROOM_BY_KEY = {r[0]: r for r in ROOMS}

ROOM_ALIASES = {
    "living": ["living", "hall", "зочин", "зочны", "зал"],
    "bedroom": ["bedroom", "bed", "унтлага", "унтлагын", "унтах"],
    "kitchen": ["kitchen", "гал", "тогоо"],
    "bathroom": ["bathroom", "bath", "угаалга", "угаалгын"],
    "office": ["office", "work", "ажлын", "ажил"],
}


@dataclass(frozen=True)
class House:
    key: str
    emoji: str
    name: str
    price: int
    rooms: int  # хэдэн өрөөтэй вэ (ROOMS-ийн эхнээс)
    slots: int  # өрөө бүрт хэдэн эд зүйл байрлуулах вэ


# Хамгийн хямд нь 150,000₮, хамгийн үнэтэй нь 250,000,000₮ (28 байшин)
HOUSES = sorted([
    House("tent", "🏕️", "Майхан", 150_000, 1, 2),
    House("container", "🏗️", "Контейнер гэр", 300_000, 1, 3),
    House("ger", "🛖", "Хуучин гэр", 500_000, 1, 4),
    House("cabin", "🪵", "Модон байшин (Cabin)", 700_000, 2, 4),
    House("studio", "🏬", "Студи байр", 1_000_000, 2, 4),
    House("hut", "🏠", "Жижиг байшин", 1_200_000, 2, 5),
    House("loft", "🏙️", "Лофт", 1_800_000, 3, 5),
    House("flat", "🏢", "Орон сууц", 2_500_000, 3, 6),
    House("duplex", "🏣", "Дуплекс", 3_000_000, 3, 7),
    House("bungalow", "🏝️", "Бунгало", 3_500_000, 4, 6),
    House("yard", "🏡", "Хашаа байшин", 4_000_000, 4, 7),
    House("farmhouse", "🚜", "Ферм байшин", 4_800_000, 4, 9),
    House("town", "🏘️", "Таунхаус", 5_500_000, 5, 8),
    House("chalet", "🏔️", "Уулын шале", 6_000_000, 5, 9),
    House("cottage", "🏚️", "Коттедж", 7_000_000, 5, 10),
    House("townvilla", "🏤", "Хотын вилла", 7_800_000, 5, 11),
    House("villa", "🏛️", "Вилла", 8_500_000, 5, 12),
    House("lakehouse", "🏞️", "Нуурын эргийн байшин", 9_200_000, 5, 13),
    House("mansion", "🏰", "Харш", 10_000_000, 5, 15),
    House("penthouse", "🌆", "Пентхаус", 12_000_000, 5, 16),
    House("beachvilla", "🏖️", "Далайн эргийн вилла", 15_000_000, 5, 18),
    House("modern", "🏨", "Орчин үеийн харш", 18_000_000, 5, 20),
    House("castle", "🏯", "Цайз", 25_000_000, 5, 24),
    House("palace", "🕌", "Ордон", 40_000_000, 5, 28),
    House("tower", "🗼", "Хувийн цамхаг", 60_000_000, 5, 32),
    House("island", "🌴", "Хувийн арал", 80_000_000, 5, 36),
    House("yacht", "🛥️", "Тансаг усан онгоц", 120_000_000, 5, 40),
    House("space", "🚀", "Сансрын станц", 250_000_000, 5, 50),
], key=lambda h: h.price)
HOUSES_BY_KEY = {h.key: h for h in HOUSES}
HOUSE_SELL_RATE = 0.7  # байшин сайжруулахад хуучин байшингийн үнийн 70%-ийг буцаан тооцно

# ---------- сейф ----------
SAFE_PRICE_PER_LEVEL = 300_000
MAX_SAFE_LEVEL = 5
SAFE_MONEY_PER_LEVEL = 2_000_000
SAFE_SLOTS_PER_LEVEL = 20


def get_house(key: str | None) -> House | None:
    return HOUSES_BY_KEY.get(key) if key else None


def find_house(query: str) -> House | None:
    q = query.strip().casefold()
    for h in HOUSES:
        if q in (h.key, h.name.casefold()):
            return h
    for h in HOUSES:
        if h.key.startswith(q) or q in h.name.casefold():
            return h
    return None


def find_room(query: str) -> str | None:
    """'bedroom', 'унтлагын', 'bed' гэх мэтээс өрөөний ID олно."""
    q = query.strip().casefold()
    if not q:
        return None
    for key, aliases in ROOM_ALIASES.items():
        if q == key or q in aliases:
            return key
    for key, aliases in ROOM_ALIASES.items():
        if any(a.startswith(q) or q.startswith(a) for a in aliases):
            return key
    return None


def house_rooms(house: House):
    return ROOMS[: house.rooms]


def comfort_pct(total_value: int) -> int:
    """Байрлуулсан эд зүйлсийн нийт үнэ 100,000₮ тутамд ажлын орлого +1% (дээд тал нь +10%)."""
    return min(10, total_value // 100_000)


def safe_money_cap(level: int) -> int:
    return SAFE_MONEY_PER_LEVEL * level


def safe_slot_cap(level: int) -> int:
    return SAFE_SLOTS_PER_LEVEL * level


def safe_next_price(level: int) -> int | None:
    if level >= MAX_SAFE_LEVEL:
        return None
    return SAFE_PRICE_PER_LEVEL * (level + 1)
