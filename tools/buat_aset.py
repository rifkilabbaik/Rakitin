"""Generator aset visual Rakitin: tekstur item/blok/entity, model entity,
ikon pack, serta gambar resep untuk dokumentasi.

Semua gambar dibuat secara prosedural (pixel art) supaya addon tidak memakai
aset milik Mojang. Jalankan dari root repo:  python3 tools/buat_aset.py
Butuh paket: pip install pillow
"""

import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from data_rakitin import ITEMS, RESEP, RESEP_TUNGKU, nama_item  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RP = os.path.join(ROOT, "Rakitin_RP")
BP = os.path.join(ROOT, "Rakitin_BP")
DOCS = os.path.join(ROOT, "docs")

random.seed(20261003)


# ===========================================================================
# Alat gambar dasar
# ===========================================================================
def hex2rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ubah(warna, f):
    """Terangkan (f > 1) atau gelapkan (f < 1) warna."""
    r, g, b, a = warna
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


def kanvas(w=16, h=16, latar=(0, 0, 0, 0)):
    return Image.new("RGBA", (w, h), latar)


def px(img, x, y, warna):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), warna)


def kotak(img, x0, y0, x1, y1, warna, derau=0.0):
    """Isi persegi (inklusif) dengan warna + sedikit derau."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            f = 1 + random.uniform(-derau, derau)
            px(img, x, y, ubah(warna, f))


def jarak_segmen(px_, py_, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = ((px_ - ax) * dx + (py_ - ay) * dy) / max(1e-9, dx * dx + dy * dy)
    t = max(0, min(1, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px_ - cx, py_ - cy), t


def batang(img, a, b, r, warna, garis=None, sorot=None, derau=0.06):
    """Garis tebal dengan outline dan sisi terang (untuk tongkat, kail, botol)."""
    for y in range(img.height):
        for x in range(img.width):
            d, _t = jarak_segmen(x + 0.5, y + 0.5, a[0], a[1], b[0], b[1])
            if d <= r:
                w = warna
                if sorot and (x + 0.5 - (a[0] + b[0]) / 2) + (y + 0.5 - (a[1] + b[1]) / 2) < -0.3 and d > r * 0.35:
                    w = sorot
                px(img, x, y, ubah(w, 1 + random.uniform(-derau, derau)))
            elif garis and d <= r + 0.9:
                if img.getpixel((x, y))[3] == 0:
                    px(img, x, y, garis)


def outline(img, warna):
    """Tambahkan outline 1 piksel di sekeliling piksel yang tidak transparan."""
    salinan = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            if salinan.getpixel((x, y))[3]:
                continue
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ox, y + oy
                if 0 <= nx < img.width and 0 <= ny < img.height and salinan.getpixel((nx, ny))[3]:
                    px(img, x, y, warna)
                    break


def poligon(img, titik, warna, derau=0.05):
    lapis = kanvas(img.width, img.height)
    ImageDraw.Draw(lapis).polygon(titik, fill=warna)
    for y in range(img.height):
        for x in range(img.width):
            if lapis.getpixel((x, y))[3]:
                px(img, x, y, ubah(warna, 1 + random.uniform(-derau, derau)))


def elips(img, kotak_, warna, derau=0.05):
    lapis = kanvas(img.width, img.height)
    ImageDraw.Draw(lapis).ellipse(kotak_, fill=warna)
    for y in range(img.height):
        for x in range(img.width):
            if lapis.getpixel((x, y))[3]:
                px(img, x, y, ubah(warna, 1 + random.uniform(-derau, derau)))


def simpan(img, *bagian):
    path = os.path.join(*bagian)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


# ===========================================================================
# Pola permukaan (kayu, air, tanah)
# ===========================================================================
def papan_horizontal(img, warna, celah, tinggi_papan=4, y0=0, y1=15, x0=0, x1=15):
    for y in range(y0, y1 + 1):
        papan = (y - y0) // tinggi_papan
        f_papan = 1 + ((papan * 37) % 7 - 3) * 0.025
        for x in range(x0, x1 + 1):
            if (y - y0) % tinggi_papan == tinggi_papan - 1:
                px(img, x, y, ubah(celah, 1 + random.uniform(-0.05, 0.05)))
                continue
            serat = 0.06 * math.sin((x + papan * 5) * 0.9 + y * 0.3)
            px(img, x, y, ubah(warna, f_papan + serat + random.uniform(-0.04, 0.04)))
    # sambungan papan
    for papan in range((y1 - y0 + 1) // tinggi_papan):
        sx = x0 + (papan * 7 + 3) % (x1 - x0 + 1)
        for y in range(y0 + papan * tinggi_papan, y0 + papan * tinggi_papan + tinggi_papan - 1):
            px(img, sx, y, celah)


def papan_vertikal(img, warna, celah, lebar=4):
    for x in range(16):
        papan = x // lebar
        f_papan = 1 + ((papan * 41) % 7 - 3) * 0.03
        for y in range(16):
            if x % lebar == lebar - 1:
                px(img, x, y, ubah(celah, 1 + random.uniform(-0.05, 0.05)))
                continue
            serat = 0.06 * math.sin((y + papan * 4) * 0.8 + x * 0.2)
            px(img, x, y, ubah(warna, f_papan + serat + random.uniform(-0.04, 0.04)))


def air(img, warna, x0, y0, x1, y1, kilau=6):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            gel = 0.08 * math.sin(x * 0.9 + y * 0.5) + 0.05 * math.cos(y * 1.3 - x * 0.4)
            px(img, x, y, ubah(warna, 1 + gel + random.uniform(-0.03, 0.03)))
    for _ in range(kilau):
        px(img, random.randint(x0, x1), random.randint(y0, y1), ubah(warna, 1.45))


# ===========================================================================
# Ikon item
# ===========================================================================
def ikon_plastik():
    img = kanvas()
    batang(img, (4, 12), (10, 6), 2.6, hex2rgb("#bfe8f5"), hex2rgb("#3f7f9c"), hex2rgb("#effaff"))
    batang(img, (10, 6), (12, 4), 1.2, hex2rgb("#bfe8f5"), hex2rgb("#3f7f9c"))
    batang(img, (12.5, 3.5), (13.2, 2.8), 1.4, hex2rgb("#2f6fd6"), hex2rgb("#1b3f7a"))
    for x, y in ((6, 10), (8, 9), (7, 8), (5, 11)):
        px(img, x, y, hex2rgb("#8fc3d8"))
    return img


def ikon_daun_palem():
    """Daun palem: tulang daun diagonal dengan anak daun terpisah."""
    img = kanvas()
    hijau, terang, gelap = hex2rgb("#3fa34d"), hex2rgb("#7fd36a"), hex2rgb("#2d6e2f")
    tulang = [(4, 12), (6, 10), (8, 8), (10, 6), (12, 4)]
    panjang = [5, 4.5, 4, 3, 2]
    for (x0, y0), p in zip(tulang, panjang):
        for arah in ((-0.3, -1.0), (1.0, 0.3)):
            s_ = 0.0
            while s_ <= p:
                w = terang if s_ > p - 1 else hijau
                px(img, round(x0 + arah[0] * s_), round(y0 + arah[1] * s_), w)
                s_ += 0.5
    for i in range(12):
        px(img, 2 + i, 14 - i, gelap)
    outline(img, hex2rgb("#1d3f20"))
    return img


def ikon_besi_tua():
    img = kanvas()
    poligon(img, [(2, 5), (7, 2), (13, 3), (14, 9), (11, 14), (4, 13), (1, 9)], hex2rgb("#8a8f96"), 0.08)
    for x, y in ((4, 6), (5, 7), (10, 11), (11, 10), (12, 6), (6, 11)):
        px(img, x, y, hex2rgb("#a0522d"))
    for x, y in ((5, 5), (11, 5), (9, 11)):
        px(img, x, y, hex2rgb("#4a4e52"))
        px(img, x + 1, y, hex2rgb("#c9ced3"))
    for x in range(3, 13):
        px(img, x, 8 + (x % 3 == 0), hex2rgb("#6d7278"))
    outline(img, hex2rgb("#33363a"))
    return img


def ikon_gigi_hiu():
    img = kanvas()
    poligon(img, [(3, 3), (12, 3), (8, 14)], hex2rgb("#f2ead3"), 0.04)
    for y in range(4, 12):
        px(img, 5 + (y - 3) // 3, y, hex2rgb("#fffaf0"))
    for x in range(4, 12, 2):
        px(img, x, 3, hex2rgb("#c9bfa0"))
    kotak(img, 3, 2, 12, 2, hex2rgb("#d9a0a0"))
    outline(img, hex2rgb("#8c836a"))
    return img


def ikon_daging(matang):
    img = kanvas()
    if matang:
        elips(img, (1, 4, 14, 12), hex2rgb("#a0612d"), 0.06)
        for x0 in (4, 8, 12):
            for i in range(5):
                px(img, x0 - i, 5 + i + (x0 % 3), hex2rgb("#5a3214"))
        outline(img, hex2rgb("#3d230f"))
    else:
        elips(img, (1, 4, 14, 12), hex2rgb("#e8a0a0"), 0.05)
        kotak(img, 3, 4, 12, 5, hex2rgb("#6d7d8a"), 0.05)
        for x in range(3, 13, 3):
            for y in range(7, 11):
                px(img, x + (y % 2), y, hex2rgb("#f5c6c6"))
        outline(img, hex2rgb("#7a3a3a"))
    return img


def ikon_botol(isi=None, salju=False):
    img = kanvas()
    kaca = hex2rgb("#dfeff5")
    kotak(img, 5, 6, 10, 14, kaca)
    kotak(img, 6, 3, 9, 5, kaca)
    kotak(img, 6, 1, 9, 2, hex2rgb("#2f6fd6"))
    if isi:
        air(img, hex2rgb(isi), 5, 8, 10, 14, kilau=2)
        if salju:
            for x, y in ((6, 10), (9, 12), (7, 13), (8, 9)):
                px(img, x, y, hex2rgb("#f4f4f4"))
    for y in range(6, 13):
        px(img, 6, y, hex2rgb("#ffffff"))
    outline(img, hex2rgb("#4f7383"))
    return img


def ikon_tombak():
    img = kanvas()
    batang(img, (2, 14), (10.5, 5.5), 0.8, hex2rgb("#8b5a2b"), None, None, 0.08)
    poligon(img, [(9, 5), (14, 1), (12, 7)], hex2rgb("#c0c6cc"), 0.05)
    px(img, 12, 3, hex2rgb("#eef2f5"))
    px(img, 11, 4, hex2rgb("#eef2f5"))
    batang(img, (9, 7), (10, 6), 1.0, hex2rgb("#d9c79e"))
    outline(img, hex2rgb("#2f2a26"))
    return img


def ikon_buku():
    img = kanvas()
    kotak(img, 3, 2, 13, 14, hex2rgb("#3c8d40"), 0.08)
    kotak(img, 3, 2, 4, 14, hex2rgb("#2a5e2c"))
    kotak(img, 13, 3, 13, 13, hex2rgb("#efe6c8"))
    for y in (5, 9, 12):
        kotak(img, 3, y, 5, y, hex2rgb("#d8c79a"))
    for i in range(5):
        px(img, 7 + i, 6 + i // 2, hex2rgb("#6fcf6a"))
        px(img, 9, 4 + i * 2, hex2rgb("#2d6e2f"))
    outline(img, hex2rgb("#1d3f20"))
    return img


WARNA_TIER = {
    1: ("#8b5a2b", "#c48a52"),
    2: ("#9aa1a8", "#e3e8ec"),
    3: ("#d9a520", "#ffe27a"),
    4: ("#37bdbd", "#a8fff6"),
    5: ("#4a3f4f", "#8f7a99"),
}


def ikon_kail(tier, polos=False):
    img = kanvas()
    utama, terang = WARNA_TIER.get(tier, WARNA_TIER[1]) if not polos else ("#8b5a2b", "#c48a52")
    batang(img, (2.5, 13.5), (13, 2.5), 0.75, hex2rgb(utama), None, hex2rgb(terang), 0.05)
    batang(img, (2.5, 13.5), (5, 11), 1.1, hex2rgb("#3b2a1c"))
    for y in range(3, 10):
        px(img, 13, y, hex2rgb("#d0d0d0"))
    px(img, 13, 10, hex2rgb("#a9b0b5"))
    px(img, 12, 11, hex2rgb("#a9b0b5"))
    px(img, 12, 10, hex2rgb("#a9b0b5"))
    elips(img, (4, 9, 7, 12), hex2rgb("#5c5f63"), 0.02)
    px(img, 5, 10, hex2rgb("#c9ced3"))
    if not polos and tier >= 2:
        px(img, 3, 12, hex2rgb(terang))
    outline(img, hex2rgb("#241a12"))
    return img


def ikon_pecahan_portal():
    img = kanvas()
    poligon(img, [(7, 1), (13, 6), (11, 14), (4, 13), (2, 6)], hex2rgb("#14302c"), 0.1)
    for _ in range(9):
        px(img, random.randint(4, 11), random.randint(4, 12), hex2rgb(random.choice(["#3fe0c0", "#9ff5e0", "#7b4fa0"])))
    for i in range(5):
        px(img, 7 + i, 2 + i, hex2rgb("#7b4fa0"))
    outline(img, hex2rgb("#070f0d"))
    return img


def ikon_inti_portal():
    img = kanvas()
    elips(img, (1, 1, 14, 14), hex2rgb("#c8d6b0"), 0.06)
    elips(img, (3, 3, 12, 12), hex2rgb("#1f5f4f"), 0.08)
    elips(img, (6, 5, 9, 10), hex2rgb("#0b1a14"), 0.0)
    px(img, 5, 5, hex2rgb("#63e6b0"))
    px(img, 6, 4, hex2rgb("#63e6b0"))
    px(img, 10, 10, hex2rgb("#9d6fd0"))
    outline(img, hex2rgb("#4b5a3c"))
    return img


# Ikon vanilla sederhana (hanya untuk gambar resep di dokumentasi).
def ikon_benang():
    img = kanvas()
    for x in range(2, 15):
        y = 8 + 3 * math.sin(x * 0.7)
        px(img, x, round(y), hex2rgb("#f4f4f4"))
        px(img, x, round(y) + 1, hex2rgb("#bdbdbd"))
    return img


def ikon_tongkat():
    img = kanvas()
    batang(img, (3, 13), (12, 3), 0.8, hex2rgb("#8b5a2b"), hex2rgb("#3b2a1c"), hex2rgb("#b07a42"))
    return img


def ikon_batangan(warna, terang):
    img = kanvas()
    poligon(img, [(2, 10), (6, 6), (14, 6), (10, 10)], hex2rgb(terang), 0.03)
    poligon(img, [(2, 10), (10, 10), (10, 13), (2, 13)], hex2rgb(warna), 0.03)
    poligon(img, [(10, 10), (14, 6), (14, 9), (10, 13)], ubah(hex2rgb(warna), 0.8), 0.03)
    outline(img, ubah(hex2rgb(warna), 0.45))
    return img


def ikon_berlian():
    img = kanvas()
    poligon(img, [(3, 6), (6, 3), (10, 3), (13, 6), (8, 14)], hex2rgb("#4fe3e1"), 0.04)
    poligon(img, [(3, 6), (13, 6), (8, 14)], hex2rgb("#2cb8b6"), 0.04)
    px(img, 6, 5, hex2rgb("#e8ffff"))
    px(img, 7, 4, hex2rgb("#e8ffff"))
    outline(img, hex2rgb("#125c5b"))
    return img


def ikon_serpihan_netherite():
    img = kanvas()
    poligon(img, [(3, 6), (8, 3), (13, 6), (12, 12), (5, 13)], hex2rgb("#4d3b36"), 0.12)
    for x, y in ((6, 7), (9, 9), (10, 6), (7, 11)):
        px(img, x, y, hex2rgb("#7a625a"))
    outline(img, hex2rgb("#1f1714"))
    return img


def ikon_mata_ender():
    img = kanvas()
    elips(img, (2, 2, 13, 13), hex2rgb("#2f8f6f"), 0.08)
    elips(img, (5, 5, 10, 10), hex2rgb("#7fd8a8"), 0.04)
    elips(img, (7, 6, 8, 9), hex2rgb("#0b1a14"), 0.0)
    outline(img, hex2rgb("#103a2c"))
    return img


def ikon_botol_kaca():
    img = kanvas()
    kotak(img, 5, 6, 10, 14, hex2rgb("#e6f2f7"))
    kotak(img, 6, 3, 9, 5, hex2rgb("#e6f2f7"))
    for y in range(6, 13):
        px(img, 6, y, hex2rgb("#ffffff"))
    outline(img, hex2rgb("#7a98a6"))
    return img


# ===========================================================================
# Tekstur blok
# ===========================================================================
def tex_fondasi_rakit():
    img = kanvas()
    papan_horizontal(img, hex2rgb("#b08a55"), hex2rgb("#5e4527"))
    for x0 in (2, 12):
        for y in range(16):
            for x in (x0, x0 + 1):
                w = hex2rgb("#d8c79a") if (x + y) % 3 else hex2rgb("#a8986b")
                px(img, x, y, w)
    return img


def tex_fondasi_kuat():
    img = kanvas()
    papan_horizontal(img, hex2rgb("#9c7a4b"), hex2rgb("#4f3a22"))
    besi = hex2rgb("#9aa0a6")
    for x0, y0 in ((0, 0), (12, 0), (0, 12), (12, 12)):
        kotak(img, x0, y0, x0 + 3, y0 + 3, besi, 0.05)
        px(img, x0 + 1, y0 + 1, hex2rgb("#4a4e52"))
        px(img, x0 + 2, y0 + 2, hex2rgb("#d5d9dd"))
    kotak(img, 0, 7, 15, 8, ubah(besi, 0.9), 0.05)
    for x in (3, 8, 13):
        px(img, x, 7, hex2rgb("#4a4e52"))
    return img


def bingkai_kayu(img, tebal=2):
    for y in range(16):
        for x in range(16):
            if x < tebal or y < tebal or x > 15 - tebal or y > 15 - tebal:
                px(img, x, y, ubah(hex2rgb("#8b6337"), 1 + random.uniform(-0.08, 0.08)))
    for i in range(16):
        px(img, i, 0, hex2rgb("#5e4527"))
        px(img, i, 15, hex2rgb("#5e4527"))
        px(img, 0, i, hex2rgb("#5e4527"))
        px(img, 15, i, hex2rgb("#5e4527"))


def tex_penyaring_samping():
    img = kanvas()
    papan_vertikal(img, hex2rgb("#a07a48"), hex2rgb("#5e4527"))
    kotak(img, 0, 3, 15, 4, hex2rgb("#3a7bd5"), 0.05)
    kotak(img, 0, 11, 15, 12, hex2rgb("#3a7bd5"), 0.05)
    kotak(img, 7, 7, 8, 9, hex2rgb("#9aa0a6"))
    return img


def tex_penyaring_atas(mode):
    img = kanvas()
    bingkai_kayu(img)
    if mode == "kosong":
        kotak(img, 2, 2, 13, 13, hex2rgb("#3b3b3b"), 0.08)
        for i in range(2, 14):
            for j in range(2, 14):
                if (i + j) % 4 == 0 or (i - j) % 4 == 0:
                    px(img, i, j, hex2rgb("#cfc6a8"))
    elif mode == "proses":
        air(img, hex2rgb("#2e8b8b"), 2, 2, 13, 13, kilau=4)
        for x, y in ((4, 5), (9, 4), (11, 9), (6, 11), (8, 8)):
            px(img, x, y, hex2rgb("#e8f8f8"))
            px(img, x + 1, y, hex2rgb("#bfe8e8"))
    else:
        air(img, hex2rgb("#59c7f2"), 2, 2, 13, 13, kilau=8)
    return img


def tex_penampung_samping():
    img = kanvas()
    papan_vertikal(img, hex2rgb("#8b6337"), hex2rgb("#4f3a22"), lebar=8)
    for x0 in (1, 9):
        kotak(img, x0, 2, x0 + 5, 13, hex2rgb("#9fd3ef"), 0.04)
        for y in range(2, 14, 3):
            px(img, x0 + 1, y, hex2rgb("#d9f0fb"))
    return img


def tex_penampung_atas(level):
    img = kanvas()
    bingkai_kayu(img)
    for y in range(2, 14):
        for x in range(2, 14):
            d = math.hypot(x - 7.5, y - 7.5)
            w = ubah(hex2rgb("#9fd3ef"), 0.75 + d * 0.05)
            px(img, x, y, w)
    if level == 0:
        elips(img, (6, 6, 9, 9), hex2rgb("#2b2b2b"), 0.0)
    elif level == 1:
        elips(img, (4, 4, 11, 11), hex2rgb("#4fa9e0"), 0.04)
        px(img, 6, 6, hex2rgb("#d9f0fb"))
    else:
        air(img, hex2rgb("#4fa9e0"), 2, 2, 13, 13, kilau=6)
    return img


def tex_pot_samping():
    img = kanvas()
    for y in range(16):
        for x in range(16):
            px(img, x, y, ubah(hex2rgb("#a0623a"), 1 + random.uniform(-0.06, 0.06)))
    for x in range(16):
        px(img, x, 1, hex2rgb("#c27a4a"))
        px(img, x, 2, hex2rgb("#7a4626"))
        px(img, x, 8, hex2rgb("#7a4626"))
    return img


def tex_pot_tanah():
    img = kanvas()
    for y in range(16):
        for x in range(16):
            px(img, x, y, ubah(hex2rgb("#4a3524"), 1 + random.uniform(-0.15, 0.15)))
    for _ in range(10):
        px(img, random.randint(0, 15), random.randint(0, 15), hex2rgb("#6b4e36"))
    return img


def daun_kecil(img, x, y, arah, warna):
    px(img, x, y, warna)
    px(img, x + arah, y - 1, warna)
    px(img, x + 2 * arah, y - 1, ubah(warna, 1.2))


def tex_tanaman(jenis):
    img = kanvas()
    hijau = hex2rgb("#4caf50")
    if jenis == "bibit":
        for y in range(12, 16):
            px(img, 8, y, hex2rgb("#3d8b40"))
        daun_kecil(img, 7, 12, -1, hijau)
        daun_kecil(img, 9, 12, 1, hijau)
    elif jenis == "tumbuh":
        for x0 in (5, 8, 11):
            for y in range(10, 16):
                px(img, x0 + (y % 2 == 0 and x0 != 8), y, hex2rgb("#3d8b40"))
            daun_kecil(img, x0 - 1, 11, -1, hijau)
            daun_kecil(img, x0 + 1, 13, 1, hijau)
    elif jenis == "gandum":
        for x0 in (3, 6, 9, 12):
            for y in range(11, 16):
                px(img, x0, y, hex2rgb("#b8a040"))
            for y in range(8, 11):
                px(img, x0, y, hex2rgb("#e0c050"))
                px(img, x0 + 1, y, hex2rgb("#c9a63a"))
    elif jenis in ("kentang", "wortel", "bit"):
        daun = {"kentang": "#4caf50", "wortel": "#5cbf3a", "bit": "#3f9a45"}[jenis]
        akar = {"kentang": "#c9a46a", "wortel": "#f28c28", "bit": "#9e1f3f"}[jenis]
        for x0 in (4, 8, 11):
            for y in range(9, 14):
                px(img, x0 + (y % 3 == 0), y, hex2rgb(daun))
                if jenis == "bit":
                    px(img, x0, y, hex2rgb("#b0304f"))
            daun_kecil(img, x0 - 1, 10, -1, hex2rgb(daun))
            daun_kecil(img, x0 + 1, 11, 1, hex2rgb(daun))
            kotak(img, x0 - 1, 14, x0 + 1, 15, hex2rgb(akar))
    return img


def tex_layar_kain():
    img = kanvas()
    for y in range(16):
        for x in range(16):
            w = hex2rgb("#efe8d8") if y % 4 else hex2rgb("#d9cfb8")
            px(img, x, y, ubah(w, 1 + random.uniform(-0.04, 0.04)))
    kotak(img, 9, 8, 12, 11, hex2rgb("#c9b48a"), 0.05)
    for i in range(16):
        px(img, 0, i, hex2rgb("#bfb39a"))
        px(img, 15, i, hex2rgb("#bfb39a"))
    return img


def tex_kayu_polos(warna):
    img = kanvas()
    for y in range(16):
        for x in range(16):
            serat = 0.07 * math.sin(y * 0.9 + x * 0.15)
            px(img, x, y, ubah(hex2rgb(warna), 1 + serat + random.uniform(-0.04, 0.04)))
    return img


# ===========================================================================
# Entity: model + tekstur (box UV)
# ===========================================================================
def wajah_box(uv, ukuran):
    """Posisi tiap sisi untuk box UV Bedrock. Mengembalikan dict nama -> (x, y, w, h)."""
    u, v = uv
    w, h, d = ukuran
    return {
        "up": (u + d, v, w, d),
        "down": (u + d + w, v, w, d),
        "east": (u, v + d, d, h),
        "north": (u + d, v + d, w, h),
        "west": (u + d + w, v + d, d, h),
        "south": (u + 2 * d + w, v + d, w, h),
    }


def cat_sisi(img, rect, warna_fn):
    x0, y0, w, h = rect
    for j in range(int(math.ceil(h))):
        for i in range(int(math.ceil(w))):
            px(img, int(x0) + i, int(y0) + j, warna_fn(i, j, w, h))


HIU = [
    # nama, induk, pivot, kubus: [(origin, size, uv, rotasi?)]
    ("badan", None, [0, 5, 0], [([-4, 1, -8], [8, 8, 18], [0, 0], None)]),
    ("kepala", "badan", [0, 5, -8], [([-3.5, 1.5, -15], [7, 6, 7], [0, 26], None)]),
    ("moncong", "kepala", [0, 4, -15], [([-2.5, 2.5, -18], [5, 4, 3], [28, 26], None)]),
    ("rahang", "kepala", [0, 2, -9], [([-3, 0.5, -16], [6, 1, 7], [44, 26], None)]),
    ("ekor1", "badan", [0, 5, 10], [([-3, 2, 10], [6, 6, 8], [0, 40], None)]),
    ("ekor2", "ekor1", [0, 5, 18], [([-1.5, 3, 18], [3, 4, 6], [28, 40], None)]),
    ("sirip_ekor", "ekor2", [0, 5, 23], [
        ([-0.5, 5, 21], [1, 9, 4], [46, 40], [-35, 0, 0]),
        ([-0.5, -1, 21], [1, 6, 3], [56, 40], [35, 0, 0]),
    ]),
    ("sirip_punggung", "badan", [0, 9, 0], [([-0.5, 9, -3], [1, 8, 6], [52, 0], [-30, 0, 0])]),
    ("sirip_kiri", "badan", [4, 2, -3], [([4, 1.5, -6], [8, 1, 5], [66, 0], [0, 0, -25])]),
    ("sirip_kanan", "badan", [-4, 2, -3], [([-12, 1.5, -6], [8, 1, 5], [66, 6], [0, 0, 25])]),
]

PUING = [
    ("akar", None, [0, 0, 0], []),
    ("papan", "akar", [0, 0, 0], [
        ([-6, 0, -3.5], [12, 2, 3], [0, 0], None),
        ([-5, 0, 0.5], [11, 2, 3], [0, 5], None),
        ([-1, 2, -4], [2, 1, 8], [30, 0], None),
    ]),
    ("plastik", "akar", [0, 0, 0], [
        ([-4, 0, -2], [7, 4, 4], [0, 12], None),
        ([3, 1, -1], [2, 2, 2], [22, 12], None),
        ([5, 1, -1], [1, 2, 2], [30, 12], None),
    ]),
    ("daun", "akar", [0, 0, 0], [
        ([-7, 0.5, -3], [14, 1, 6], [0, 22], None),
        ([-8, 0.6, -0.5], [16, 1, 1], [0, 30], None),
    ]),
    ("barel", "akar", [0, 0, 0], [([-4, 0, -4], [8, 10, 8], [0, 34], None)]),
]


def geometri_entity(ident, tw, th, bones, lebar=3, tinggi=2):
    hasil = []
    for nama, induk, pivot, kubus in bones:
        b = {"name": nama, "pivot": pivot}
        if induk:
            b["parent"] = induk
        if kubus:
            b["cubes"] = []
            for origin, size, uv, rot in kubus:
                c = {"origin": origin, "size": size, "uv": uv}
                if rot:
                    c["rotation"] = rot
                    c["pivot"] = pivot
                b["cubes"].append(c)
        hasil.append(b)
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": ident,
                    "texture_width": tw,
                    "texture_height": th,
                    "visible_bounds_width": lebar,
                    "visible_bounds_height": tinggi,
                    "visible_bounds_offset": [0, 0.5, 0],
                },
                "bones": hasil,
            }
        ],
    }


def tekstur_hiu():
    img = kanvas(128, 64)
    punggung = hex2rgb("#5b6d7c")
    perut = hex2rgb("#e6ecef")

    def samping(i, j, w, h):
        batas = h * 0.55
        if j < batas:
            return ubah(punggung, 1 + 0.06 * math.sin(i * 0.7) + random.uniform(-0.05, 0.05))
        if j < batas + 1:
            return ubah(punggung, 1.25)
        return ubah(perut, 1 + random.uniform(-0.03, 0.03))

    for nama, _induk, _pivot, kubus in HIU:
        for _origin, size, uv, _rot in kubus:
            f = wajah_box(uv, size)
            cat_sisi(img, f["up"], lambda i, j, w, h: ubah(punggung, 0.92 + random.uniform(-0.05, 0.05)))
            cat_sisi(img, f["down"], lambda i, j, w, h: ubah(perut, 1 + random.uniform(-0.03, 0.03)))
            for s in ("east", "west", "north", "south"):
                cat_sisi(img, f[s], samping)
            if nama.startswith("sirip"):
                for s in f.values():
                    cat_sisi(img, s, lambda i, j, w, h: ubah(punggung, 0.85 + random.uniform(-0.05, 0.05)))

    # Mata di sisi kepala + insang di sisi badan.
    kep = wajah_box([0, 26], [7, 6, 7])
    for s in ("east", "west"):
        x0, y0, w, h = kep[s]
        mx = x0 + 1 if s == "east" else x0 + w - 2
        px(img, mx, y0 + 2, hex2rgb("#0e0e0e"))
        px(img, mx, y0 + 1, hex2rgb("#2a2a2a"))
    bad = wajah_box([0, 0], [8, 8, 18])
    for s in ("east", "west"):
        x0, y0, w, h = bad[s]
        for k in range(3):
            gx = x0 + 2 + k * 2 if s == "east" else x0 + w - 3 - k * 2
            for j in range(2, 5):
                px(img, gx, y0 + j, ubah(punggung, 0.7))
    # Gigi di depan moncong dan rahang.
    for uv, ukuran in (([28, 26], [5, 4, 3]), ([44, 26], [6, 1, 7])):
        x0, y0, w, h = wajah_box(uv, ukuran)["north"]
        for i in range(int(w)):
            px(img, x0 + i, y0 + h - 1, hex2rgb("#ffffff") if i % 2 == 0 else hex2rgb("#c9c9c9"))
    return img


def tekstur_puing():
    img = kanvas(64, 64)
    kayu = hex2rgb("#a8814f")
    for _n, _i, _p, kubus in PUING[1:2]:
        for _o, size, uv, _r in kubus:
            for s in wajah_box(uv, size).values():
                cat_sisi(img, s, lambda i, j, w, h: ubah(kayu, 1 + 0.08 * math.sin(i * 0.9) + random.uniform(-0.05, 0.05)))
    plastik = PUING[2][3]
    for k, (_o, size, uv, _r) in enumerate(plastik):
        warna = [hex2rgb("#bfe8f5"), hex2rgb("#bfe8f5"), hex2rgb("#2f6fd6")][k]
        for s in wajah_box(uv, size).values():
            cat_sisi(img, s, lambda i, j, w, h, c=warna: ubah(c, 1 + random.uniform(-0.06, 0.06)))
    for k, (_o, size, uv, _r) in enumerate(PUING[3][3]):
        warna = hex2rgb("#3fa34d") if k == 0 else hex2rgb("#2d6e2f")
        for s in wajah_box(uv, size).values():
            cat_sisi(img, s, lambda i, j, w, h, c=warna: ubah(c, 1 + 0.1 * math.sin(i * 1.3) + random.uniform(-0.05, 0.05)))
    _o, size, uv, _r = PUING[4][3][0]
    f = wajah_box(uv, size)
    for s in ("east", "west", "north", "south"):
        cat_sisi(img, f[s], lambda i, j, w, h: hex2rgb("#4a4e52") if j in (1, 8) else ubah(hex2rgb("#8b5e34"), 1 + 0.07 * math.sin(i * 1.7) + random.uniform(-0.04, 0.04)))
    for s in ("up", "down"):
        cat_sisi(img, f[s], lambda i, j, w, h: hex2rgb("#4a4e52") if i in (0, w - 1) or j in (0, h - 1) else ubah(hex2rgb("#9c6b3d"), 1 + random.uniform(-0.05, 0.05)))
    return img


# ===========================================================================
# Ikon pack & banner
# ===========================================================================
def adegan(w, h, posisi_rakit=0.42):
    """Pemandangan laut dengan rakit, layar, matahari, dan sirip hiu."""
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    laut = int(h * 0.58)
    for y in range(laut):
        t = y / laut
        d.line([(0, y), (w, y)], fill=(int(90 + 120 * t), int(170 + 60 * t), int(235 + 10 * t), 255))
    for y in range(laut, h):
        t = (y - laut) / (h - laut)
        d.line([(0, y), (w, y)], fill=(int(30 - 20 * t), int(120 - 60 * t), int(190 - 70 * t), 255))
    s = h / 128
    d.ellipse([w * 0.72, h * 0.08, w * 0.72 + 26 * s, h * 0.08 + 26 * s], fill=(255, 226, 120, 255))
    for i in range(int(w / (14 * s)) + 1):
        x = i * 14 * s
        d.arc([x, laut - 3 * s, x + 14 * s, laut + 5 * s], 180, 360, fill=(220, 240, 255, 255), width=max(1, int(s)))
    cx = w * posisi_rakit
    rx0, rx1 = cx - 34 * s, cx + 34 * s
    ry = laut - 4 * s
    d.rectangle([rx0, ry, rx1, ry + 9 * s], fill=(176, 138, 85, 255), outline=(94, 69, 39, 255), width=max(1, int(s)))
    for k in range(1, 6):
        x = rx0 + k * (rx1 - rx0) / 6
        d.line([(x, ry), (x, ry + 9 * s)], fill=(94, 69, 39, 255), width=max(1, int(s)))
    d.rectangle([cx - 2 * s, ry - 52 * s, cx + 2 * s, ry], fill=(122, 85, 48, 255))
    d.polygon([(cx + 3 * s, ry - 50 * s), (cx + 3 * s, ry - 8 * s), (cx + 32 * s, ry - 10 * s)], fill=(239, 232, 216, 255), outline=(191, 179, 154, 255))
    d.rectangle([rx0 + 6 * s, ry - 10 * s, rx0 + 16 * s, ry], fill=(140, 100, 50, 255), outline=(80, 55, 25, 255))
    fx = w * (0.82 if posisi_rakit < 0.6 else 0.9)
    d.polygon([(fx, laut + 14 * s), (fx + 7 * s, laut - 2 * s), (fx + 13 * s, laut + 14 * s)], fill=(91, 109, 124, 255))
    return img


def ikon_pack():
    besar = adegan(512, 512)
    kecil = besar.resize((128, 128), Image.LANCZOS)
    kecil = kecil.resize((64, 64), Image.NEAREST).resize((256, 256), Image.NEAREST)
    return kecil


def banner():
    img = adegan(1280, 400, posisi_rakit=0.66).resize((640, 200), Image.LANCZOS)
    img = img.resize((320, 100), Image.NEAREST).resize((1280, 400), Image.NEAREST)
    d = ImageDraw.Draw(img)
    font = muat_font(110, tebal=True)
    kecil = muat_font(36)
    teks = "RAKITIN"
    d.text((64 + 5, 50 + 5), teks, font=font, fill=(0, 0, 0, 140))
    d.text((64, 50), teks, font=font, fill=(255, 255, 255, 255))
    d.text((70, 300), "Addon bertahan hidup di lautan • Minecraft Bedrock 1.26", font=kecil, fill=(255, 255, 255, 255))
    return img


# ===========================================================================
# Gambar resep untuk dokumentasi
# ===========================================================================
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


def iso_blok(atas, samping, ukuran=16):
    """Render blok isometrik kecil (32x32) dari tekstur atas & samping.

    Koordinat ternormalisasi: X dari -1..1 (kiri-kanan), Y dari 0..2 (atas-bawah).
    Wajah atas = belah ketupat, wajah kiri & kanan = jajaran genjang.
    """
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


def ikon_pot_dok():
    img = kanvas()
    kotak(img, 3, 8, 12, 14, hex2rgb("#a0623a"), 0.06)
    kotak(img, 2, 7, 13, 8, hex2rgb("#c27a4a"))
    kotak(img, 4, 8, 11, 8, hex2rgb("#4a3524"))
    for y in range(3, 8):
        px(img, 7 + (y % 2), y, hex2rgb("#3d8b40"))
    daun_kecil(img, 6, 4, -1, hex2rgb("#4caf50"))
    daun_kecil(img, 9, 5, 1, hex2rgb("#4caf50"))
    outline(img, hex2rgb("#3b2414"))
    return img


def ikon_layar_dok():
    img = kanvas()
    kotak(img, 7, 1, 8, 15, hex2rgb("#7a5530"))
    poligon(img, [(9, 2), (9, 12), (15, 12)], hex2rgb("#efe8d8"), 0.04)
    poligon(img, [(6, 3), (6, 12), (1, 12)], hex2rgb("#e3dac4"), 0.04)
    kotak(img, 1, 13, 15, 13, hex2rgb("#5e4527"))
    outline(img, hex2rgb("#3b2a1c"))
    return img


def ikon_kemudi_dok():
    img = kanvas()
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 13, 13], outline=hex2rgb("#8a5a30"), width=2)
    d.line([(7.5, 2), (7.5, 13)], fill=hex2rgb("#6e4624"), width=1)
    d.line([(2, 7.5), (13, 7.5)], fill=hex2rgb("#6e4624"), width=1)
    kotak(img, 6, 6, 9, 9, hex2rgb("#9aa0a6"))
    for x, y in ((7, 0), (7, 15), (0, 7), (15, 7)):
        kotak(img, x, y, x + 1, y, hex2rgb("#6e4624"))
    return img


def daftar_ikon(tekstur_item, tekstur_blok):
    ikon = {f"rakit:{k}": v for k, v in tekstur_item.items()}
    ikon.update({
        "rakit:fondasi_rakit": iso_blok(tekstur_blok["fondasi_rakit"], tekstur_blok["fondasi_rakit"]),
        "rakit:fondasi_kuat": iso_blok(tekstur_blok["fondasi_kuat"], tekstur_blok["fondasi_kuat"]),
        "rakit:penyaring_air": iso_blok(tekstur_blok["penyaring_atas_siap"], tekstur_blok["penyaring_samping"]),
        "rakit:penampung_hujan": iso_blok(tekstur_blok["penampung_atas_sedikit"], tekstur_blok["penampung_samping"]),
        "rakit:pot_tanam": ikon_pot_dok(),
        "rakit:layar": ikon_layar_dok(),
        "rakit:kemudi": ikon_kemudi_dok(),
        "tag:minecraft:planks": iso_blok(tex_kayu_polos("#b8945f"), tex_kayu_polos("#b8945f")),
        "minecraft:dirt": iso_blok(tex_pot_tanah(), tex_pot_tanah()),
        "minecraft:string": ikon_benang(),
        "minecraft:stick": ikon_tongkat(),
        "minecraft:iron_ingot": ikon_batangan("#b8bec4", "#e3e8ec"),
        "minecraft:gold_ingot": ikon_batangan("#e0a820", "#ffe27a"),
        "minecraft:diamond": ikon_berlian(),
        "minecraft:netherite_scrap": ikon_serpihan_netherite(),
        "minecraft:fishing_rod": ikon_kail(1, polos=True),
        "minecraft:glass_bottle": ikon_botol_kaca(),
        "minecraft:ender_eye": ikon_mata_ender(),
    })
    return ikon


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


def tulis_jumlah(kanvas_, x, y, n, ukuran=SLOT):
    if n <= 1:
        return
    d = ImageDraw.Draw(kanvas_)
    font = muat_font(9 * SKALA // 2 + 6, tebal=True)
    teks = str(n)
    bx = d.textbbox((0, 0), teks, font=font)
    tx = x + ukuran - (bx[2] - bx[0]) - 4
    ty = y + ukuran - (bx[3] - bx[1]) - 8
    d.text((tx + 2, ty + 2), teks, font=font, fill=(62, 62, 62, 255))
    d.text((tx, ty), teks, font=font, fill=(255, 255, 255, 255))


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


def gambar_resep(r, ikon):
    w = TEPI * 2 + SLOT * 3 + 70 + SLOT + 16
    h = TEPI * 2 + SLOT * 3
    img = panel(w, h)
    sel = [[None] * 3 for _ in range(3)]
    if r["tipe"] == "shaped":
        for j, baris in enumerate(r["pola"]):
            for i, ch in enumerate(baris):
                if ch != " ":
                    sel[j][i] = r["kunci"][ch]
    else:
        for k, b in enumerate(r["bahan"]):
            sel[k // 3][k % 3] = b
    for j in range(3):
        for i in range(3):
            x, y = TEPI + i * SLOT, TEPI + j * SLOT
            gambar_slot(img, x, y)
            if sel[j][i]:
                tempel_ikon(img, ikon[sel[j][i]], x, y)
    ax = TEPI + SLOT * 3 + 12
    ay = TEPI + SLOT + (SLOT - 34) // 2
    panah(img, ax, ay)
    rx = ax + 58
    ry = TEPI + SLOT - 8
    gambar_slot(img, rx, ry, SLOT + 16)
    tempel_ikon(img, ikon[r["hasil"]], rx, ry, SLOT + 16)
    tulis_jumlah(img, rx, ry, r["jumlah"], SLOT + 16)
    return img


def ikon_api():
    img = kanvas()
    poligon(img, [(8, 1), (13, 8), (12, 13), (4, 13), (3, 8)], hex2rgb("#f28c28"), 0.08)
    poligon(img, [(8, 5), (11, 10), (10, 13), (6, 13), (5, 10)], hex2rgb("#ffd54a"), 0.05)
    kotak(img, 2, 14, 13, 15, hex2rgb("#6e4624"))
    return img


def gambar_resep_tungku(r, ikon):
    w = TEPI * 2 + SLOT + 70 + SLOT + 16
    h = TEPI * 2 + SLOT * 2 + 10
    img = panel(w, h)
    gambar_slot(img, TEPI, TEPI)
    tempel_ikon(img, ikon[r["masuk"]], TEPI, TEPI)
    tempel_ikon(img, ikon_api(), TEPI, TEPI + SLOT + 10)
    ax = TEPI + SLOT + 12
    ay = TEPI + SLOT // 2
    panah(img, ax, ay)
    rx = ax + 58
    ry = TEPI + SLOT // 2 - 8
    gambar_slot(img, rx, ry, SLOT + 16)
    tempel_ikon(img, ikon[r["hasil"]], rx, ry, SLOT + 16)
    return img


def tulis_resep_md():
    baris = [
        "# Daftar Resep Rakitin",
        "",
        "Semua resep di bawah dibuat di **Meja Kerajinan** (resep 2x2 juga bisa di inventori),",
        "kecuali bagian *Tungku & Api Unggun*. Gambar dibuat otomatis oleh `tools/buat_aset.py`.",
        "",
        "> Resep yang ditandai **tanpa pola** bisa disusun di posisi mana saja.",
        "",
        "## Meja Kerajinan",
        "",
    ]
    for r in RESEP:
        if r["tipe"] == "shaped":
            bahan = {}
            for baris_pola in r["pola"]:
                for ch in baris_pola:
                    if ch != " ":
                        bahan[r["kunci"][ch]] = bahan.get(r["kunci"][ch], 0) + 1
        else:
            bahan = {}
            for b in r["bahan"]:
                bahan[b] = bahan.get(b, 0) + 1
        daftar = ", ".join(f"{n}× {nama_item(k)}" for k, n in bahan.items())
        label = " *(tanpa pola)*" if r["tipe"] == "shapeless" else ""
        baris += [
            f"### {r['judul']}{label}",
            "",
            f"![Resep {r['judul']}](resep/{r['id']}.png)",
            "",
            f"- **Bahan:** {daftar}",
            f"- **Hasil:** {r['jumlah']}× {nama_item(r['hasil'])}",
            f"- {r['catatan']}",
            "",
        ]
    baris += ["## Tungku & Api Unggun", ""]
    nama_tag = {"furnace": "Tungku", "smoker": "Smoker", "campfire": "Api Unggun", "soul_campfire": "Api Unggun Jiwa", "blast_furnace": "Tanur Tiup"}
    for r in RESEP_TUNGKU:
        baris += [
            f"### {r['judul']}",
            "",
            f"![Resep {r['judul']}](resep/{r['id']}.png)",
            "",
            f"- **Masukan:** {nama_item(r['masuk'])} → **Hasil:** {nama_item(r['hasil'])}",
            f"- **Alat:** {', '.join(nama_tag[t] for t in r['tag'])}",
            f"- {r['catatan']}",
            "",
        ]
    with open(os.path.join(DOCS, "RESEP.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(baris))


# ===========================================================================
def main():
    tekstur_item = {
        "plastik": ikon_plastik(),
        "daun_palem": ikon_daun_palem(),
        "besi_tua": ikon_besi_tua(),
        "gigi_hiu": ikon_gigi_hiu(),
        "daging_hiu_mentah": ikon_daging(False),
        "daging_hiu_matang": ikon_daging(True),
        "botol_kosong": ikon_botol(),
        "air_laut": ikon_botol("#2f8f8f", salju=True),
        "air_bersih": ikon_botol("#4fc3f7"),
        "tombak": ikon_tombak(),
        "buku_catatan": ikon_buku(),
        "pecahan_portal": ikon_pecahan_portal(),
        "inti_portal": ikon_inti_portal(),
    }
    for t in range(1, 6):
        tekstur_item[f"kail_t{t}"] = ikon_kail(t)
    hilang = {it["id"] for it in ITEMS} - set(tekstur_item)
    assert not hilang, f"tekstur item belum dibuat: {hilang}"
    for nama, img in tekstur_item.items():
        simpan(img, RP, "textures", "items", f"{nama}.png")

    tekstur_blok = {
        "fondasi_rakit": tex_fondasi_rakit(),
        "fondasi_kuat": tex_fondasi_kuat(),
        "penyaring_samping": tex_penyaring_samping(),
        "penyaring_atas_kosong": tex_penyaring_atas("kosong"),
        "penyaring_atas_proses": tex_penyaring_atas("proses"),
        "penyaring_atas_siap": tex_penyaring_atas("siap"),
        "penampung_samping": tex_penampung_samping(),
        "penampung_atas_kosong": tex_penampung_atas(0),
        "penampung_atas_sedikit": tex_penampung_atas(1),
        "penampung_atas_penuh": tex_penampung_atas(2),
        "pot_samping": tex_pot_samping(),
        "pot_tanah": tex_pot_tanah(),
        "tanaman_bibit": tex_tanaman("bibit"),
        "tanaman_tumbuh": tex_tanaman("tumbuh"),
        "tanaman_gandum": tex_tanaman("gandum"),
        "tanaman_kentang": tex_tanaman("kentang"),
        "tanaman_wortel": tex_tanaman("wortel"),
        "tanaman_bit": tex_tanaman("bit"),
        "layar_kain": tex_layar_kain(),
        "layar_tiang": tex_kayu_polos("#7a5530"),
        "kemudi": tex_kayu_polos("#8a5a30"),
    }
    for nama, img in tekstur_blok.items():
        simpan(img, RP, "textures", "blocks", f"{nama}.png")

    simpan(tekstur_hiu(), RP, "textures", "entity", "hiu.png")
    simpan(tekstur_puing(), RP, "textures", "entity", "puing.png")
    for nama, ident, tw, th, bones in (
        ("hiu", "geometry.rakit.hiu", 128, 64, HIU),
        ("puing", "geometry.rakit.puing", 64, 64, PUING),
    ):
        path = os.path.join(RP, "models", "entity", f"{nama}.geo.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(geometri_entity(ident, tw, th, bones), f, indent=2)
            f.write("\n")

    ikon = ikon_pack()
    simpan(ikon, BP, "pack_icon.png")
    simpan(ikon, RP, "pack_icon.png")
    simpan(banner(), DOCS, "banner.png")

    semua_ikon = daftar_ikon(tekstur_item, tekstur_blok)
    for r in RESEP:
        simpan(gambar_resep(r, semua_ikon), DOCS, "resep", f"{r['id']}.png")
    for r in RESEP_TUNGKU:
        simpan(gambar_resep_tungku(r, semua_ikon), DOCS, "resep", f"{r['id']}.png")
    tulis_resep_md()

    # Ikon besar untuk tabel di README.
    for kunci, img in semua_ikon.items():
        if kunci.startswith("rakit:"):
            simpan(img.resize((32, 32), Image.NEAREST), DOCS, "ikon", f"{kunci.split(':')[1]}.png")
    print("Aset visual selesai dibuat.")


if __name__ == "__main__":
    main()
