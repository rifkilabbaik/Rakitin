"""Kerangka model detail ala Yes Steve Model (YSM) untuk addon Waguri.

Isi modul ini:
  * TULANG     : kerangka tulang standar. Nama & pivot tulang utama SAMA dengan
                 skin vanilla (root, waist, body, head, rightArm, ...), sehingga
                 semua animasi vanilla tetap bekerja. Ditambah tulang khas YSM:
                 siku (rightForearm/leftForearm), lutut (rightShin/leftShin),
                 tulang fisika rambut/ekor kuda/rok/pita, serta tulang wajah
                 (mata, kelopak, alis, ekspresi).
  * Model      : pembangun model (kubus box-UV, kubus cermin, bidang datar).
  * kuas_*     : pelukis tekstur HD (K piksel per unit model).
  * wajah      : mata anime terpisah (bisa berkedip & berekspresi).
  * bangun()   : menata UV, melukis tekstur, menghasilkan geometri Bedrock.
  * render()   : perender 3D perangkat lunak (proyeksi ortografis + z-buffer)
                 yang menghormati rotasi kubus, untuk pratinjau & ulasan.
  * animasi    : animasi fisika/kedip/siku/lutut yang memakai tulang di atas.

KONVENSI KOORDINAT (ruang model Bedrock, satuan "unit"; 16 unit = 1 blok)
  * y ke atas, kaki di y = 0, puncak kepala standar di y = 32.5.
  * Depan model menghadap -z (wajah di z = -4.5 untuk kepala 9x9x9).
  * x negatif = sisi KANAN tubuh karakter (tampak di kiri layar bila dilihat
    dari depan). Tulang "right*" berada di x negatif.
  * Rotasi kubus [rx, ry, rz] derajat terhadap pivot, aturan Bedrock:
      - rx positif: ujung bawah kubus berayun ke BELAKANG (+z).
      - rz positif: ujung bawah kubus berayun ke kanan karakter (-x).
"""

import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

K = 4  # piksel tekstur per unit model (YSM umumnya memakai tekstur HD)
LEBAR_TEKSTUR = 128  # lebar tekstur dalam unit (=> 512 piksel); tinggi otomatis

KOSONG = (0, 0, 0, 0)


# ===========================================================================
# Warna
# ===========================================================================
def rgb(h, a=255):
    """'#rrggbb' -> (r, g, b, a). Tuple diteruskan apa adanya."""
    if isinstance(h, tuple):
        return h
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ubah(w, f):
    """Terangkan (f > 1) / gelapkan (f < 1)."""
    r, g, b, a = rgb(w)
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


def campur(a, b, t):
    a, b = rgb(a), rgb(b)
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(4))


def hexs(w):
    w = rgb(w)
    return "#%02x%02x%02x" % w[:3]


# ===========================================================================
# Kerangka tulang
# ===========================================================================
# (nama, induk, pivot)
TULANG = [
    ("root", None, [0, 0, 0]),
    ("waist", "root", [0, 12, 0]),
    ("body", "waist", [0, 24, 0]),
    ("head", "body", [0, 24, 0]),
    ("rightArm", "body", [-5, 22, 0]),
    ("rightForearm", "rightArm", [-5.5, 17, 0]),
    ("rightItem", "rightArm", [-6, 15, 1]),
    ("leftArm", "body", [5, 22, 0]),
    ("leftForearm", "leftArm", [5.5, 17, 0]),
    ("leftItem", "leftArm", [6, 15, 1]),
    ("rightLeg", "root", [-1.9, 12, 0]),
    ("rightShin", "rightLeg", [-1.9, 6, 0]),
    ("leftLeg", "root", [1.9, 12, 0]),
    ("leftShin", "leftLeg", [1.9, 6, 0]),
    # --- tulang fisika (bergoyang) ---
    ("rambut_belakang", "head", [0, 30, 4.5]),
    ("rambut_belakang2", "rambut_belakang", [0, 21, 5.0]),
    ("rambut_kanan", "head", [-4.5, 29, -1]),
    ("rambut_kiri", "head", [4.5, 29, -1]),
    ("ahoge", "head", [0, 32.5, -1]),
    ("ekor_kuda", "head", [0, 30, 5]),
    ("ekor_kuda2", "ekor_kuda", [0, 23, 6.5]),
    ("pita", "body", [0, 20, -2.5]),
    ("rok", "waist", [0, 12, 0]),
    ("rok_depan", "rok", [0, 12, -2]),
    ("rok_belakang", "rok", [0, 12, 2]),
    ("rok_kanan", "rok", [-3.5, 12, 0]),
    ("rok_kiri", "rok", [3.5, 12, 0]),
    ("jubah", "body", [0, 23, 2.5]),
    # --- wajah ---
    ("mata", "head", [0, 27, -4.5]),
    ("kelopak", "head", [0, 27, -4.6]),
    ("alis", "head", [0, 29, -4.6]),
    ("ekspresi_senang", "head", [0, 27, -4.7]),
]
NAMA_TULANG = [t[0] for t in TULANG]

# pasangan tulang kanan <-> kiri untuk Model.cermin()
PASANGAN = {}
for _a, _b in [("rightArm", "leftArm"), ("rightForearm", "leftForearm"), ("rightItem", "leftItem"),
               ("rightLeg", "leftLeg"), ("rightShin", "leftShin"), ("rambut_kanan", "rambut_kiri"),
               ("rok_kanan", "rok_kiri")]:
    PASANGAN[_a] = _b
    PASANGAN[_b] = _a

# Proporsi tubuh standar (dipakai helper & dokumentasi).
#   kepala 9x9x9 : x -4.5..4.5, y 23.5..32.5, z -4.5..4.5 (wajah di z = -4.5)
#   leher        : y 23..24
#   putri        : badan lebar 7 (x -3.5..3.5), tebal 4, y 12..23
#                  lengan lebar 3: lengan atas y 17..23, lengan bawah 13..17, tangan 11..13
#                  (x -7..-4 untuk lengan kanan)
#                  kaki lebar 3 (x -3.4..-0.4): paha y 6..12, betis+kaki y 0..6
#   putra        : badan lebar 8 (x -4..4), tebal 4, y 12..24; lengan lebar 4 (x -8..-4)
#                  kaki lebar 4 (x -3.9..0.1)
WAJAH_Z = -4.5


# ===========================================================================
# Kuas (pelukis sisi). Tanda tangan: f(img, X, Y, W, H, rnd) dalam piksel.
# ===========================================================================
def titik(img, x, y, w):
    x, y = int(x), int(y)
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), rgb(w))


def isi_rect(img, X, Y, W, H, w):
    if W > 0 and H > 0:
        ImageDraw.Draw(img).rectangle([X, Y, X + W - 1, Y + H - 1], fill=rgb(w))


def kuas_polos(warna, derau=0.03, gradasi=0.0, tepi=None, tebal_tepi=1):
    """Warna rata + derau halus; gradasi gelap ke bawah; tepi opsional."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            g = 1 - gradasi * (y / max(1, H - 1))
            for x in range(W):
                img.putpixel((X + x, Y + y), ubah(c, g * (1 + rnd.uniform(-derau, derau))))
        if tepi:
            kuas_tepi(tepi, tebal_tepi)(img, X, Y, W, H, rnd)
    return f


def kuas_kosong():
    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, KOSONG)
    return f


def kuas_lapis(*kuas):
    """Gabungkan beberapa kuas berurutan."""
    def f(img, X, Y, W, H, rnd):
        for k in kuas:
            k(img, X, Y, W, H, rnd)
    return f


def kuas_tepi(warna, tebal=1, sisi="lrtb"):
    """Garis tepi (outline) di sisi muka: l, r, t, b."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for i in range(tebal):
            if "t" in sisi:
                isi_rect(img, X, Y + i, W, 1, c)
            if "b" in sisi:
                isi_rect(img, X, Y + H - 1 - i, W, 1, c)
            if "l" in sisi:
                isi_rect(img, X + i, Y, 1, H, c)
            if "r" in sisi:
                isi_rect(img, X + W - 1 - i, Y, 1, H, c)
    return f


def kuas_kain(warna, lipatan=0.07, gradasi=0.12, tepi=None):
    """Kain: warna dasar + bayangan lipatan vertikal lembut + gradasi."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        fase = rnd.uniform(0, 6.28)
        for x in range(W):
            lip = 1 + lipatan * math.sin(x * 0.55 + fase) * (0.6 + 0.4 * math.sin(x * 0.17))
            for y in range(H):
                g = 1 - gradasi * (y / max(1, H - 1))
                img.putpixel((X + x, Y + y), ubah(c, lip * g * (1 + rnd.uniform(-0.015, 0.015))))
        if tepi:
            kuas_tepi(tepi)(img, X, Y, W, H, rnd)
    return f


def kuas_rambut(r, kilau=0.28, gradasi=0.18, lebar_helai=3):
    """Rambut anime: helai vertikal, pita kilau ("angel ring"), makin gelap ke bawah.

    r = (warna_utama, warna_gelap, warna_kilau)."""
    c, g, t = rgb(r[0]), rgb(r[1]), rgb(r[2])

    def f(img, X, Y, W, H, rnd):
        offs = [rnd.randint(0, lebar_helai - 1) for _ in range(W // lebar_helai + 2)]
        yk = int(H * kilau)
        for x in range(W):
            j = (x + offs[x // lebar_helai]) % (lebar_helai * 2)
            dasar = g if j == 0 else (campur(c, g, 0.35) if j == 1 else c)
            for y in range(H):
                gd = 1 - gradasi * (y / max(1, H - 1))
                w = ubah(dasar, gd)
                if kilau is not None and abs(y - yk) <= max(1, H // 18) and (x // 2 + y) % 3 != 0 and H >= 8:
                    w = campur(w, t, 0.75)
                img.putpixel((X + x, Y + y), ubah(w, 1 + rnd.uniform(-0.02, 0.02)))
    return f


def kuas_ujung_rambut(r, panjang_min=0.6, pola="runcing", **kw):
    """Rambut dengan tepi bawah runcing ('runcing') / bergelombang ('gelombang') /
    lurus berponi ('rata'); bagian di bawah ujung transparan."""
    dasar = kuas_rambut(r, **kw)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        for x in range(W):
            if pola == "gelombang":
                t = 0.5 + 0.5 * math.sin(x / max(1, W) * 6.28 * 1.5 + 0.8)
            elif pola == "rata":
                t = 1.0 if (x % 6) else 0.85
            else:  # runcing: gigi gergaji
                p = (x % 6) / 5.0
                t = 1 - abs(p - 0.5) * 2
            p_ = int(H * (panjang_min + (1 - panjang_min) * t))
            isi_rect(img, X + x, Y + p_, 1, H - p_, KOSONG)
    return f


def kuas_poni(r, ujung=(0.45, 1.0), helai_px=5):
    """Poni: helai-helai runcing; ujung=(min, maks) panjang relatif tinggi muka."""
    dasar = kuas_rambut(r, kilau=0.18)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        n = max(1, W // helai_px)
        for x in range(W):
            i = min(n - 1, x * n // W)
            p = (x - i * W / n) / (W / n)  # 0..1 di dalam helai
            puncak = ujung[0] + (ujung[1] - ujung[0]) * (0.5 + 0.5 * math.sin(i * 2.4 + 1.1))
            panjang = puncak * (1 - abs(p - 0.5) * 0.9)
            p_ = int(H * panjang)
            isi_rect(img, X + x, Y + p_, 1, H - p_, KOSONG)
        # garis gelap pemisah helai
        for i in range(1, n):
            xx = X + int(i * W / n)
            for y in range(int(H * 0.15), H):
                if img.getpixel((xx, Y + y))[3]:
                    img.putpixel((xx, Y + y), ubah(rgb(r[1]), 0.9))
    return f


def kuas_lipit(warna, gelap, jarak=4, gradasi=0.12, tepi_bawah=True):
    """Kain berlipit (rok): garis lipit gelap & sisi terang."""
    c, g = rgb(warna), rgb(gelap)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            k = x % jarak
            dasar = g if k == 0 else (ubah(c, 1.08) if k == 1 else c)
            for y in range(H):
                gd = 1 - gradasi * (y / max(1, H - 1))
                img.putpixel((X + x, Y + y), ubah(dasar, gd * (1 + rnd.uniform(-0.015, 0.015))))
        if tepi_bawah:
            isi_rect(img, X, Y + H - 1, W, 1, ubah(g, 0.85))
    return f


def kuas_strip_h(warna, y0, tebal, x0=0.0, x1=1.0):
    """Strip horizontal. y0/tebal dalam piksel; x0/x1 relatif (0..1).
    y0 negatif = dihitung dari bawah."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        yy = y0 if y0 >= 0 else H + y0
        isi_rect(img, X + int(W * x0), Y + yy, int(W * x1) - int(W * x0), tebal, c)
    return f


def kuas_strip_v(warna, x0, x1, y0=0.0, y1=1.0):
    """Strip vertikal, semua koordinat relatif (0..1)."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X + int(W * x0), Y + int(H * y0), int(W * x1) - int(W * x0), int(H * y1) - int(H * y0), c)
    return f


def kuas_rect(warna, x0, y0, x1, y1):
    """Persegi dengan koordinat relatif (0..1)."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X + int(W * x0), Y + int(H * y0), max(1, int(W * x1) - int(W * x0)),
                 max(1, int(H * y1) - int(H * y0)), c)
    return f


def kuas_poligon(warna, titik_rel):
    """Poligon terisi, titik relatif (0..1)."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        pts = [(X + px * (W - 1), Y + py * (H - 1)) for px, py in titik_rel]
        ImageDraw.Draw(img).polygon(pts, fill=c)
    return f


def kuas_elips(warna, x0, y0, x1, y1):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        ImageDraw.Draw(img).ellipse([X + x0 * (W - 1), Y + y0 * (H - 1), X + x1 * (W - 1), Y + y1 * (H - 1)], fill=c)
    return f


def kuas_garis(warna, titik_rel, tebal=1):
    """Polyline, titik relatif."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        pts = [(X + px * (W - 1), Y + py * (H - 1)) for px, py in titik_rel]
        ImageDraw.Draw(img).line(pts, fill=c, width=tebal)
    return f


def kuas_kancing(warna, x=0.5, y0=0.15, y1=0.9, jumlah=3, ukuran=2, kilap=None):
    """Deret kancing vertikal (posisi relatif), ukuran dalam piksel."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for i in range(jumlah):
            t = 0.5 if jumlah == 1 else i / (jumlah - 1)
            cy = Y + int(H * (y0 + (y1 - y0) * t))
            cx = X + int(W * x) - ukuran // 2
            isi_rect(img, cx, cy, ukuran, ukuran, c)
            if kilap:
                titik(img, cx, cy, kilap)
    return f


def kuas_kerah_pelaut(putih, garis, dalam=0.5, lebar_px=None, garis_px=1):
    """Kerah pelaut (V) di muka depan badan."""
    cp, cg = rgb(putih), rgb(garis)

    def f(img, X, Y, W, H, rnd):
        lb = lebar_px or max(3, W // 6)
        d = int(H * dalam)
        for y in range(d):
            t = y / max(1, d)
            kiri = int((W / 2) * t * 0.98)
            for i in range(lb):
                w = cg if i >= lb - garis_px else cp
                titik(img, X + kiri + i, Y + y, w)
                titik(img, X + W - 1 - kiri - i, Y + y, w)
    return f


def kuas_gelombang_tepi(warna, amplitudo=2, periode=8, dari_bawah=True):
    """Potong tepi bawah (atau atas) dengan gelombang (renda / rambut ikal)."""
    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            a = int(amplitudo * (0.5 + 0.5 * math.sin(x / periode * 6.28)))
            if dari_bawah:
                isi_rect(img, X + x, Y + H - a, 1, a, KOSONG)
            else:
                isi_rect(img, X + x, Y, 1, a, KOSONG)
    return f


def kuas_kulit(kulit, gradasi=0.06):
    return kuas_polos(kulit, derau=0.012, gradasi=gradasi)


def kuas_per_sisi(**sisi):
    """Kuas berbeda per sisi: depan, belakang, kanan, kiri, atas, bawah, '_' (bawaan)."""
    d = dict(sisi)
    if "lain" in d:
        d["_"] = d.pop("lain")
    return d


# ===========================================================================
# Wajah anime (mata terpisah sebagai bidang datar -> bisa berkedip & berekspresi)
# ===========================================================================
def kuas_wajah(kulit, rambut0, mulut="senyum", pipi=True, hidung=True, garis_rambut=True, y_mulut=0.78):
    """Muka depan kepala: kulit, rona pipi, hidung, mulut. Mata TIDAK dilukis di
    sini (dipasang lewat pasang_mata)."""
    kc = rgb(kulit)
    bay = ubah(kc, 0.9)
    mc = rgb("#b64e5a")
    lidah = rgb("#e88b97")
    gigi = rgb("#ffffff")
    pink = rgb("#f4a3ae")

    def f(img, X, Y, W, H, rnd):
        kuas_kulit(kulit, 0.04)(img, X, Y, W, H, rnd)
        if garis_rambut:
            for x in range(W):
                tinggi = int(H * 0.12) + (2 if (x // 3) % 2 else 0)
                isi_rect(img, X + x, Y, 1, tinggi, ubah(rgb(rambut0), 0.95))
        cx = X + W // 2
        if pipi:
            yy = Y + int(H * 0.66)
            for sx in (-1, 1):
                x0 = cx + sx * int(W * 0.30) - 2
                for i in range(5):
                    titik(img, x0 + i, yy, campur(kc, pink, 0.85))
                    if 0 < i < 4:
                        titik(img, x0 + i, yy + 1, campur(kc, pink, 0.5))
                for i in range(0, 5, 2):
                    titik(img, x0 + i, yy - 1, campur(kc, pink, 0.6))
        if hidung:
            titik(img, cx, Y + int(H * 0.68), bay)
            titik(img, cx - 1, Y + int(H * 0.69), ubah(kc, 0.94))
        my = Y + int(H * y_mulut)
        if mulut == "senyum":
            for dx, dy in ((-3, 0), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 0)):
                titik(img, cx + dx, my + dy, mc)
        elif mulut == "tawa":
            isi_rect(img, cx - 3, my, 6, 1, mc)
            isi_rect(img, cx - 2, my + 1, 4, 1, mc)
            isi_rect(img, cx - 1, my + 1, 2, 1, lidah)
            isi_rect(img, cx - 1, my + 2, 2, 1, mc)
        elif mulut == "lebar":
            isi_rect(img, cx - 4, my, 8, 1, mc)
            isi_rect(img, cx - 4, my + 1, 8, 1, gigi)
            isi_rect(img, cx - 3, my + 2, 6, 1, mc)
            titik(img, cx - 5, my - 1, mc)
            titik(img, cx + 4, my - 1, mc)
        elif mulut == "datar":
            isi_rect(img, cx - 2, my + 1, 4, 1, ubah(mc, 0.9))
        elif mulut == "kecil":
            isi_rect(img, cx - 1, my + 1, 2, 1, mc)
        # bayangan dagu
        isi_rect(img, X, Y + H - 1, W, 1, ubah(kc, 0.95))
    return f


def kuas_mata(iris, gaya="putri", sisi="kanan"):
    """Lukisan satu mata anime (bidang datar). gaya: putri | putra | tajam | sayu.

    Bulu mata atas tebal, iris bergradasi gelap->terang, pupil, 2 kilau putih."""
    ic = rgb(iris)
    gelap = ubah(ic, 0.45)
    terang = campur(ic, "#ffffff", 0.35)
    lash = rgb("#22161c")
    putih = rgb("#fbfbff")

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, KOSONG)
        top = 2 if gaya in ("putri", "sayu") else 1
        # sklera (putih) tipis di sisi luar
        isi_rect(img, X + 1, Y + top, W - 2, H - top - 1, putih)
        # iris
        ix0, ix1 = X + 1 + (W - 2) // 6, X + W - 1 - (W - 2) // 6
        for y in range(Y + top, Y + H - 1):
            t = (y - Y - top) / max(1, H - top - 2)
            w = campur(gelap, terang, t ** 0.9)
            isi_rect(img, ix0, y, ix1 - ix0, 1, w)
        # pupil
        pc = (ix0 + ix1) // 2
        isi_rect(img, pc - 1, Y + top + (H - top) // 3, 2, max(2, (H - top) // 3), ubah(gelap, 0.6))
        # kilau
        kx = ix0 + 1 if sisi == "kanan" else ix1 - 3
        isi_rect(img, kx, Y + top + 1, 2, 2, putih)
        titik(img, ix1 - 2 if sisi == "kanan" else ix0 + 1, Y + H - 3, campur(putih, ic, 0.2))
        # bulu mata atas
        tebal = 2 if gaya in ("putri", "sayu") else 1
        isi_rect(img, X, Y + top - tebal, W, tebal, lash)
        if gaya == "putri":  # ujung bulu mata melengkung ke luar
            ox = X - 1 if sisi == "kanan" else X + W
            titik(img, ox, Y + top - 1, lash)
            titik(img, X if sisi == "kanan" else X + W - 1, Y + top, lash)
        if gaya == "tajam":  # kelopak atas turun ke arah dalam
            dx = X + W - 2 if sisi == "kanan" else X
            isi_rect(img, dx, Y + top, 2, 1, lash)
        if gaya == "sayu":  # mata setengah terpejam
            isi_rect(img, X + 1, Y + top, W - 2, max(1, (H - top) // 4), ubah(lash, 1.4))
        # garis bawah tipis
        isi_rect(img, X + 2, Y + H - 1, W - 4, 1, ubah(lash, 2.2))
    return f


def kuas_kelopak(kulit, sisi="kanan"):
    """Mata terpejam (dipakai saat berkedip)."""
    kc = rgb(kulit)
    lash = rgb("#22161c")

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, kc)
        y = Y + int(H * 0.62)
        for x in range(W):
            lengkung = 1 if 0 < x < W - 1 else 0
            titik(img, X + x, y + lengkung, lash)
        titik(img, X - 0 if sisi == "kanan" else X + W - 1, y - 1, lash)
    return f


def kuas_senang(kulit):
    """Mata bahagia '^ ^' (ekspresi senang)."""
    kc = rgb(kulit)
    lash = rgb("#22161c")

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, kc)
        tengah = X + W // 2
        for i in range(W // 2 + 1):
            yy = Y + int(H * 0.35) + int(i * (H * 0.4) / max(1, W // 2))
            titik(img, tengah - i, yy, lash)
            titik(img, tengah + i, yy, lash)
            titik(img, tengah - i, yy + 1, lash)
            titik(img, tengah + i, yy + 1, lash)
    return f


def kuas_alis(warna, gaya="putri", sisi="kanan"):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, KOSONG)
        for x in range(W):
            t = x / max(1, W - 1)
            if gaya == "tajam":
                naik = t if sisi == "kanan" else 1 - t  # alis turun ke tengah
                yy = Y + int((H - 2) * naik)
            else:
                yy = Y + int((H - 2) * (1 - math.sin(t * math.pi)) * 0.8)
            isi_rect(img, X + x, yy, 1, 2 if gaya != "putri" else 1, c)
    return f


def kuas_mulut_senang():
    mc = rgb("#b64e5a")
    lidah = rgb("#e88b97")

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, KOSONG)
        isi_rect(img, X + 1, Y, W - 2, 1, mc)
        isi_rect(img, X + 1, Y + 1, W - 2, H - 2, ubah(mc, 0.8))
        isi_rect(img, X + 2, Y + H - 2, W - 4, 1, lidah)
        isi_rect(img, X + 2, Y + H - 1, W - 4, 1, mc)
    return f


# ===========================================================================
# Model
# ===========================================================================
class Model:
    """Model satu karakter.

    m = Model("kaoruko", "Kaoruko Waguri", "Kaoruko Waguri (Seragam Kikyo)",
              skala=0.84, deskripsi="...")
    m.kubus("head", [-4.5, 23.5, -4.5], [9, 9, 9], kuas)  # kuas: fungsi atau dict per sisi
    m.cermin("rightArm", [-7, 17, -1.5], [3, 6, 3], kuas)  # + salinan di leftArm
    m.datar("mata", [-3.5, 25.5, -4.55], 2, 2.5, kuas)    # bidang menghadap depan
    """

    def __init__(self, id_, nama, nama_id, skala=1.0, deskripsi=""):
        self.id = id_
        self.nama = nama
        self.nama_id = nama_id
        self.skala = skala
        self.deskripsi = deskripsi
        self.daftar = []  # semua kubus (dict)
        self.rnd = random.Random(sum(map(ord, id_)) * 7919)

    # -- penambah -----------------------------------------------------------
    def kubus(self, bone, origin, size, kuas, inflate=0.0, rot=None, pivot=None, mirror=False, _uv_dari=None):
        """Tambah kubus box-UV. size boleh pecahan; UV memakai ceil(size).

        rot/pivot: rotasi kubus (derajat) terhadap pivot (default: pusat kubus)."""
        assert bone in NAMA_TULANG, f"tulang tidak dikenal: {bone}"
        if rot and pivot is None:
            pivot = [origin[i] + size[i] / 2 for i in range(3)]
        k = dict(bone=bone, origin=[float(v) for v in origin], size=[float(v) for v in size], kuas=kuas,
                 inflate=float(inflate), rot=list(rot) if rot else None, pivot=list(pivot) if pivot else None,
                 mirror=mirror, datar=False, uv_dari=_uv_dari)
        self.daftar.append(k)
        return k

    def cermin(self, bone, origin, size, kuas, inflate=0.0, rot=None, pivot=None):
        """Tambah kubus di sisi kanan (x negatif) & salinan cerminnya di sisi kiri.

        Tulang ditukar otomatis (rightArm->leftArm, rambut_kanan->rambut_kiri, ...);
        tulang tengah (head, body, ...) dipakai keduanya. Salinan memakai UV yang
        sama dengan flag mirror."""
        if rot and pivot is None:
            pivot = [origin[i] + size[i] / 2 for i in range(3)]
        a = self.kubus(bone, origin, size, kuas, inflate, rot, pivot)
        o2 = [-(origin[0] + size[0]), origin[1], origin[2]]
        r2 = [rot[0], -rot[1], -rot[2]] if rot else None
        p2 = [-pivot[0], pivot[1], pivot[2]] if pivot else None
        b = self.kubus(PASANGAN.get(bone, bone), o2, size, kuas, inflate, r2, p2, mirror=True, _uv_dari=a)
        return a, b

    def datar(self, bone, origin, w, h, kuas, dua_sisi=False):
        """Bidang datar menghadap depan (-z) di z = origin[2]; origin = pojok kiri-bawah."""
        assert bone in NAMA_TULANG, f"tulang tidak dikenal: {bone}"
        k = dict(bone=bone, origin=[float(v) for v in origin], size=[float(w), float(h), 0.0], kuas=kuas,
                 inflate=0.0, rot=None, pivot=None, mirror=False, datar=True, dua_sisi=dua_sisi, uv_dari=None)
        self.daftar.append(k)
        return k

    def jumlah_kubus(self):
        return len(self.daftar)


# ===========================================================================
# Helper wajah standar (kepala 9x9x9 di [-4.5, 23.5, -4.5])
# ===========================================================================
def pasang_mata(m, kulit, iris, rambut0, gaya="putri", lebar=2.25, tinggi=2.5, jarak=0.75, y_bawah=25.25,
                alis=True, x_offset=0.0):
    """Pasang mata (tulang 'mata'), kelopak kedip ('kelopak'), alis ('alis') dan
    mata bahagia ('ekspresi_senang') di depan wajah kepala standar.

    lebar/tinggi: ukuran satu mata (unit). jarak: setengah jarak antar mata dari
    garis tengah. y_bawah: tepi bawah mata."""
    z = WAJAH_Z
    for sisi, sx in (("kanan", -1), ("kiri", 1)):
        x0 = x_offset + (-(jarak + lebar) if sx < 0 else jarak)
        m.datar("mata", [x0, y_bawah, z - 0.05], lebar, tinggi, kuas_mata(iris, gaya, sisi))
        m.datar("kelopak", [x0 - 0.1, y_bawah - 0.1, z - 0.08], lebar + 0.2, tinggi + 0.2, kuas_kelopak(kulit, sisi))
        m.datar("ekspresi_senang", [x0 - 0.1, y_bawah - 0.1, z - 0.1], lebar + 0.2, tinggi + 0.2, kuas_senang(kulit))
        if alis:
            m.datar("alis", [x0, y_bawah + tinggi + 0.35, z - 0.06], lebar, 0.75, kuas_alis(ubah(rgb(rambut0), 0.85), gaya, sisi))
    # mulut bahagia (terbuka) ikut ekspresi senang
    m.datar("ekspresi_senang", [-0.75, 24.25, z - 0.1], 1.5, 0.75, kuas_mulut_senang())


# ===========================================================================
# Bangun: UV + tekstur + geometri
# ===========================================================================
def kotak_uv(u, v, w, h, d):
    """Sisi kubus pada tata letak box-UV Bedrock (satuan unit)."""
    return {
        "atas": (u + d, v, w, d),
        "bawah": (u + d + w, v, w, d),
        "kanan": (u, v + d, d, h),       # sisi -x (kanan karakter)
        "depan": (u + d, v + d, w, h),   # sisi -z
        "kiri": (u + d + w, v + d, d, h),  # sisi +x
        "belakang": (u + d + w + d, v + d, w, h),  # sisi +z
    }


def ukuran_uv(size):
    return [max(1, math.ceil(s - 1e-6)) for s in size]


class Penata:
    """Penempatan UV (rak). Tinggi tumbuh otomatis."""

    def __init__(self, lebar):
        self.x = self.y = self.t = 0
        self.lebar = lebar
        self.maks_y = 0

    def tempat(self, fw, fh):
        assert fw <= self.lebar, f"kubus terlalu lebar untuk tekstur ({fw})"
        if self.x + fw > self.lebar:
            self.x, self.y, self.t = 0, self.y + self.t, 0
        u, v = self.x, self.y
        self.x += fw
        self.t = max(self.t, fh)
        self.maks_y = max(self.maks_y, v + fh)
        return u, v


def bangun(m):
    """Kembalikan (geometri_json, tekstur PIL, info).

    Tekstur: LEBAR_TEKSTUR unit x tinggi (pangkat dua) unit, K piksel per unit."""
    penata = Penata(LEBAR_TEKSTUR)
    # 1) tata letak (urut dari yang terbesar agar rapat)
    urutan = sorted(range(len(m.daftar)), key=lambda i: -(_luas(m.daftar[i])))
    for i in urutan:
        k = m.daftar[i]
        if k["uv_dari"] is not None:
            continue
        w, h, d = ukuran_uv(k["size"])
        if k["datar"]:
            k["uv"] = penata.tempat(w, h)
        else:
            k["uv"] = penata.tempat(2 * (w + d), h + d)
    tinggi = 16
    while tinggi < penata.maks_y:
        tinggi *= 2
    img = Image.new("RGBA", (LEBAR_TEKSTUR * K, tinggi * K), KOSONG)
    # 2) lukis
    for k in m.daftar:
        if k["uv_dari"] is not None:
            k["uv"] = k["uv_dari"]["uv"]
            continue
        u, v = k["uv"]
        w, h, d = ukuran_uv(k["size"])
        kuas = k["kuas"]
        if k["datar"]:
            f = kuas.get("depan", kuas.get("_")) if isinstance(kuas, dict) else kuas
            f(img, u * K, v * K, w * K, h * K, m.rnd)
            continue
        for nama, (fx, fy, fw, fh) in kotak_uv(u, v, w, h, d).items():
            f = kuas.get(nama, kuas.get("_")) if isinstance(kuas, dict) else kuas
            if f is None:
                f = kuas_kosong()
            f(img, fx * K, fy * K, fw * K, fh * K, m.rnd)
    # 3) geometri
    tulang = {}
    for k in m.daftar:
        u, v = k["uv"]
        w, h, d = ukuran_uv(k["size"])
        if k["datar"]:
            # bidang datar: ukuran asli (pecahan) dipetakan ke region UV utuh
            uvm = {"north": {"uv": [u, v], "uv_size": [w, h]}}
            if k.get("dua_sisi"):
                uvm["south"] = {"uv": [u + w, v], "uv_size": [-w, h]}
            c = {"origin": _r(k["origin"]), "size": _r([k["size"][0], k["size"][1], 0]), "uv": uvm}
        else:
            c = {"origin": _r(k["origin"]), "size": _r(k["size"]), "uv": [u, v]}
            if k["size"] != [float(x) for x in ukuran_uv(k["size"])]:
                # UV memakai ukuran bulat: pakai UV per sisi supaya tekstur tidak bergeser
                c["uv"] = _uv_per_sisi(u, v, w, h, d, k["mirror"])
                c.pop("mirror", None)
            elif k["mirror"]:
                c["mirror"] = True
        if k["inflate"]:
            c["inflate"] = round(k["inflate"], 4)
        if k["rot"]:
            c["rotation"] = _r(k["rot"])
            c["pivot"] = _r(k["pivot"])
        tulang.setdefault(k["bone"], []).append(c)
    bones = []
    for nama, induk, pivot in TULANG:
        b = {"name": nama, "pivot": pivot}
        if induk:
            b["parent"] = induk
        if nama in tulang:
            b["cubes"] = tulang[nama]
        bones.append(b)
    geo = {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.waguri.{m.id}",
                "texture_width": LEBAR_TEKSTUR, "texture_height": tinggi,
                "visible_bounds_width": 3, "visible_bounds_height": 3.5,
                "visible_bounds_offset": [0, 1.5, 0],
            },
            "bones": bones,
        }],
    }
    info = {"kubus": len(m.daftar), "tekstur_unit": (LEBAR_TEKSTUR, tinggi), "terpakai_y": penata.maks_y}
    return geo, img, info


def _luas(k):
    w, h, d = ukuran_uv(k["size"])
    return w * h if k["datar"] else 2 * (w + d) * (h + d)


def _r(v):
    return [round(float(x), 4) for x in v]


def _uv_per_sisi(u, v, w, h, d, mirror):
    """UV per sisi (Bedrock) dari region box-UV berukuran bulat."""
    s = kotak_uv(u, v, w, h, d)
    # Region (u, v+d) pada box-UV adalah sisi "east" Bedrock (= sisi -x / kanan karakter,
    # sama seperti tata letak skin), region (u+d+w, v+d) adalah "west".
    peta = {"east": "kanan", "north": "depan", "west": "kiri", "south": "belakang", "up": "atas", "down": "bawah"}
    if mirror:
        peta["west"], peta["east"] = "kanan", "kiri"
    hasil = {}
    for arah, nama in peta.items():
        fx, fy, fw, fh = s[nama]
        if mirror:
            hasil[arah] = {"uv": [fx + fw, fy], "uv_size": [-fw, fh]}
        else:
            hasil[arah] = {"uv": [fx, fy], "uv_size": [fw, fh]}
        if arah == "down":  # Bedrock membalik sisi bawah secara vertikal
            u0, v0 = hasil[arah]["uv"]
            sw, sh = hasil[arah]["uv_size"]
            hasil[arah] = {"uv": [u0, v0 + sh], "uv_size": [sw, -sh]}
    return hasil


# ===========================================================================
# Perender 3D perangkat lunak (untuk pratinjau & ulasan)
# ===========================================================================
def _rot_bedrock(rot):
    """Matriks rotasi di ruang Bedrock (mengikuti konversi Blockbench:
    x dicerminkan, rx & ry dinegasikan, urutan ZYX)."""
    rx, ry, rz = [math.radians(a) for a in rot]
    rx, ry = -rx, -ry
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    F = np.diag([-1.0, 1.0, 1.0])
    return F @ (Rz @ Ry @ Rx) @ F


def _muka_kubus(k):
    """Daftar (nama_sisi, TL, vektor_u, vektor_v, normal) dalam ruang Bedrock."""
    inf = k["inflate"]
    (x0, y0, z0) = [k["origin"][i] - inf for i in range(3)]
    (x1, y1, z1) = [k["origin"][i] + k["size"][i] + inf for i in range(3)]
    P = np.array
    if k["datar"]:
        z = k["origin"][2]
        return [("depan", P([x0, y1, z]), P([x1 - x0, 0, 0]), P([0, -(y1 - y0), 0]), P([0, 0, -1]))]
    return [
        ("depan", P([x0, y1, z0]), P([x1 - x0, 0, 0]), P([0, y0 - y1, 0]), P([0, 0, -1])),
        ("belakang", P([x1, y1, z1]), P([x0 - x1, 0, 0]), P([0, y0 - y1, 0]), P([0, 0, 1])),
        ("kanan", P([x0, y1, z1]), P([0, 0, z0 - z1]), P([0, y0 - y1, 0]), P([-1, 0, 0])),
        ("kiri", P([x1, y1, z0]), P([0, 0, z1 - z0]), P([0, y0 - y1, 0]), P([1, 0, 0])),
        ("atas", P([x0, y1, z1]), P([x1 - x0, 0, 0]), P([0, 0, z0 - z1]), P([0, 1, 0])),
        ("bawah", P([x0, y0, z0]), P([x1 - x0, 0, 0]), P([0, 0, z1 - z0]), P([0, -1, 0])),
    ]


def render(m, tex, yaw=0.0, pitch=0.0, S=8, lebar=44, tinggi=46, atas=40, sembunyikan=("kelopak", "ekspresi_senang"),
           latar=None, skala=True):
    """Render model (pose diam) dengan proyeksi ortografis.

    yaw: derajat; 0 = tampak depan, 90 = tampak samping (sisi kanan karakter),
    180 = belakang. S = piksel per unit. Mengembalikan gambar RGBA."""
    W, H = lebar * S, tinggi * S
    warna = np.zeros((H, W, 4), dtype=np.uint8)
    if latar:
        warna[:, :] = rgb(latar)
    zbuf = np.full((H, W), np.inf)
    texa = np.asarray(tex.convert("RGBA"))
    th, tw = texa.shape[:2]
    a = math.radians(yaw)
    p_ = math.radians(pitch)
    # kamera: putar dunia terhadap sumbu y (yaw) lalu x (pitch)
    Ry = np.array([[math.cos(a), 0, -math.sin(a)], [0, 1, 0], [math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p_), -math.sin(p_)], [0, math.sin(p_), math.cos(p_)]])
    V = Rx @ Ry
    cahaya = np.array([0.35, 0.8, -0.5])
    cahaya = cahaya / np.linalg.norm(cahaya)
    sk = m.skala if skala else 1.0
    for k in m.daftar:
        if k["bone"] in sembunyikan:
            continue
        u0, v0 = k["uv"]
        w, h, d = ukuran_uv(k["size"])
        reg = {"depan": (u0, v0, w, h)} if k["datar"] else kotak_uv(u0, v0, w, h, d)
        R = _rot_bedrock(k["rot"]) if k["rot"] else np.eye(3)
        piv = np.array(k["pivot"]) if k["rot"] else np.zeros(3)
        for nama, TL, du, dv, n in _muka_kubus(k):
            sisi_tex = nama
            if k["mirror"] and nama in ("kanan", "kiri"):
                sisi_tex = "kiri" if nama == "kanan" else "kanan"
            fx, fy, fw, fh = reg[sisi_tex]
            pts = [TL, TL + du, TL + du + dv, TL + dv]
            pts = [(R @ (p - piv)) + piv for p in pts]
            nn = R @ n
            pts = [V @ (p * sk) for p in pts]
            nv = V @ nn
            terang = 0.74 + 0.26 * max(0.0, float(nn @ cahaya)) if not k["datar"] else 0.88
            if not k["datar"] and nv[2] > 0.02:  # menghadap menjauh (culling)
                continue
            # layar: x ke kanan = +x Bedrock (tampak depan), y ke bawah
            scr = [((p[0] + lebar / 2) * S, (atas - p[1]) * S, p[2]) for p in pts]
            # uv tiap sudut (dalam piksel tekstur)
            uu = [0.0, 1.0, 1.0, 0.0]
            vv = [0.0, 0.0, 1.0, 1.0]
            if k["mirror"]:
                uu = [1 - x for x in uu]
            for tri in ((0, 1, 2), (0, 2, 3)):
                _gambar_segitiga(warna, zbuf, texa, [scr[i] for i in tri], [uu[i] for i in tri], [vv[i] for i in tri],
                                 (fx * K, fy * K, fw * K, fh * K), terang)
    return Image.fromarray(warna, "RGBA")


def _gambar_segitiga(warna, zbuf, texa, p, uu, vv, reg, terang):
    H, W = zbuf.shape
    xs = [q[0] for q in p]
    ys = [q[1] for q in p]
    x0, x1 = max(0, int(math.floor(min(xs)))), min(W - 1, int(math.ceil(max(xs))))
    y0, y1 = max(0, int(math.floor(min(ys)))), min(H - 1, int(math.ceil(max(ys))))
    if x0 > x1 or y0 > y1:
        return
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = p
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-9:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    l1 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
    l2 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
    l3 = 1 - l1 - l2
    eps = -1e-4
    dalam = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
    if not dalam.any():
        return
    z = l1 * az + l2 * bz + l3 * cz
    u = l1 * uu[0] + l2 * uu[1] + l3 * uu[2]
    v = l1 * vv[0] + l2 * vv[1] + l3 * vv[2]
    fx, fy, fw, fh = reg
    tx = np.clip((fx + np.clip(u, 0, 0.9999) * fw).astype(int), 0, texa.shape[1] - 1)
    ty = np.clip((fy + np.clip(v, 0, 0.9999) * fh).astype(int), 0, texa.shape[0] - 1)
    c = texa[ty, tx]
    zb = zbuf[y0:y1 + 1, x0:x1 + 1]
    tulis = dalam & (c[..., 3] > 0) & (z < zb - 1e-6)
    if not tulis.any():
        return
    zb[tulis] = z[tulis]
    blok = warna[y0:y1 + 1, x0:x1 + 1]
    rgb_ = (c[..., :3].astype(float) * terang).clip(0, 255).astype(np.uint8)
    blok[tulis, :3] = rgb_[tulis]
    blok[tulis, 3] = 255


def lembar_render(m, tex, S=8, latar="#f4eef0"):
    """Lembar ulasan: depan, 3/4 depan, samping, belakang, 3/4 belakang + close-up wajah."""
    sudut = [(0, "depan"), (35, "3/4 kanan"), (90, "samping"), (180, "belakang"), (-145, "3/4 belakang kiri")]
    gambar = [render(m, tex, yaw=y, S=S, latar=latar) for y, _n in sudut]
    wajah = render(m, tex, yaw=15, S=S * 3, lebar=14, tinggi=14, atas=34.5, latar=latar, skala=False)
    gw = gambar[0].width
    out = Image.new("RGBA", (gw * len(gambar) + wajah.width + 10, max(gambar[0].height, wajah.height) + 24), rgb(latar))
    dr = ImageDraw.Draw(out)
    for i, (g, (_y, n)) in enumerate(zip(gambar, sudut)):
        out.alpha_composite(g, (i * gw, 24))
        dr.text((i * gw + 6, 6), n, fill=(40, 30, 40, 255))
    out.alpha_composite(wajah, (gw * len(gambar) + 10, 24))
    dr.text((gw * len(gambar) + 16, 6), "wajah (close-up, tanpa skala)", fill=(40, 30, 40, 255))
    dr.text((6, out.height - 14), f"{m.nama} - {len(m.daftar)} kubus", fill=(40, 30, 40, 255))
    return out


# ===========================================================================
# Pemeriksaan teknis
# ===========================================================================
def periksa(m, geo, tex):
    """Daftar masalah teknis (string). Kosong = aman."""
    masalah = []
    tw, th = geo["minecraft:geometry"][0]["description"]["texture_width"], geo["minecraft:geometry"][0]["description"]["texture_height"]
    if tex.width != tw * K or tex.height != th * K:
        masalah.append("ukuran tekstur tidak cocok dengan geometri")
    for k in m.daftar:
        for v in k["origin"] + k["size"]:
            if not math.isfinite(v):
                masalah.append(f"nilai tidak valid pada kubus {k['bone']}")
        if any(s < 0 for s in k["size"]):
            masalah.append(f"ukuran negatif pada kubus {k['bone']} {k['origin']}")
        top = k["origin"][1] + k["size"][1]
        if top > 44 or k["origin"][1] < -2:
            masalah.append(f"kubus di luar jangkauan tinggi wajar: {k['bone']} {k['origin']} {k['size']}")
    nama = set(NAMA_TULANG)
    for b in geo["minecraft:geometry"][0]["bones"]:
        if b.get("parent") and b["parent"] not in nama:
            masalah.append(f"induk tulang tidak ada: {b['name']} -> {b['parent']}")
    for wajib in ("head", "body", "rightArm", "leftArm", "rightLeg", "leftLeg"):
        if not any(k["bone"] in (wajib, PASANGAN.get(wajib, wajib)) for k in m.daftar):
            masalah.append(f"tidak ada kubus pada tulang {wajib}")
    if not any(k["bone"] == "mata" for k in m.daftar):
        masalah.append("tidak ada mata (pakai pasang_mata)")
    return masalah
