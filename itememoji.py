"""Барааны emoji (дэлгүүр, цэс, pixel icon үүсгэхэд)."""

EMO = {
    # гэр ахуй
    "knife": "🔪", "spoon": "🥄", "fork": "🍴", "plate": "🍽️", "cup": "☕", "kettle": "🫖", "chair": "🪑", "table": "🛋️",
    "bed": "🛏️", "pillow": "🛌", "blanket": "🧣", "cabinet": "🗄️", "wardrobe": "🚪", "mirror": "🪞", "curtain": "🪟",
    "carpet": "🟫", "wall_clock": "🕰️", "picture_frame": "🖼️", "vase": "🏺", "lamp": "💡", "fridge": "🧊",
    "microwave": "📟", "stove": "🔥", "sink": "🚰", "soap": "🧼", "towel": "🧻", "toothbrush": "🪥", "toothpaste": "🧴",
    "comb": "💇", "hairdryer": "💨", "ladle": "🥄", "pot": "🍲", "frying_pan": "🍳", "trash_can": "🗑️", "keys": "🔑",
    "wallet": "👛", "book": "📖", "notebook": "📓", "pen": "🖊️", "pencil": "✏️", "bag": "👜", "clothes": "👕",
    "shoes": "👟", "socks": "🧦", "scissors": "✂️", "tape": "📎", "medicine": "💊", "thermos": "🍶", "water_bottle": "🧴",
    "perfume": "🧪", "wristwatch": "⌚", "glasses": "👓", "mask": "😷", "flashlight": "🔦", "broom": "🧹", "cap": "🧢",
    "gloves": "🧤", "belt": "➰", "toy": "🧸", "chess": "♟️", "playing_cards": "🃏", "magazine": "📰", "map": "🗺️",
    "binoculars": "🔭", "sewing_kit": "🧵", "clothes_iron": "♨️", "vacuum_cleaner": "🧽", "bedspread": "🛏️",
    "napkin": "🧻", "dish_soap": "🫧", "sponge": "🧽", "cardboard_box": "📦", "tray": "🥡", "jar": "🫙", "bottle": "🍾",
    "glass": "🥛", "gift_box": "🎁", "candle": "🕯️", "matches": "🔥", "lighter": "🔥", "hammer": "🔨", "rope": "🪢",
    "ruler": "📏", "plant": "🪴", "flower_pot": "🌷", "paint": "🎨", "newspaper": "🗞️", "photo_album": "📔",
    "piggy_bank": "🐷", "umbrella": "☂️", "lock": "🔒", "diary": "📒", "needle": "📌",
    # дижитал
    "battery": "🔋", "charger": "🔌", "calculator": "🧮", "nokia": "📞", "router": "📡", "headphones": "🎧",
    "speaker": "🔊", "smartwatch": "⌚", "phone": "📱", "tv": "📺", "tablet": "📲", "computer": "🖥️", "camera": "📷",
    "console": "🎮", "laptop": "💻", "drone": "🛸",
    # үнэт эдлэл, металл
    "ring": "💍", "watch": "🕐", "necklace": "📿", "crystal": "🔮", "gem": "💎", "gold_coin": "🪙",
    "iron": "🔩", "copper": "🟠", "bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "⬜", "diamond": "💠",
    "uranium": "☢️", "gold_ore": "🪨",
    # хоол
    "candy": "🍬", "cookie": "🍪", "chips": "🍟", "milk_tea": "🍵", "bread": "🍞", "noodles": "🍜", "bansh": "🥟",
    "buuz": "🥟", "khuushuur": "🥮", "tsuivan": "🍝", "soup": "🍲", "khorkhog": "🍖", "steak": "🥩", "boodog": "🍗",
    "feast": "🍱",
    # байшин
    "ger": "🛖", "hut": "🏠", "flat": "🏢", "yard": "🏡", "town": "🏘️", "cottage": "🏚️", "villa": "🏛️", "mansion": "🏰",
    # хайрцаг, хэрэгсэл
    "box": "📦", "case": "💼", "chest": "🧰", "shield": "🛡️", "luck_potion": "🍀", "money_potion": "💰", "revive": "💖",
}

# pixel icon: (emoji, өнгө | None). Өнгө өгвөл emoji-г тэр өнгөөр будна.
_GEM = "💎"
ICON_TINT = {
    # металл (ингот хэлбэр)
    "lead": ("INGOT", "#6b7280"), "tin": ("INGOT", "#cbd5e1"), "zinc": ("INGOT", "#94a3b8"), "aluminium": ("INGOT", "#d1d5db"),
    "nickel": ("INGOT", "#a8a29e"), "brass": ("INGOT", "#d4a017"), "steel": ("INGOT", "#64748b"), "chrome": ("INGOT", "#e5e7eb"),
    "cobalt": ("INGOT", "#2563eb"), "titanium": ("INGOT", "#9ca3af"), "tungsten": ("INGOT", "#475569"),
    "palladium": ("INGOT", "#e2e8f0"), "rhodium": ("INGOT", "#f0abfc"), "iridium": ("INGOT", "#67e8f9"),
    # үнэт эдлэл
    "silver_ring": ("💍", "#cbd5e1"), "earrings": ("🔔", "#facc15"), "bracelet": ("📿", "#facc15"),
    "pearl": ("🦪", None), "amber": (_GEM, "#f59e0b"), "coral": ("🪸", None), "turquoise": (_GEM, "#2dd4bf"),
    "jade": (_GEM, "#22c55e"), "amethyst": (_GEM, "#a855f7"), "topaz": (_GEM, "#fde047"), "opal": (_GEM, "#e0e7ff"),
    "gold_chain": ("⛓️", "#facc15"), "emerald": (_GEM, "#16a34a"), "sapphire": (_GEM, "#2563eb"),
    "ruby": (_GEM, "#dc2626"), "brooch": ("🎖️", "#facc15"), "diamond_ring": ("💍", None),
    "tiara": ("👑", "#f9a8d4"), "crown": ("👑", None), "scepter": ("🔱", "#facc15"),
    # хайрцаг
    "coin_case": ("👛", "#facc15"), "silver_case": ("💼", "#cbd5e1"), "gold_case": ("💼", "#facc15"),
    "diamond_case": ("💼", "#22d3ee"), "kitchen_box": ("📦", "#fb923c"), "tech_box": ("📦", "#3b82f6"),
    "food_box": ("🍱", None), "style_box": ("🎁", "#f472b6"), "lucky_box": ("🎁", "#22c55e"),
    "metal_crate": ("🧰", "#6b7280"), "jewel_box": ("🎁", "#a855f7"), "premium_box": ("🎁", "#facc15"),
    "royal_chest": ("🧰", "#facc15"),
    # хэрэгсэл
    "shield_lite": ("🛡️", "#22c55e"), "shield_pro": ("🛡️", "#3b82f6"), "shield_max": ("🛡️", "#a855f7"),
    "luck_potion_x": ("🍀", "#16a34a"), "money_potion_x": ("💰", "#eab308"), "protein": ("🥤", None),
    "energy_bar": ("🍫", None), "bail_pass": ("🎫", None), "meal_voucher": ("🎟️", None),
    "scratch_card": ("🎴", None), "lotto_ticket": ("🎰", None),
}
