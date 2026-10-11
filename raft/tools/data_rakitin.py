"""Data bersama untuk generator addon Rakitin.

Semua definisi item, blok, dan resep ada di sini supaya file JSON addon,
gambar resep, dan daftar resep di dokumentasi selalu sinkron.
"""

NS = "rakit"

# ---------------------------------------------------------------------------
# Item custom
# ---------------------------------------------------------------------------
# kunci: id, nama, kategori menu, stack, komponen tambahan (opsional)
ITEMS = [
    dict(id="plastik", nama="Plastik", kategori="items"),
    dict(id="daun_palem", nama="Daun Palem", kategori="nature"),
    dict(id="besi_tua", nama="Besi Tua", kategori="items"),
    dict(id="gigi_hiu", nama="Gigi Hiu", kategori="items"),
    dict(
        id="daging_hiu_mentah",
        nama="Daging Hiu Mentah",
        kategori="items",
        komponen={
            "minecraft:food": {"nutrition": 3, "saturation_modifier": 0.3},
            "minecraft:use_animation": "eat",
            "minecraft:use_modifiers": {"use_duration": 1.6, "movement_modifier": 0.35},
        },
    ),
    dict(
        id="daging_hiu_matang",
        nama="Daging Hiu Matang",
        kategori="items",
        komponen={
            "minecraft:food": {"nutrition": 8, "saturation_modifier": 0.8},
            "minecraft:use_animation": "eat",
            "minecraft:use_modifiers": {"use_duration": 1.6, "movement_modifier": 0.35},
        },
    ),
    dict(
        id="botol_kosong",
        nama="Botol Kosong",
        kategori="items",
        stack=16,
        komponen={"rakit:botol_kosong": {}},
    ),
    dict(
        id="air_laut",
        nama="Botol Air Laut",
        kategori="items",
        stack=16,
        komponen={
            "minecraft:food": {
                "nutrition": 0,
                "saturation_modifier": 0,
                "can_always_eat": True,
                "using_converts_to": "rakit:botol_kosong",
            },
            "minecraft:use_animation": "drink",
            "minecraft:use_modifiers": {"use_duration": 1.6, "movement_modifier": 0.35},
            "rakit:minuman": {"haus": 3, "asin": True},
        },
    ),
    dict(
        id="air_bersih",
        nama="Botol Air Bersih",
        kategori="items",
        stack=16,
        komponen={
            "minecraft:food": {
                "nutrition": 0,
                "saturation_modifier": 0,
                "can_always_eat": True,
                "using_converts_to": "rakit:botol_kosong",
            },
            "minecraft:use_animation": "drink",
            "minecraft:use_modifiers": {"use_duration": 1.6, "movement_modifier": 0.35},
            "rakit:minuman": {"haus": 8, "asin": False},
        },
    ),
    dict(
        id="tombak",
        nama="Tombak",
        kategori="equipment",
        stack=1,
        komponen={
            "minecraft:hand_equipped": True,
            "minecraft:damage": 6,
            "minecraft:durability": {"max_durability": 300},
            "minecraft:enchantable": {"slot": "sword", "value": 10},
            "rakit:tombak": {"bonus_hiu": 6},
        },
    ),
    dict(
        id="buku_catatan",
        nama="Buku Catatan Rakit",
        kategori="items",
        stack=1,
        komponen={"rakit:buku": {}},
    ),
    dict(
        id="pecahan_portal",
        nama="Pecahan Portal",
        kategori="items",
        komponen={"minecraft:rarity": "rare", "minecraft:glint": True},
    ),
    dict(
        id="inti_portal",
        nama="Inti Portal End",
        kategori="items",
        stack=1,
        komponen={"minecraft:rarity": "epic", "minecraft:glint": True, "rakit:inti_portal": {}},
    ),
]

TIER_KAIL = [
    # tier, nama pendek, warna format Minecraft
    (1, "Kayu", "§f"),
    (2, "Besi", "§7"),
    (3, "Emas", "§e"),
    (4, "Berlian", "§b"),
    (5, "Netherite", "§d"),
]

for tier, nama, _warna in TIER_KAIL:
    ITEMS.append(
        dict(
            id=f"kail_t{tier}",
            nama=f"Kail {nama} (Tier {tier})",
            kategori="equipment",
            stack=1,
            komponen={
                "minecraft:hand_equipped": True,
                "minecraft:glint": True,
                "rakit:kail": {"tier": tier},
            },
        )
    )

# ---------------------------------------------------------------------------
# Blok custom
# ---------------------------------------------------------------------------
BLOK_NAMA = {
    "fondasi_rakit": "Fondasi Rakit",
    "fondasi_kuat": "Fondasi Diperkuat",
    "penyaring_air": "Penyaring Air",
    "penampung_hujan": "Penampung Air Hujan",
    "pot_tanam": "Pot Tanam",
    "layar": "Layar",
    "kemudi": "Kemudi",
}

# ---------------------------------------------------------------------------
# Resep
# ---------------------------------------------------------------------------
# Bahan ditulis sebagai id item; "tag:..." berarti tag item (misal semua papan).
PAPAN = "tag:minecraft:planks"

RESEP = [
    dict(
        id="fondasi_rakit", judul="Fondasi Rakit", tipe="shaped",
        pola=["PP", "KK"], kunci={"P": PAPAN, "K": "rakit:plastik"},
        hasil="rakit:fondasi_rakit", jumlah=2,
        catatan="Lantai rakit. Klik kanan ke permukaan air untuk memasangnya langsung di laut.",
    ),
    dict(
        id="fondasi_kuat", judul="Fondasi Diperkuat", tipe="shapeless",
        bahan=["rakit:fondasi_rakit", "rakit:besi_tua"],
        hasil="rakit:fondasi_kuat", jumlah=1,
        catatan="Tidak bisa digigit hiu.",
    ),
    dict(
        id="penyaring_air", judul="Penyaring Air", tipe="shaped",
        pola=["KBK", "P P", "PPP"],
        kunci={"K": "rakit:plastik", "B": "rakit:botol_kosong", "P": PAPAN},
        hasil="rakit:penyaring_air", jumlah=1,
        catatan="Masukkan Botol Air Laut, tunggu ±30 detik, ambil Air Bersih dengan Botol Kosong.",
    ),
    dict(
        id="penampung_hujan", judul="Penampung Air Hujan", tipe="shaped",
        pola=["K K", "K K", "PPP"], kunci={"K": "rakit:plastik", "P": PAPAN},
        hasil="rakit:penampung_hujan", jumlah=1,
        catatan="Terisi air bersih saat hujan (harus di bawah langit terbuka).",
    ),
    dict(
        id="pot_tanam", judul="Pot Tanam", tipe="shaped",
        pola=["P P", "PDP"], kunci={"P": PAPAN, "D": "minecraft:dirt"},
        hasil="rakit:pot_tanam", jumlah=1,
        catatan="Tanam bibit gandum, kentang, wortel, atau bit. Bisa dipupuk dengan Bone Meal.",
    ),
    dict(
        id="layar", judul="Layar", tipe="shaped",
        pola=["DSD", "DTD", " T "],
        kunci={"D": "rakit:daun_palem", "S": "minecraft:string", "T": "minecraft:stick"},
        hasil="rakit:layar", jumlah=1,
        catatan="Pasang di atas rakit. Makin banyak layar, makin cepat rakit berlayar (maks 3).",
    ),
    dict(
        id="kemudi", judul="Kemudi", tipe="shaped",
        pola=["TPT", "PBP", "TPT"],
        kunci={"T": "minecraft:stick", "P": PAPAN, "B": "rakit:besi_tua"},
        hasil="rakit:kemudi", jumlah=1,
        catatan="Pasang di atas rakit, lalu klik kanan untuk mulai/berhenti berlayar ke arah pandanganmu.",
    ),
    dict(
        id="botol_kosong_plastik", judul="Botol Kosong (Plastik)", tipe="shaped",
        pola=["K K", " K "], kunci={"K": "rakit:plastik"},
        hasil="rakit:botol_kosong", jumlah=2,
        catatan="Klik kanan ke air laut untuk mengisi Botol Air Laut.",
    ),
    dict(
        id="botol_kosong_kaca", judul="Botol Kosong (Kaca)", tipe="shapeless",
        bahan=["minecraft:glass_bottle"],
        hasil="rakit:botol_kosong", jumlah=1,
        catatan="Mengubah botol kaca vanilla menjadi botol Rakitin.",
    ),
    dict(
        id="tombak", judul="Tombak", tipe="shaped",
        pola=["  B", " T ", "T  "], kunci={"B": "rakit:besi_tua", "T": "minecraft:stick"},
        hasil="rakit:tombak", jumlah=1,
        catatan="Senjata anti-hiu: +6 damage tambahan ke hiu.",
    ),
    dict(
        id="buku_catatan", judul="Buku Catatan Rakit", tipe="shapeless",
        bahan=["rakit:daun_palem", "rakit:daun_palem", "minecraft:string"],
        hasil="rakit:buku_catatan", jumlah=1,
        catatan="Klik kanan untuk melihat statistik, pencapaian, dan panduan.",
    ),
    dict(
        id="tali_daun", judul="Tali dari Daun", tipe="shapeless",
        bahan=["rakit:daun_palem", "rakit:daun_palem"],
        hasil="minecraft:string", jumlah=1,
        catatan="Sumber benang di tengah laut.",
    ),
    dict(
        id="tanah_kompos", judul="Tanah Kompos", tipe="shaped",
        pola=["DD", "DD"], kunci={"D": "rakit:daun_palem"},
        hasil="minecraft:dirt", jumlah=1,
        catatan="Sumber tanah untuk Pot Tanam dan menanam pohon.",
    ),
    dict(
        id="kail_t1", judul="Kail Kayu (Tier 1)", tipe="shapeless",
        bahan=["minecraft:fishing_rod", "rakit:plastik"],
        hasil="rakit:kail_t1", jumlah=1,
        catatan="Kail awal. Klik kanan item kail untuk mengaktifkannya (enchant maksimal).",
    ),
    dict(
        id="kail_t2", judul="Kail Besi (Tier 2)", tipe="shaped",
        pola=["IPI", "PKP", "IPI"],
        kunci={"I": "minecraft:iron_ingot", "P": "rakit:plastik", "K": "rakit:kail_t1"},
        hasil="rakit:kail_t2", jumlah=1,
        catatan="Upgrade dari Tier 1.",
    ),
    dict(
        id="kail_t3", judul="Kail Emas (Tier 3)", tipe="shaped",
        pola=["GTG", "SKS", "GTG"],
        kunci={"G": "minecraft:gold_ingot", "T": "rakit:gigi_hiu", "S": "minecraft:string", "K": "rakit:kail_t2"},
        hasil="rakit:kail_t3", jumlah=1,
        catatan="Upgrade dari Tier 2. Gigi Hiu didapat dari mengalahkan hiu.",
    ),
    dict(
        id="kail_t4", judul="Kail Berlian (Tier 4)", tipe="shaped",
        pola=["GDG", "TKT", "GDG"],
        kunci={"G": "minecraft:gold_ingot", "D": "minecraft:diamond", "T": "rakit:gigi_hiu", "K": "rakit:kail_t3"},
        hasil="rakit:kail_t4", jumlah=1,
        catatan="Upgrade dari Tier 3.",
    ),
    dict(
        id="kail_t5", judul="Kail Netherite (Tier 5)", tipe="shaped",
        pola=["TNT", "DKD", "T T"],
        kunci={"T": "rakit:gigi_hiu", "N": "minecraft:netherite_scrap", "D": "minecraft:diamond", "K": "rakit:kail_t4"},
        hasil="rakit:kail_t5", jumlah=1,
        catatan="Tier tertinggi. Bisa memancing Pecahan Portal.",
    ),
    dict(
        id="inti_portal", judul="Inti Portal End", tipe="shaped",
        pola=["PPP", "PEP", "PPP"],
        kunci={"P": "rakit:pecahan_portal", "E": "minecraft:ender_eye"},
        hasil="rakit:inti_portal", jumlah=1,
        catatan="Klik kanan di atas rakit untuk membangun Portal End yang langsung aktif.",
    ),
]

RESEP_TUNGKU = [
    dict(
        id="masak_daging_hiu", judul="Daging Hiu Matang",
        masuk="rakit:daging_hiu_mentah", hasil="rakit:daging_hiu_matang",
        tag=["furnace", "smoker", "campfire", "soul_campfire"],
        catatan="Masak di Tungku, Smoker, atau Api Unggun.",
    ),
    dict(
        id="rebus_air_laut", judul="Rebus Air Laut",
        masuk="rakit:air_laut", hasil="rakit:air_bersih",
        tag=["furnace", "campfire", "soul_campfire"],
        catatan="Merebus air laut menjadi air bersih di Tungku atau Api Unggun.",
    ),
    dict(
        id="lebur_besi_tua", judul="Lebur Besi Tua",
        masuk="rakit:besi_tua", hasil="minecraft:iron_ingot",
        tag=["furnace", "blast_furnace"],
        catatan="Mengubah Besi Tua menjadi Batangan Besi.",
    ),
]

# Nama tampilan untuk bahan vanilla (dipakai di dokumentasi resep).
NAMA_VANILLA = {
    PAPAN: "Papan Kayu (jenis apa saja)",
    "minecraft:string": "Benang",
    "minecraft:stick": "Tongkat",
    "minecraft:dirt": "Tanah",
    "minecraft:iron_ingot": "Batangan Besi",
    "minecraft:gold_ingot": "Batangan Emas",
    "minecraft:diamond": "Berlian",
    "minecraft:netherite_scrap": "Serpihan Netherite",
    "minecraft:fishing_rod": "Pancingan",
    "minecraft:glass_bottle": "Botol Kaca",
    "minecraft:ender_eye": "Mata Ender",
}


def nama_item(item_id):
    """Nama tampilan sebuah item (custom atau vanilla)."""
    if item_id in NAMA_VANILLA:
        return NAMA_VANILLA[item_id]
    if item_id.startswith(NS + ":"):
        kunci = item_id.split(":", 1)[1]
        for it in ITEMS:
            if it["id"] == kunci:
                return it["nama"]
        if kunci in BLOK_NAMA:
            return BLOK_NAMA[kunci]
    raise KeyError(item_id)
