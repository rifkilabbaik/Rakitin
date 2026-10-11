"""Generator aset visual Torch Detektor: ikon item Obor Detektor, tekstur
partikel outline, ikon pack, gambar resep, dan legenda warna ore.

Semua gambar dibuat secara prosedural (pixel art) supaya addon tidak memakai
aset milik Mojang. Jalankan dari folder mana saja:
    python3 Torch_Detektor/tools/buat_aset.py
Butuh paket: pip install pillow
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BP = os.path.join(ROOT, "TorchDetektor_BP")
XRAY = os.path.join(ROOT, "TorchDetektor_XRay_BP")
RP = os.path.join(ROOT, "TorchDetektor_RP")
DOCS = os.path.join(ROOT, "docs")

# Sama dengan tabel ORE di TorchDetektor_BP/scripts/config.js (urutan = prioritas HUD).
# (kunci, nama, warna outline, warna bintik bijih di tekstur, batuan dasar)
ORE = [
    ("berlian", "Berlian", "#4EE2EC", "#4EE2EC", "batu"),
    ("zamrud", "Zamrud", "#17DD62", "#17DD62", "batu"),
    ("emas", "Emas", "#FCEE4B", "#FCEE4B", "batu"),
    ("besi", "Besi", "#D8AF93", "#D8AF93", "batu"),
    ("tembaga", "Tembaga", "#E0734A", "#E0734A", "batu"),
    ("redstone", "Redstone", "#FF2A2A", "#FF2A2A", "deepslate"),
    ("lapis", "Lapis", "#2F5BFF", "#2F5BFF", "deepslate"),
    ("batubara", "Batu Bara", "#5A5A5A", "#262626", "batu"),
    ("kuarsa", "Kuarsa", "#F2EDE6", "#F2EDE6", "netherrack"),
    ("debris", "Puing Kuno", "#A0674F", None, "debris"),
]

random.seed(20261011)


# ===========================================================================
# Alat gambar dasar (gaya sama dengan generator aset addon Rakitin)
# ===========================================================================
def hex2rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ubah(warna, f):
    """Terangkan (f > 1) atau gelapkan (f < 1) warna."""
    r, g, b, a = warna
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


def campur(w1, w2, t):
    """Campur dua warna RGBA (t=0 -> w1, t=1 -> w2)."""
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(w1, w2))


def kanvas(w=16, h=16, latar=(0, 0, 0, 0)):
    return Image.new("RGBA", (w, h), latar)


def px(img, x, y, warna):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), warna)


def simpan(img, *bagian):
    path = os.path.join(*bagian)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def muat_font(ukuran, tebal=False):
    kandidat = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if tebal else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if tebal else "DejaVuSans.ttf",
    ]
    for k in kandidat:
        try:
            return ImageFont.truetype(k, ukuran)
        except OSError:
            continue
    return ImageFont.load_default()


def teks_bayang(d, xy, teks, font, warna, bayang=(0, 0, 0, 200), geser=3):
    d.text((xy[0] + geser, xy[1] + geser), teks, font=font, fill=bayang)
    d.text(xy, teks, font=font, fill=warna)


# ===========================================================================
# Ikon item
# ===========================================================================
KAYU = hex2rgb("#8a5a2e")
KAYU_TERANG = hex2rgb("#b07a42")
KAYU_GELAP = hex2rgb("#5a3a1e")


def tongkat_obor(img, y0, y1):
    """Tongkat kayu tegak 2 piksel (x=7..8) dari y0 sampai y1."""
    for y in range(y0, y1 + 1):
        px(img, 7, y, ubah(KAYU_TERANG, 1 + random.uniform(-0.05, 0.05)))
        px(img, 8, y, ubah(KAYU, 1 + random.uniform(-0.05, 0.05)))
    px(img, 8, y1, KAYU_GELAP)


def ikon_obor_detektor():
    """Obor Detektor: tongkat kayu, cangkir kuningan berhias permata warna ore,
    api dengan inti kristal biru muda, dan gelombang deteksi di kiri-kanan api.
    Semua piksel padat (tanpa semi-transparan) supaya rapi saat dipegang."""
    img = kanvas()
    tongkat_obor(img, 9, 15)
    px(img, 7, 9, hex2rgb("#5a3a1e"))
    px(img, 8, 9, hex2rgb("#3e2814"))

    # Cangkir kuningan dengan 4 permata warna ore.
    for x in range(6, 10):
        px(img, x, 6, hex2rgb("#e8bd55"))
        px(img, x, 8, hex2rgb("#8a6420"))
    for x, w in zip(range(6, 10), ("#4EE2EC", "#17DD62", "#FCEE4B", "#FF2A2A")):
        px(img, x, 7, hex2rgb(w))

    # Api (tepi oranye, dasar kuning) dengan kristal pendeteksi di tengahnya.
    oranye, kuning = hex2rgb("#f28c28"), hex2rgb("#ffd54a")
    px(img, 8, 0, oranye)
    px(img, 7, 1, kuning)
    px(img, 8, 1, oranye)
    for y in range(2, 6):
        px(img, 6, y, oranye)
        px(img, 9, y, oranye)
    px(img, 7, 5, kuning)
    px(img, 8, 5, kuning)
    for x, y, w in ((7, 2, "#ffffff"), (8, 2, "#b5f8fb"), (7, 3, "#4EE2EC"), (8, 3, "#2cb8c4"), (7, 4, "#2cb8c4"), (8, 4, "#1b8a96")):
        px(img, x, y, hex2rgb(w))

    # Gelombang deteksi: busur dalam terang, busur luar lebih redup.
    dalam, luar = hex2rgb("#9ff6fa"), hex2rgb("#4f9fa8")
    for x, y in ((4, 2), (3, 3), (4, 4)):
        px(img, x, y, dalam)
        px(img, 15 - x, y, dalam)
    for x, y in ((2, 1), (1, 2), (1, 3), (1, 4), (2, 5)):
        px(img, x, y, luar)
        px(img, 15 - x, y, luar)
    return img


def ikon_obor_biasa():
    """Obor vanilla versi sederhana (hanya untuk gambar resep di dokumentasi)."""
    img = kanvas()
    tongkat_obor(img, 6, 15)
    px(img, 7, 5, hex2rgb("#3a2614"))
    px(img, 8, 5, hex2rgb("#2a1a0c"))
    px(img, 7, 4, hex2rgb("#ffd54a"))
    px(img, 8, 4, hex2rgb("#f28c28"))
    px(img, 7, 3, hex2rgb("#fff6c8"))
    px(img, 8, 3, hex2rgb("#ffd54a"))
    px(img, 7, 2, hex2rgb("#f28c28"))
    return img


def tex_garis():
    """Tekstur partikel outline: kotak berongga putih, tepi 1 piksel, dalam transparan.
    Diwarnai di game lewat particle_appearance_tinting (variable.warna)."""
    img = kanvas()
    putih = (255, 255, 255, 255)
    for i in range(16):
        px(img, i, 0, putih)
        px(img, i, 15, putih)
        px(img, 0, i, putih)
        px(img, 15, i, putih)
    return img


# ===========================================================================
# Tekstur batuan & ore (untuk ikon pack dan legenda)
# ===========================================================================
BATUAN = {
    "batu": (hex2rgb("#7f7f7f"), hex2rgb("#686868"), hex2rgb("#959595")),
    "deepslate": (hex2rgb("#50505a"), hex2rgb("#3b3b44"), hex2rgb("#62626c")),
    "netherrack": (hex2rgb("#6e2a2a"), hex2rgb("#521c1c"), hex2rgb("#87393a")),
}


def isi_batuan(img, jenis, x0=0, y0=0, n=16):
    dasar, gelap, terang = BATUAN[jenis]
    for y in range(n):
        for x in range(n):
            r = random.random()
            if jenis == "deepslate":
                garis = (y + (x // 5)) % 4 == 0
                w = gelap if garis and r < 0.7 else (terang if r < 0.12 else dasar)
            else:
                w = gelap if r < 0.22 else (terang if r < 0.36 else dasar)
            px(img, x0 + x, y0 + y, ubah(w, 1 + random.uniform(-0.04, 0.04)))


def tex_debris(n=16):
    """Puing kuno: cokelat tua dengan pola cincin konsentris."""
    img = kanvas(n, n)
    c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c) * 16 / n
            cincin = int(d * 1.1) % 3 == 0
            w = hex2rgb("#8a5a46") if cincin else hex2rgb("#5e3d31")
            px(img, x, y, ubah(w, 1 + random.uniform(-0.07, 0.07)))
    return img


def bintik_ore(img, warna, x0=0, y0=0, n=16, jumlah=None):
    """Gambar gugus bintik bijih (2x2 dengan sisi terang & gelap)."""
    jumlah = jumlah or (4 if n >= 16 else 2)
    w = hex2rgb(warna)
    pos = []
    percobaan = 0
    while len(pos) < jumlah and percobaan < 200:
        percobaan += 1
        x = random.randint(1, n - 3)
        y = random.randint(1, n - 3)
        if all(abs(x - a) > 2 or abs(y - b) > 2 for a, b in pos):
            pos.append((x, y))
    for x, y in pos:
        px(img, x0 + x, y0 + y, ubah(w, 1.25))
        px(img, x0 + x + 1, y0 + y, w)
        px(img, x0 + x, y0 + y + 1, w)
        px(img, x0 + x + 1, y0 + y + 1, ubah(w, 0.7))
        if n >= 16 and random.random() < 0.6:
            px(img, x0 + x + 2, y0 + y + 1, ubah(w, 0.85))


def tex_ore(kunci):
    _k, _nama, _garis, bintik, batuan = next(o for o in ORE if o[0] == kunci)
    if batuan == "debris":
        return tex_debris()
    img = kanvas()
    isi_batuan(img, batuan)
    bintik_ore(img, bintik)
    return img


def iso_blok(atas, samping, ukuran=16):
    """Render blok isometrik kecil (32x32) dari tekstur atas & samping."""
    n = 32
    img = kanvas(n, n)
    for y in range(n):
        for x in range(n):
            X = (x + 0.5 - n / 2) / (n / 2)
            Y = (y + 0.5) / (n / 2)
            u = (X + 2 * Y) / 2
            v = (2 * Y - X) / 2
            if 0 <= u < 1 and 0 <= v < 1:
                px(img, x, y, atas.getpixel((int(u * ukuran), int(v * ukuran))))
                continue
            if X < 0:
                s_ = X + 1
                t = Y - 0.5 - 0.5 * s_
                gelap = 0.82
            else:
                s_ = X
                t = Y - 1 + 0.5 * s_
                gelap = 0.65
            if 0 <= s_ < 1 and 0 <= t < 1:
                c = samping.getpixel((int(s_ * ukuran), int(t * ukuran)))
                px(img, x, y, ubah(c, gelap))
    return img


def garis_iso(img, warna, skala, tebal):
    """Gambar 9 rusuk kubus isometrik yang terlihat (koordinat dasar 32x32)."""
    d = ImageDraw.Draw(img)
    titik = {
        "a": (16, 0), "b": (32, 8), "c": (32, 24), "e": (16, 32), "f": (0, 24), "g": (0, 8), "m": (16, 16),
    }
    rusuk = ["ab", "bc", "ce", "ef", "fg", "ga", "mg", "mb", "me"]

    def skalakan(v):
        # Titik di tepi kanan/bawah digeser 1 piksel ke dalam supaya tidak terpotong.
        return min(v * skala, 32 * skala - 1)

    for r in rusuk:
        (x0, y0), (x1, y1) = titik[r[0]], titik[r[1]]
        d.line([(skalakan(x0), skalakan(y0)), (skalakan(x1), skalakan(y1))], fill=warna, width=tebal)


# ===========================================================================
# Pemandangan gua (ikon pack & banner)
# ===========================================================================
SEL = 8  # ukuran satu blok di kanvas kecil


def adegan(kolom, baris, obor, ore, mode="biasa", seed=1):
    """Dinding gua dari blok batu/deepslate dengan ore bergaris warna dan Obor
    Detektor yang menerangi sekitarnya.

    obor : (x, y) pusat obor dalam piksel kanvas kecil.
    ore  : daftar (kolom, baris, kunci_ore).
    mode : "biasa" (ore terlihat + outline) atau "xray" (ore tersembunyi di balik
           batu, hanya outline yang tampak menembus).
    """
    rnd_lama = random.getstate()
    random.seed(seed)
    w, h = kolom * SEL, baris * SEL
    img = kanvas(w, h, (0, 0, 0, 255))
    lapis_ore = kanvas(w, h)
    batas = [baris * 0.55 + 1.2 * math.sin(c * 1.3) for c in range(kolom)]
    for r in range(baris):
        for c in range(kolom):
            isi_batuan(img, "deepslate" if r >= batas[c] else "batu", c * SEL, r * SEL, SEL)
            # sambungan antar blok sedikit lebih gelap
            for i in range(SEL):
                for x, y in ((c * SEL + SEL - 1, r * SEL + i), (c * SEL + i, r * SEL + SEL - 1)):
                    px(img, x, y, ubah(img.getpixel((x, y)), 0.82))
    if mode == "biasa":
        for c, r, k in ore:
            data = next(o for o in ORE if o[0] == k)
            if data[4] == "debris":
                lapis_ore.alpha_composite(tex_debris(SEL), (c * SEL, r * SEL))
            else:
                bintik_ore(lapis_ore, data[3], c * SEL, r * SEL, SEL, jumlah=3)

    # Cahaya obor: makin jauh makin gelap, dekat obor agak hangat.
    # Bintik ore diberi batas terang minimum supaya tetap terlihat di ikon.
    ox, oy = obor
    jari = max(w, h) * (0.6 if mode == "biasa" else 0.75)
    hangat = (255, 196, 120, 255) if mode == "biasa" else (196, 140, 255, 255)
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - ox, y + 0.5 - oy) / jari
            terang = max(0.3, min(1.12, 1.18 - d * 1.05))
            hangat_t = max(0.0, 0.25 - d * 0.6)
            c = campur(ubah(img.getpixel((x, y)), terang), hangat, hangat_t)
            o = lapis_ore.getpixel((x, y))
            if o[3]:
                c = ubah(o, max(terang, 0.8))
            px(img, x, y, c)

    # Outline ore (tidak terpengaruh cahaya, sama seperti partikel di game).
    for c, r, k in ore:
        warna = hex2rgb(next(o for o in ORE if o[0] == k)[2])
        x0, y0 = c * SEL, r * SEL
        if mode == "xray":
            img.alpha_composite(kanvas(SEL, SEL, warna[:3] + (70,)), (x0, y0))
        for i in range(SEL):
            for x, y in ((x0 + i, y0), (x0 + i, y0 + SEL - 1), (x0, y0 + i), (x0 + SEL - 1, y0 + i)):
                px(img, x, y, warna)

    # Obor Detektor (ikon item diperbesar 2x).
    ikon = ikon_obor_detektor().resize((32, 32), Image.NEAREST)
    img.alpha_composite(ikon, (int(ox - 16), int(oy - 14)))
    random.setstate(rnd_lama)
    return img


# Posisi ore untuk ikon pack (grid 8x8 blok, obor di tengah, pojok kanan bawah untuk label).
ORE_IKON = [
    (1, 1, "berlian"),
    (6, 1, "emas"),
    (1, 4, "zamrud"),
    (6, 4, "redstone"),
    (1, 6, "lapis"),
    (3, 6, "tembaga"),
]

GAYA_PACK = {
    # nama pack: (warna bingkai, label, mode)
    "bp": ("#f2a33a", "BP", "biasa"),
    "rp": ("#3fcf6a", "RP", "biasa"),
    "xray": ("#b45cff", "X-RAY", "xray"),
}


def ikon_pack(jenis):
    bingkai, label, mode = GAYA_PACK[jenis]
    kecil = adegan(8, 8, (32, 30), ORE_IKON, mode=mode, seed=7)
    img = kecil.resize((256, 256), Image.NEAREST)
    d = ImageDraw.Draw(img)
    # Bingkai tebal sesuai warna pack.
    d.rectangle([0, 0, 255, 255], outline=hex2rgb(bingkai), width=8)
    d.rectangle([8, 8, 247, 247], outline=(0, 0, 0, 160), width=2)
    # Label pack di pojok kanan bawah.
    font = muat_font(28 if len(label) > 2 else 40, tebal=True)
    bx = d.textbbox((0, 0), label, font=font)
    tw, th = bx[2] - bx[0], bx[3] - bx[1]
    x1, y1 = 256 - 16, 256 - 16
    x0, y0 = x1 - tw - 20, y1 - th - 18
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(20, 20, 24, 225), outline=hex2rgb(bingkai), width=3)
    d.text((x0 + 10 - bx[0], y0 + 9 - bx[1]), label, font=font, fill=hex2rgb(bingkai))
    return img


def font_muat_lebar(d, teks, lebar_maks, ukuran, tebal=True):
    """Kecilkan ukuran font sampai teks muat di lebar_maks piksel."""
    while ukuran > 10:
        font = muat_font(ukuran, tebal)
        bx = d.textbbox((0, 0), teks, font=font)
        if bx[2] - bx[0] <= lebar_maks:
            return font
        ukuran -= 2
    return muat_font(ukuran, tebal)


def banner():
    kolom, baris, skala = 20, 6, 8
    ore = [
        (1, 0, "berlian"), (0, 4, "redstone"), (5, 0, "zamrud"), (5, 4, "emas"), (9, 5, "lapis"),
        (12, 5, "besi"), (15, 5, "tembaga"), (18, 5, "batubara"), (11, 0, "kuarsa"), (16, 0, "debris"),
    ]
    kecil = adegan(kolom, baris, (24, 24), ore, seed=11)
    img = kecil.resize((kolom * SEL * skala, baris * SEL * skala), Image.NEAREST)
    # Kotak gelap di belakang judul supaya tulisan terbaca.
    x0, y0, x1, y1 = 400, 84, 1240, 300
    lapis = kanvas(img.width, img.height)
    ImageDraw.Draw(lapis).rounded_rectangle([x0, y0, x1, y1], radius=18, fill=(10, 10, 14, 185))
    img.alpha_composite(lapis)
    d = ImageDraw.Draw(img)
    judul = font_muat_lebar(d, "TORCH DETEKTOR", x1 - x0 - 64, 92)
    teks_bayang(d, (x0 + 32, y0 + 18), "TORCH DETEKTOR", judul, (255, 214, 102, 255), geser=5)
    sub = font_muat_lebar(d, "Obor di tangan kiri + beliung = ore di dekatmu bergaris warna", x1 - x0 - 64, 30, tebal=False)
    teks_bayang(d, (x0 + 34, y0 + 128), "Obor di tangan kiri + beliung = ore di dekatmu bergaris warna", sub, (240, 240, 240, 255), geser=2)
    teks_bayang(d, (x0 + 34, y0 + 170), "Addon Minecraft Bedrock 1.26", muat_font(24), (180, 180, 190, 255), geser=2)
    return img


# ===========================================================================
# Gambar resep untuk dokumentasi (gaya sama dengan gambar resep Rakitin)
# ===========================================================================
SKALA = 3
SLOT = 18 * SKALA
TEPI = 10


def gambar_slot(kanvas_, x, y, ukuran=SLOT):
    d = ImageDraw.Draw(kanvas_)
    d.rectangle([x, y, x + ukuran - 1, y + ukuran - 1], fill=(139, 139, 139, 255))
    d.line([(x, y), (x + ukuran - 1, y)], fill=(55, 55, 55, 255), width=SKALA)
    d.line([(x, y), (x, y + ukuran - 1)], fill=(55, 55, 55, 255), width=SKALA)
    d.line([(x, y + ukuran - 1), (x + ukuran - 1, y + ukuran - 1)], fill=(255, 255, 255, 255), width=SKALA)
    d.line([(x + ukuran - 1, y), (x + ukuran - 1, y + ukuran - 1)], fill=(255, 255, 255, 255), width=SKALA)


def tempel_ikon(kanvas_, ikon, x, y, ukuran=SLOT):
    target = 16 * SKALA
    besar = ikon.resize((target, target), Image.NEAREST)
    off = (ukuran - target) // 2
    kanvas_.alpha_composite(besar, (x + off, y + off))


def panah(kanvas_, x, y):
    d = ImageDraw.Draw(kanvas_)
    d.rectangle([x, y + 12, x + 30, y + 22], fill=(139, 139, 139, 255))
    d.polygon([(x + 30, y + 4), (x + 46, y + 17), (x + 30, y + 30)], fill=(139, 139, 139, 255))


def panel(w, h):
    img = Image.new("RGBA", (w, h), (198, 198, 198, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(0, 0, 0, 255), width=2)
    d.line([(2, 2), (w - 3, 2)], fill=(255, 255, 255, 255), width=3)
    d.line([(2, 2), (2, h - 3)], fill=(255, 255, 255, 255), width=3)
    d.line([(2, h - 3), (w - 3, h - 3)], fill=(85, 85, 85, 255), width=3)
    d.line([(w - 3, 2), (w - 3, h - 3)], fill=(85, 85, 85, 255), width=3)
    return img


def gambar_resep(bahan, hasil):
    """Resep tanpa pola dengan satu bahan: bahan digambar di slot tengah 3x3."""
    w = TEPI * 2 + SLOT * 3 + 70 + SLOT + 16
    h = TEPI * 2 + SLOT * 3
    img = panel(w, h)
    for j in range(3):
        for i in range(3):
            x, y = TEPI + i * SLOT, TEPI + j * SLOT
            gambar_slot(img, x, y)
            if (i, j) == (1, 1):
                tempel_ikon(img, bahan, x, y)
    ax = TEPI + SLOT * 3 + 12
    ay = TEPI + SLOT + (SLOT - 34) // 2
    panah(img, ax, ay)
    rx = ax + 58
    ry = TEPI + SLOT - 8
    gambar_slot(img, rx, ry, SLOT + 16)
    tempel_ikon(img, hasil, rx, ry, SLOT + 16)
    return img


# ===========================================================================
# Legenda warna outline ore
# ===========================================================================
def warna_teks(warna):
    """Pastikan teks berwarna gelap tetap terbaca di latar gelap."""
    r, g, b, a = warna
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return ubah(warna, 0.6 / lum) if lum < 0.4 else warna


def legenda_warna():
    kol, bar = 2, 5
    lebar_sel, tinggi_sel = 430, 118
    margin, judul_h = 24, 92
    w = margin * 2 + kol * lebar_sel + (kol - 1) * 16
    h = judul_h + bar * tinggi_sel + margin
    img = Image.new("RGBA", (w, h), (30, 30, 36, 255))
    d = ImageDraw.Draw(img)
    teks_bayang(d, (margin, 18), "Warna Outline Ore", muat_font(34, tebal=True), (255, 214, 102, 255), geser=2)
    d.text((margin, 60), "Warna garis di sekitar ore saat Obor Detektor aktif", font=muat_font(18), fill=(190, 190, 200, 255))
    f_nama, f_kode = muat_font(28, tebal=True), muat_font(20)
    for i, (kunci, nama, garis, _b, _batu) in enumerate(ORE):
        c, r = i // bar, i % bar
        x = margin + c * (lebar_sel + 16)
        y = judul_h + r * tinggi_sel
        d.rounded_rectangle([x, y + 4, x + lebar_sel, y + tinggi_sel - 8], radius=10, fill=(42, 42, 50, 255))
        tex = tex_ore(kunci)
        blok = iso_blok(tex, tex).resize((96, 96), Image.NEAREST)
        warna = hex2rgb(garis)
        garis_iso(blok, warna, 3, 3)
        img.alpha_composite(blok, (x + 10, y + 5))
        d.text((x + 128, y + 22), nama, font=f_nama, fill=(245, 245, 245, 255))
        d.text((x + 128, y + 62), garis.upper(), font=f_kode, fill=warna_teks(warna))
        d.rounded_rectangle([x + lebar_sel - 70, y + 34, x + lebar_sel - 22, y + 76], radius=6, outline=warna, width=4)
    return img


# ===========================================================================
def main():
    obor_detektor = ikon_obor_detektor()
    obor_biasa = ikon_obor_biasa()
    simpan(obor_detektor, RP, "textures", "items", "obor_detektor.png")
    simpan(tex_garis(), RP, "textures", "particle", "td_garis.png")

    simpan(ikon_pack("bp"), BP, "pack_icon.png")
    simpan(ikon_pack("rp"), RP, "pack_icon.png")
    simpan(ikon_pack("xray"), XRAY, "pack_icon.png")

    simpan(gambar_resep(obor_biasa, obor_detektor), DOCS, "resep_obor_detektor.png")
    simpan(gambar_resep(obor_detektor, obor_biasa), DOCS, "resep_obor_jadi_torch.png")
    simpan(legenda_warna(), DOCS, "warna_ore.png")
    simpan(banner(), DOCS, "banner.png")
    print("Aset visual Torch Detektor selesai dibuat.")


if __name__ == "__main__":
    main()
