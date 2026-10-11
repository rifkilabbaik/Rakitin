"""Rintaro Tsumugi (Seragam Chidori) - model detail ala Yes Steve Model.

Tokoh utama pria: 190 cm, atletis, bahu lebar, tampak seram tapi baik hati.
  * Rambut pirang dicat, pendek JABRIK disisir ke atas: mahkota membulat
    (lapisan + bevel), deretan duri rambut berlapis (depan naik, tengah, belakang,
    tengkuk), duri samping ke belakang (rambut_kanan/kiri), poni pendek runcing,
    cambang, akar rambut agak gelap.
  * Mata cokelat tajam, alis tegas, mulut datar, telinga 3D dengan tiga anting
    perak (kanan 2: anting bulat di cuping + tindik di heliks, kiri 1).
  * Gakuran hitam Chidori dipakai TERBUKA: kerah tegak dengan lapisan putih,
    panel depan terbuka (kancing emas di sisi kiri, lubang kancing di kanan),
    saku, manset berkancing emas; kemeja putih berkerah dengan kancing; sabuk;
    celana panjang hitam dengan garis setrika; sepatu kulit cokelat tua.
"""
import math
import random

from inti import (Model, KOSONG, campur, isi_rect, kuas_kain, kuas_kulit, kuas_lapis, kuas_per_sisi, kuas_poni,
                  kuas_rambut, kuas_tepi, kuas_wajah, pasang_mata, rgb, titik, ubah)

# ---------------------------------------------------------------------------
# Palet
# ---------------------------------------------------------------------------
KULIT = "#f3d3bd"
RAMBUT = ("#ecc75e", "#c2952f", "#fff1b0")
RAMBUT_GARIS = "#9c7424"
AKAR = "#7a5a2c"
ALIS = "#8a6428"
IRIS = "#7a4a2a"
JAS = "#1f2029"
JAS_G = "#121219"
JAS_T = "#383a4a"
PUTIH = "#f4f4f2"
PUTIH_G = "#c9ccd4"
EMAS = "#d9b45a"
PERAK = "#d4d8e0"
CELANA = "#1c1d25"
SEPATU = "#3a261d"
SOL = "#16120f"
SABUK = "#2a2420"


# ===========================================================================
# Kuas khusus (f(img, X, Y, W, H, rnd), piksel)
# ===========================================================================
def kuas_helai(r=RAMBUT, runcing=0.6, kilau=0.3, miring=0.0, gelap_ujung=0.12, akar=0.0, tepi=RAMBUT_GARIS):
    """Satu helai/duri rambut: bayangan silinder, guratan, pita kilau bergerigi,
    akar gelap opsional (baris atas = pangkal), ujung meruncing (transparan) dan
    outline tipis. miring: -1..1 menggeser ujung ke kiri/kanan tekstur."""
    c, g, t = rgb(r[0]), rgb(r[1]), rgb(r[2])
    ct, ca = rgb(tepi), rgb(AKAR)

    def f(img, X, Y, W, H, rnd):
        if W <= 0 or H <= 0:
            return
        kolom = []
        for x in range(W):
            u = (x + 0.5) / W
            s = 0.82 + 0.22 * math.sin(math.pi * u)
            if W >= 5 and rnd.random() < 0.25:
                s *= 0.9
            kolom.append(s)
        yk = kilau * H if kilau is not None else -99
        tebal_k = max(1, H // 20)
        geser = [0] * W
        for x in range(1, W):
            geser[x] = max(-2, min(2, geser[x - 1] + rnd.choice((-1, 0, 0, 1))))
        y0_r = (1 - runcing) * H if runcing > 0 else H + 1
        tampak = [[False] * W for _ in range(H)]
        for y in range(H):
            v = y / max(1, H - 1)
            gd = 1 - gelap_ujung * v
            if y >= y0_r:
                fr = 1 - (y - y0_r) / max(1e-6, H - y0_r)
                lebar = 0.5 * fr + 0.5 / W
                pusat = 0.5 + miring * (1 - fr) * 0.45
            else:
                lebar, pusat = 1.0, 0.5
            for x in range(W):
                u = (x + 0.5) / W
                if abs(u - pusat) > lebar:
                    img.putpixel((X + x, Y + y), KOSONG)
                    continue
                tampak[y][x] = True
                w = campur(g, ubah(c, 1.04), min(1.0, max(0.0, kolom[x] - 0.66) / 0.3))
                w = ubah(w, gd * (1 + rnd.uniform(-0.02, 0.02)))
                if akar > 0 and v < akar:
                    w = campur(w, ca, 0.6 * (1 - v / akar))
                if abs(y - (yk + geser[x])) <= tebal_k * 0.5 + 0.2 and 0.15 < u < 0.85:
                    w = campur(w, t, 0.75)
                elif abs(y - (yk + geser[x] + tebal_k + 1)) < 0.6 and 0.15 < u < 0.85:
                    w = campur(w, t, 0.35)
                img.putpixel((X + x, Y + y), w)
        if tepi and W >= 3:
            for y in range(H):
                for x in range(W):
                    if not tampak[y][x]:
                        continue
                    if x == 0 or x == W - 1 or not tampak[y][x - 1] or not tampak[y][x + 1] or \
                            (y + 1 < H and not tampak[y + 1][x]):
                        img.putpixel((X + x, Y + y), campur(img.getpixel((X + x, Y + y)), ct, 0.4))
    return f


def duri(runcing=0.65, kilau=0.3, miring=0.0, akar=0.0, gelap_ujung=0.1):
    """Kuas per sisi untuk duri rambut: empat sisi meruncing, pangkal rambut, ujung kosong."""
    h = kuas_helai(runcing=runcing, kilau=kilau, miring=miring, akar=akar, gelap_ujung=gelap_ujung)
    h2 = kuas_helai(runcing=runcing, kilau=None if kilau is None else kilau + 0.08, miring=-miring, akar=akar,
                    gelap_ujung=gelap_ujung + 0.08)
    ujung = (lambda img, X, Y, W, H, rnd: isi_rect(img, X, Y, W, H, KOSONG)) if runcing > 0 else kuas_rambut(RAMBUT, kilau=-1)
    return kuas_per_sisi(depan=h, belakang=h2, kanan=h2, kiri=h, atas=kuas_rambut(RAMBUT, kilau=-1), bawah=ujung)


def kuas_rambut_kepala(akar=True):
    dasar = kuas_rambut(RAMBUT, kilau=0.3, gradasi=0.1, lebar_helai=3)
    ca = rgb(AKAR)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        if akar:  # bayangan akar di bagian atas
            for y in range(min(H, 5)):
                for x in range(W):
                    p = img.getpixel((X + x, Y + y))
                    img.putpixel((X + x, Y + y), campur(p, ca, 0.35 * (1 - y / 5)))
    return f


def kuas_akar():
    """Permukaan atas kepala: akar gelap tersamar."""
    dasar = kuas_rambut(RAMBUT, kilau=-1, gradasi=0.0)
    ca = rgb(AKAR)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        for y in range(H):
            for x in range(W):
                if rnd.random() < 0.55:
                    p = img.getpixel((X + x, Y + y))
                    img.putpixel((X + x, Y + y), campur(p, ca, 0.45))
    return f


def kuas_sisi_kepala(sisi):
    """Sisi kepala: rambut di atas & belakang telinga, kulit pelipis/pipi/telinga,
    cambang tipis di depan telinga."""
    rambut = kuas_rambut(RAMBUT, kilau=0.2, gradasi=0.12)
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        rambut(img, X, Y, W, H, rnd)
        for y in range(H):
            yy = 32.5 - (y + 0.5) / 4  # y model
            for x in range(W):
                dari_depan = (W - 1 - x) if sisi == "kanan" else x  # piksel dari muka depan
                zd = (dari_depan + 0.5) / 4  # unit dari depan
                batas_atas = 28.7 - 0.5 * min(1.0, max(0.0, zd - 1.8))
                if zd > 5.7 + 0.15 * (28.0 - yy):
                    continue  # rambut belakang telinga
                if yy > batas_atas:
                    continue
                if 1.45 < zd < 2.25 and yy > 25.6:  # cambang
                    continue
                w = ubah(kc, 0.97 - 0.07 * (28.6 - yy) / 5 - (0.05 if zd < 0.5 else 0))
                img.putpixel((X + x, Y + y), w)
        # garis rahang
        for x in range(W):
            dari_depan = (W - 1 - x) if sisi == "kanan" else x
            if dari_depan < 22:
                titik(img, X + x, Y + H - 1, ubah(kc, 0.84))
    return f


def kuas_muka():
    """Muka depan: kuas_wajah + bayangan di bawah garis rambut, rahang tegas,
    hidung lebih jelas, kerut tipis di antara alis (kesan seram)."""
    dasar = kuas_wajah(KULIT, RAMBUT[1], "datar", pipi=False, hidung=True)
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        y0 = int(H * 0.12) + 2
        for i, a in enumerate((0.45, 0.25, 0.1)):
            for x in range(W):
                p = img.getpixel((X + x, Y + y0 + i))
                if abs(p[0] - kc[0]) < 24 and abs(p[2] - kc[2]) < 24:
                    img.putpixel((X + x, Y + y0 + i), campur(p, ubah(kc, 0.82), a))
        # rahang (sisi kiri & kanan bawah)
        for y in range(int(H * 0.55), H):
            k = (y - H * 0.55) / (H * 0.45)
            for i in range(2):
                for xx in (X + i, X + W - 1 - i):
                    img.putpixel((xx, Y + y), campur(img.getpixel((xx, Y + y)), ubah(kc, 0.82), (0.25 + 0.35 * k) * (1 - 0.4 * i)))
        cx = X + W // 2
        # batang hidung + bayangan
        for y in range(int(H * 0.56), int(H * 0.68)):
            titik(img, cx, Y + y, campur(kc, ubah(kc, 0.85), 0.5))
        titik(img, cx - 1, Y + int(H * 0.69), ubah(kc, 0.8))
        titik(img, cx, Y + int(H * 0.69), ubah(kc, 0.86))
        # kerut di antara alis
        titik(img, cx - 1, Y + int(H * 0.36), ubah(kc, 0.9))
        titik(img, cx, Y + int(H * 0.35), ubah(kc, 0.9))
        # mulut datar agak menurun di ujung (kesan seram)
        my = Y + int(H * 0.78)
        isi_rect(img, cx - 3, my - 1, 7, 3, campur(img.getpixel((cx - 3, my - 2)), kc, 1.0))
        isi_rect(img, cx - 2, my + 1, 5, 1, rgb("#8a5149"))
        titik(img, cx - 3, my + 1, campur(kc, rgb("#8a5149"), 0.5))
        titik(img, cx + 3, my + 1, campur(kc, rgb("#8a5149"), 0.5))
        # bayangan bibir bawah & dagu
        isi_rect(img, cx - 1, my + 3, 2, 1, ubah(kc, 0.9))
        isi_rect(img, X + 4, Y + H - 2, W - 8, 1, ubah(kc, 0.9))
    return f


def kuas_bawah_kepala():
    kul = kuas_kulit(KULIT, 0.1)
    rmb = kuas_rambut(RAMBUT, kilau=-1)

    def f(img, X, Y, W, H, rnd):
        rmb(img, X, Y, W, H, rnd)
        kul(img, X, Y, W, int(H * 0.62), rnd)
    return f


def kuas_kulit2(gradasi=0.12, tepi=None):
    ks = [kuas_kulit(KULIT, gradasi)]
    if tepi:
        ks.append(kuas_tepi(ubah(rgb(KULIT), 0.85), 1, tepi))
    return kuas_lapis(*ks)


def kuas_telinga():
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        kuas_kulit(KULIT, 0.1)(img, X, Y, W, H, rnd)
        isi_rect(img, X + W // 4, Y + H // 5, max(1, W // 2), max(1, H * 3 // 5), ubah(kc, 0.86))
        isi_rect(img, X + W // 3, Y + H // 3, max(1, W // 4), max(1, H // 4), ubah(kc, 0.78))
        kuas_tepi(ubah(kc, 0.9), 1)(img, X, Y, W, H, rnd)
    return f


def kuas_jas(warna=JAS, gelap=JAS_G, lipatan=0.09, gradasi=0.18, tepi="lrtb", jahit=None):
    """Wol hitam gakuran: lipatan lembut, gradasi, sorot tepi & jahitan opsional."""
    c, g = rgb(warna), rgb(gelap)
    kt = campur(c, rgb(JAS_T), 0.75)

    def f(img, X, Y, W, H, rnd):
        fase = rnd.uniform(0, 6.28)
        for x in range(W):
            lip = 1 + lipatan * math.sin(x * 0.7 + fase) * (0.6 + 0.4 * math.sin(x * 0.23 + fase))
            for y in range(H):
                v = y / max(1, H - 1)
                w = campur(ubah(c, 1.12), g, gradasi * 2.2 * v)
                img.putpixel((X + x, Y + y), ubah(w, lip * (1 + rnd.uniform(-0.03, 0.03))))
        if tepi:
            kuas_tepi(kt, 1, tepi)(img, X, Y, W, H, rnd)
        if jahit and H > 4 and W > 4:
            for x in range(1, W - 1, 2):
                if "t" in jahit:
                    titik(img, X + x, Y + 2, kt)
                if "b" in jahit:
                    titik(img, X + x, Y + H - 3, kt)
            for y in range(1, H - 1, 2):
                if "l" in jahit:
                    titik(img, X + 2, Y + y, kt)
                if "r" in jahit:
                    titik(img, X + W - 3, Y + y, kt)
    return f


def kuas_panel_depan(sisi):
    """Panel depan gakuran terbuka. sisi 'kanan' (x negatif): lubang kancing di
    tepi dalam; 'kiri': tanpa (kancing 3D). Tepi dalam disorot (kain terlipat)."""
    dasar = kuas_jas(lipatan=0.07, gradasi=0.16, tepi="tb")
    c = rgb(JAS)
    kt = rgb(JAS_T)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        dalam = X + W - 1 if sisi == "kanan" else X
        luar = X if sisi == "kanan" else X + W - 1
        isi_rect(img, dalam, Y, 1, H, campur(kt, rgb("#5a5c70"), 0.4))
        isi_rect(img, dalam + (-1 if sisi == "kanan" else 1), Y, 1, H, ubah(c, 0.75))
        isi_rect(img, luar, Y, 1, H, ubah(c, 0.7))
        # jahitan tepi dalam
        jx = dalam + (-3 if sisi == "kanan" else 3)
        for y in range(1, H - 1, 2):
            titik(img, jx, Y + y, campur(c, kt, 0.7))
        if sisi == "kanan":
            for i in range(5):
                yy = Y + int(H * (0.08 + i * 0.19))
                isi_rect(img, dalam - 5, yy, 3, 1, ubah(c, 0.45))
                isi_rect(img, dalam - 5, yy + 1, 3, 1, campur(c, kt, 0.4))
    return f


def kuas_kemeja(depan=False, buka=True):
    """Kemeja putih: bayangan lipatan abu kebiruan, plaket & kancing kecil di tengah,
    kerah terbuka (V kulit) di atas."""
    c, g = rgb(PUTIH), rgb(PUTIH_G)
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        fase = rnd.uniform(0, 6.28)
        for x in range(W):
            lip = 0.5 + 0.5 * math.sin(x * 0.9 + fase)
            for y in range(H):
                v = y / max(1, H - 1)
                w = campur(c, g, 0.12 + 0.25 * lip ** 3 + 0.18 * v)
                img.putpixel((X + x, Y + y), ubah(w, 1 + rnd.uniform(-0.01, 0.01)))
        if depan:
            cx = X + W // 2
            isi_rect(img, cx - 2, Y, 1, H, campur(c, g, 0.65))
            isi_rect(img, cx + 1, Y, 1, H, campur(c, g, 0.45))
            for i in range(5):
                yy = Y + int(H * (0.22 + 0.16 * i))
                isi_rect(img, cx - 1, yy, 2, 2, rgb("#e2e2e6"))
                titik(img, cx - 1, yy, rgb("#9fa3ad"))
                titik(img, cx, yy + 1, rgb("#b8bcc6"))
            if buka:  # leher terbuka (kancing atas dilepas)
                for y in range(int(H * 0.13)):
                    lb = int(W * 0.08 + y * 0.6)
                    isi_rect(img, cx - lb, Y + y, 2 * lb, 1, ubah(kc, 0.92 - 0.04 * (y / max(1, H * 0.13))))
                isi_rect(img, cx - 1, Y + int(H * 0.13), 2, 1, ubah(kc, 0.8))
        kuas_tepi(campur(c, g, 0.7), 1, "lr")(img, X, Y, W, H, rnd)
    return f


def kuas_kerah_putih(tepi="lrb"):
    c, g = rgb(PUTIH), rgb(PUTIH_G)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                img.putpixel((X + x, Y + y), ubah(campur(c, g, 0.1 + 0.25 * y / max(1, H - 1)), 1 + rnd.uniform(-0.01, 0.01)))
        kuas_tepi(campur(c, g, 0.85), 1, tepi)(img, X, Y, W, H, rnd)
    return f


def kuas_kerah_jas():
    """Kerah tegak gakuran: hitam dengan lapisan kerah putih di tepi atas."""
    dasar = kuas_jas(lipatan=0.03, gradasi=0.15, tepi="lrb")

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        isi_rect(img, X, Y, W, 1, rgb("#eeeef0"))
        isi_rect(img, X, Y + 1, W, 1, rgb("#a8acb6"))
    return f


def kuas_logam(warna, kilau="#ffffff", gelap=0.55):
    """Logam kecil (kancing emas / anting perak): kilap pojok kiri atas, bayangan."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                t = ((x + 0.5) / W + (y + 0.5) / H) / 2
                img.putpixel((X + x, Y + y), ubah(c, 1.25 - 0.55 * t))
        kuas_tepi(ubah(c, gelap), 1)(img, X, Y, W, H, rnd)
        if W >= 3 and H >= 3:
            titik(img, X + 1, Y + 1, rgb(kilau))
    return f


def kuas_cincin(warna=PERAK):
    """Anting bulat: cincin dengan lubang transparan."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, KOSONG)
        cx, cy = (W - 1) / 2, (H - 1) / 2
        for y in range(H):
            for x in range(W):
                d = max(abs(x - cx) / max(0.5, cx), abs(y - cy) / max(0.5, cy))
                if d > 0.55 or (W <= 2 or H <= 2):
                    img.putpixel((X + x, Y + y), ubah(c, 1.1 - 0.4 * (y / max(1, H - 1))))
        if W >= 3:
            titik(img, X, Y + H // 2, rgb("#ffffff"))
    return f


def kuas_celana(gradasi=0.18, garis=True, tepi_bawah=False):
    """Celana wol hitam: garis setrika di tengah, bayangan pinggir, gradasi."""
    c = rgb(CELANA)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            u = (x + 0.5) / W
            s = 0.85 + 0.3 * math.sin(math.pi * u) ** 2
            for y in range(H):
                v = y / max(1, H - 1)
                img.putpixel((X + x, Y + y), ubah(c, s * (1.1 - gradasi * v) * (1 + rnd.uniform(-0.03, 0.03))))
        if garis and W >= 6:
            isi_rect(img, X + W // 2, Y, 1, H, campur(c, rgb(JAS_T), 0.85))
            isi_rect(img, X + W // 2 + 1, Y, 1, H, ubah(c, 0.75))
        kuas_tepi(ubah(c, 0.7), 1, "lr")(img, X, Y, W, H, rnd)
        if tepi_bawah:
            isi_rect(img, X, Y + H - 1, W, 1, ubah(c, 0.6))
            isi_rect(img, X, Y + H - 3, W, 1, campur(c, rgb(JAS_T), 0.5))
    return f


def kuas_lutut():
    """Celana di lutut: kerut horizontal."""
    dasar = kuas_celana(0.1)
    c = rgb(CELANA)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        for i, yy in enumerate((0.15, 0.3, 0.48)):
            y = Y + int(H * yy)
            x0 = X + 2 + (i % 2) * 2
            isi_rect(img, x0, y, max(1, W - 6), 1, ubah(c, 0.62))
            isi_rect(img, x0 + 1, y + 1, max(1, W - 8), 1, campur(c, rgb(JAS_T), 0.6))
    return f


def kuas_sepatu(warna=SEPATU, jahit=True, kilap=True):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                v = y / max(1, H - 1)
                img.putpixel((X + x, Y + y), ubah(c, (1.18 - 0.3 * v) * (1 + rnd.uniform(-0.02, 0.02))))
        if jahit and H >= 4:
            for x in range(1, W - 1, 2):
                titik(img, X + x, Y + H - 2, ubah(c, 1.5))
        if kilap and W >= 4 and H >= 3:
            isi_rect(img, X + W // 4, Y + 1, max(1, W // 5), 1, ubah(c, 1.9))
        kuas_tepi(ubah(c, 0.6), 1)(img, X, Y, W, H, rnd)
    return f


def kuas_tangan(jari=False, buku=False):
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        kuas_kulit(KULIT, 0.1)(img, X, Y, W, H, rnd)
        if jari and W >= 4:
            for x in range(W // 4, W, max(1, W // 4)):
                isi_rect(img, X + x, Y + H // 4, 1, H - H // 4, ubah(kc, 0.84))
        if buku:
            for x in range(1, W - 1, 3):
                titik(img, X + x, Y + H - 2, ubah(kc, 0.88))
        isi_rect(img, X, Y + H - 1, W, 1, ubah(kc, 0.86))
    return f


def kuas_sabuk():
    c = rgb(SABUK)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                img.putpixel((X + x, Y + y), ubah(c, (1.15 - 0.3 * y / max(1, H - 1)) * (1 + rnd.uniform(-0.03, 0.03))))
        kuas_tepi(ubah(c, 0.6), 1, "tb")(img, X, Y, W, H, rnd)
        for x in range(1, W - 1, 2):
            titik(img, X + x, Y + 1, ubah(c, 1.5))
    return f


def kuas_rok_jas(depan=False):
    """Bagian pinggul gakuran (di bawah pinggang). Muka depan: celana terlihat di
    tengah (jas terbuka) dengan resleting."""
    jas = kuas_jas(lipatan=0.1, gradasi=0.15, tepi="b")
    cel = kuas_celana(0.1, garis=False)

    def f(img, X, Y, W, H, rnd):
        jas(img, X, Y, W, H, rnd)
        if depan:
            x0, x1 = int(W * 0.3), int(W * 0.7)
            cel(img, X + x0, Y, x1 - x0, H, rnd)
            cx = X + W // 2
            isi_rect(img, cx, Y, 1, H, ubah(rgb(CELANA), 0.6))
            for y in range(0, H, 2):
                titik(img, cx + 2, Y + y, campur(rgb(CELANA), rgb(JAS_T), 0.6))
    return f


def kuas_jas_belakang():
    """Punggung gakuran: jahitan tengah, belahan (vent) bawah, garis pinggang."""
    dasar = kuas_jas(lipatan=0.08, gradasi=0.2, tepi="lr")
    c = rgb(JAS)
    kt = rgb(JAS_T)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        cx = X + W // 2
        isi_rect(img, cx, Y, 1, H, ubah(c, 0.6))
        isi_rect(img, cx + 1, Y, 1, H, campur(c, kt, 0.35))
        # tulang belikat
        for sx in (-1, 1):
            for i in range(6):
                titik(img, cx + sx * (6 + i), Y + int(H * 0.3) + i // 2, campur(c, kt, 0.45))
    return f


# ===========================================================================
# Helper geometri
# ===========================================================================
def _arah(A, B):
    """Panjang & rotasi [rx, ry, rz] agar sumbu -y kubus mengarah dari A ke B."""
    d = [B[i] - A[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    dx, dy, dz = [v / L for v in d]
    if abs(dz) > 0.6 and abs(dz) > abs(dx) and dy <= 0:
        rx = math.degrees(math.atan2(math.sqrt(dx * dx + dz * dz), -dy))
        ry = math.degrees(math.atan2(dx, dz))
        if dz < 0:
            rx = -rx
            ry = math.degrees(math.atan2(-dx, -dz))
        return L, [rx, ry, 0.0]
    cr = math.sqrt(dx * dx + dy * dy)
    rx = math.degrees(math.atan2(dz, cr))
    rz = math.degrees(math.atan2(-dx, -dy)) if cr > 1e-9 else 0.0
    return L, [rx, 0.0, rz]


def untai(m, bone, A, B, w, t, kuas, hadap="depan", cermin=False, inflate=0.0):
    """Kubus memanjang dari titik A (pangkal = pivot) ke titik B (ujung)."""
    L, rot = _arah(A, B)
    if hadap == "depan":
        origin, size = [A[0] - w / 2, A[1] - L, A[2] - t / 2], [w, L, t]
    else:
        origin, size = [A[0] - t / 2, A[1] - L, A[2] - w / 2], [t, L, w]
    rot = [round(v, 3) for v in rot]
    if all(abs(v) < 1e-3 for v in rot):
        rot = None
    f = m.cermin if cermin else m.kubus
    return f(bone, origin, size, kuas, inflate=inflate, rot=rot, pivot=list(A) if rot else None)


# ===========================================================================
# Kepala & rambut
# ===========================================================================
def kepala(m):
    rmb = kuas_rambut_kepala()
    m.kubus("head", [-4.5, 23.5, -4.5], [9, 9, 9], kuas_per_sisi(
        depan=kuas_muka(), kanan=kuas_sisi_kepala("kanan"), kiri=kuas_sisi_kepala("kiri"),
        atas=kuas_akar(), bawah=kuas_bawah_kepala(), lain=rmb))
    pasang_mata(m, KULIT, IRIS, ALIS, gaya="tajam", lebar=2.25, tinggi=2.0, jarak=0.8, y_bawah=25.55)
    # telinga 3D
    tel = kuas_per_sisi(kanan=kuas_telinga(), lain=kuas_kulit2(0.1))
    m.cermin("head", [-4.9, 25.5, -0.45], [0.45, 2.0, 1.25], tel)
    m.cermin("head", [-4.8, 25.25, -0.3], [0.4, 0.4, 0.8], kuas_kulit2(0.1))  # cuping
    # anting: kanan 2 (cincin di cuping + tindik heliks), kiri 1 (cincin)
    cin = kuas_per_sisi(kanan=kuas_cincin(), kiri=kuas_cincin(), lain=kuas_logam(PERAK, gelap=0.6))
    m.kubus("head", [-5.02, 24.45, -0.4], [0.16, 0.9, 0.9], cin)
    m.kubus("head", [-5.0, 26.95, 0.38], [0.22, 0.32, 0.32], kuas_logam(PERAK, gelap=0.6))
    m.kubus("head", [4.86, 24.45, -0.4], [0.16, 0.9, 0.9], cin, mirror=False)
    # leher
    m.kubus("body", [-1.25, 22.3, -1.35], [2.5, 1.4, 2.5], kuas_per_sisi(
        depan=kuas_lapis(kuas_kulit(KULIT, 0.25), kuas_tepi(ubah(rgb(KULIT), 0.8), 1, "t")), lain=kuas_kulit(KULIT, 0.25)))
    m.kubus("body", [-0.9, 22.4, -1.5], [1.8, 0.6, 0.3], kuas_kulit2(0.2))  # jakun/leher depan


def mahkota(m):
    """Lapisan atas kepala yang membulat + bevel sudut supaya kepala tidak kotak."""
    r0 = kuas_akar()
    rs = kuas_rambut(RAMBUT, kilau=0.35, gradasi=0.08)
    m.kubus("head", [-4.3, 32.45, -4.3], [8.6, 0.6, 8.7], kuas_per_sisi(atas=r0, lain=rs))
    m.kubus("head", [-3.5, 32.95, -3.4], [7.0, 0.5, 7.2], kuas_per_sisi(atas=r0, lain=rs))
    for z in (-4.0, 4.0):  # bevel tepi atas depan & belakang
        m.kubus("head", [-4.35, 32.2 - 0.85, z - 0.85], [8.7, 1.7, 1.7], rs, rot=[45, 0, 0])
    m.cermin("head", [-4.0 - 0.85, 32.2 - 0.85, -4.35], [1.7, 1.7, 8.7], rs, rot=[0, 0, 45])
    # bevel sudut vertikal belakang & depan atas (di atas pelipis)
    m.cermin("head", [-4.25 - 0.7, 24.3, 4.25 - 0.7], [1.4, 8.0, 1.4], rs, rot=[0, 45, 0])
    m.cermin("head", [-4.3 - 0.6, 28.9, -4.3 - 0.6], [1.2, 3.4, 1.2], rs, rot=[0, 45, 0])


def poni(m):
    """Poni pendek runcing (sebagian besar disisir naik; beberapa jatuh ke dahi)."""
    m.kubus("head", [-4.6, 30.55, -4.85], [9.2, 2.3, 0.4], kuas_per_sisi(
        depan=kuas_poni(RAMBUT, ujung=(0.35, 0.95), helai_px=5), belakang=kuas_poni(RAMBUT, ujung=(0.35, 0.95), helai_px=5),
        lain=kuas_rambut(RAMBUT, kilau=-1)))
    # (x_pangkal, x_ujung, y_ujung, lebar, z_ujung, miring)
    daftar = [
        (-3.9, -4.7, 29.7, 1.6, -5.0, -0.5),
        (-2.8, -3.4, 29.0, 1.8, -5.05, -0.4),
        (-1.7, -2.1, 28.75, 1.7, -5.0, -0.3),
        (-0.5, -0.3, 27.75, 1.4, -5.1, 0.1),
        (0.6, 1.1, 28.8, 1.6, -5.0, 0.3),
        (1.8, 2.6, 29.1, 1.8, -5.05, 0.4),
        (3.0, 3.7, 29.5, 1.7, -5.0, 0.5),
        (4.0, 4.8, 30.1, 1.4, -4.95, 0.6),
        (-1.2, -0.7, 29.3, 1.3, -5.3, 0.0),  # lapisan depan
        (2.3, 2.0, 29.9, 1.3, -5.3, -0.2),
    ]
    for xa, xb, yb, w, z, mir in daftar:
        untai(m, "head", (xa, 32.6, z + 0.25), (xb, yb, z), w, 0.45, duri(runcing=0.6, kilau=0.25, miring=mir))
    # jambul depan naik (disisir ke atas)
    for xa, xb, zb in ((-2.2, -2.9, -5.4), (0.4, 0.9, -5.7), (2.8, 3.5, -5.2)):
        untai(m, "head", (xa, 31.6, -4.3), (xb, 34.3, zb), 2.2, 1.2, duri(runcing=0.7, kilau=0.35, akar=0.25))


def duri_atas(m):
    """Duri rambut di mahkota: berlapis dari depan ke belakang, mengarah naik/belakang."""
    rnd = random.Random(1907)

    def j(a=0.25):
        return rnd.uniform(-a, a)

    # baris depan: naik tajam sedikit ke belakang
    for x in (-3.5, -1.75, 0.0, 1.75, 3.5):
        untai(m, "head", (x, 32.0, -3.4), (x * 1.3 + j(), 35.6 - abs(x) * 0.3 + j(), -2.0 + j()), 2.3, 1.5,
              duri(runcing=0.7, kilau=0.3, akar=0.22, miring=j(0.5)))
    # baris tengah
    for x in (-2.7, -0.9, 0.9, 2.7):
        untai(m, "head", (x, 32.7, -0.6), (x * 1.35 + j(), 35.4 - abs(x) * 0.25 + j(), 1.9 + j()), 2.3, 1.5,
              duri(runcing=0.7, kilau=0.3, akar=0.22, miring=j(0.5)))
    # baris belakang atas: ke belakang-atas
    for x in (-3.2, -1.1, 1.1, 3.2):
        untai(m, "head", (x, 32.4, 2.4), (x * 1.3 + j(), 34.3 + j(), 6.0 + j()), 2.3, 1.4,
              duri(runcing=0.7, kilau=0.3, akar=0.2, miring=j(0.5)))
    # sela: duri kecil acak untuk kesan berantakan
    for x, z in ((-1.8, -2.2), (1.8, -2.0), (0.0, 0.8), (-3.6, 0.9), (3.6, 0.6), (0.0, 3.6)):
        untai(m, "head", (x, 32.8, z), (x * 1.5 + j(0.5), 34.6 + j(0.4), z + 2.2 + j(0.4)), 1.6, 1.1,
              duri(runcing=0.75, kilau=0.35, akar=0.25, miring=j(0.6)))
    # baris belakang: mencuat ke belakang
    for x in (-3.5, -1.2, 1.2, 3.5):
        untai(m, "head", (x, 30.8, 3.8), (x * 1.25 + j(), 29.6 + j(), 7.0 + j()), 2.3, 1.4,
              duri(runcing=0.7, kilau=0.35, miring=j(0.5)))


def rambut_belakang(m):
    """Bagian belakang/bawah: duri turun ke tengkuk (bergoyang ringan)."""
    rnd = random.Random(77)

    def j(a=0.2):
        return rnd.uniform(-a, a)

    for x in (-3.6, -1.8, 0.0, 1.8, 3.6):
        untai(m, "rambut_belakang", (x, 29.4, 4.1), (x * 1.12 + j(), 25.4 + j(), 6.0 + j()), 2.2, 1.3,
              duri(runcing=0.65, kilau=0.3, miring=j(0.5)))
    for x in (-2.7, -0.9, 0.9, 2.7):
        untai(m, "rambut_belakang", (x, 31.2, 4.2), (x * 1.15 + j(), 27.2 + j(), 6.4 + j()), 2.0, 1.2,
              duri(runcing=0.7, kilau=0.3, miring=j(0.5)))
    # tengkuk: helai pendek runcing turun
    for x in (-3.3, -1.1, 1.1, 3.3):
        untai(m, "rambut_belakang2", (x, 26.6, 4.3), (x * 1.05 + j(), 23.0 + j(0.15), 5.0), 1.8, 0.8,
              duri(runcing=0.7, kilau=None, miring=j(0.4)))


def rambut_samping(m):
    """Duri samping disisir ke belakang (rambut_kanan/rambut_kiri) + cambang."""
    daftar = [
        # (A, B, w, t, runcing)
        ((-4.0, 31.7, -3.3), (-5.9, 33.6, -2.0), 2.2, 1.4, 0.7),   # mencuat ke luar-atas
        ((-4.1, 30.9, -2.6), (-5.5, 30.4, 1.6), 2.2, 1.3, 0.65),   # disisir ke belakang
        ((-4.2, 29.9, -3.0), (-5.2, 28.6, 0.6), 1.9, 1.1, 0.65),
        ((-4.1, 31.0, 0.6), (-5.6, 30.0, 4.6), 2.3, 1.4, 0.65),
        ((-4.2, 29.7, 1.8), (-5.2, 26.6, 4.5), 1.9, 1.1, 0.7),     # di belakang telinga
        ((-4.0, 32.2, -1.0), (-5.4, 34.4, 0.6), 2.1, 1.3, 0.7),    # atas samping
    ]
    for A, B, w, t, rc in daftar:
        untai(m, "rambut_kanan", A, B, w, t, duri(runcing=rc, kilau=0.3), hadap="samping", cermin=True)
    # helai pendek menutup sisi atas kepala (di atas telinga), disisir ke belakang-bawah
    for z, yb, w in ((-2.6, 27.9, 1.5), (-1.1, 27.6, 1.6), (0.5, 27.7, 1.6), (2.0, 27.1, 1.6), (3.4, 26.4, 1.5)):
        untai(m, "head", (-4.55, 31.2, z - 0.4), (-4.82, yb, z + 0.9), w, 0.5,
              duri(runcing=0.55, kilau=0.3, miring=0.3), hadap="samping", cermin=True)
    # cambang tipis di depan telinga
    untai(m, "head", (-4.42, 29.0, -2.7), (-4.62, 25.7, -2.45), 1.0, 0.4,
          duri(runcing=0.5, kilau=None), hadap="samping", cermin=True)
    # asimetri: satu duri ekstra di kanan
    untai(m, "rambut_kanan", (-4.0, 30.4, -3.9), (-5.6, 29.0, -4.4), 1.4, 0.9, duri(runcing=0.7, kilau=0.3), hadap="samping")


# ===========================================================================
# Badan (gakuran terbuka + kemeja)
# ===========================================================================
def badan(m):
    sisi_jas = kuas_jas(tepi="tb")
    # cangkang jas: dada, pinggang, pinggul (meruncing)
    m.kubus("body", [-4.2, 18.0, -2.15], [8.4, 5.2, 4.3], kuas_per_sisi(
        belakang=kuas_jas_belakang(), lain=sisi_jas))
    m.kubus("body", [-3.9, 13.8, -2.0], [7.8, 4.3, 4.0], kuas_per_sisi(
        belakang=kuas_jas_belakang(), lain=kuas_jas(tepi="")))
    m.kubus("body", [-4.05, 11.5, -2.1], [8.1, 2.4, 4.2], kuas_per_sisi(
        depan=kuas_rok_jas(True), lain=kuas_rok_jas(False)))
    # bahu (sedikit menonjol ke atas, garis jahitan)
    m.cermin("body", [-4.3, 22.3, -1.9], [2.5, 1.05, 3.8], kuas_jas(gradasi=0.05, tepi="lr"), rot=[0, 0, -12],
             pivot=[-1.8, 22.8, 0])

    # kemeja putih (terlihat di bukaan jas)
    m.kubus("body", [-1.6, 12.4, -2.35], [3.2, 10.9, 0.3], kuas_per_sisi(depan=kuas_kemeja(True), lain=kuas_kemeja()))
    # kerah kemeja (dua ujung runcing)
    untai(m, "body", (-0.55, 23.25, -2.5), (-1.95, 22.2, -2.55), 1.15, 0.2,
          kuas_per_sisi(depan=kuas_kerah_putih("lrb"), lain=kuas_kerah_putih("")), cermin=True)
    m.kubus("body", [-1.45, 22.7, -2.2], [2.9, 0.45, 0.9], kuas_kerah_putih(""))  # pita kerah di belakang leher depan

    # panel depan jas terbuka: atas (dada) & bawah (perut)
    m.kubus("body", [-4.3, 17.95, -2.6], [2.85, 5.4, 0.5], kuas_per_sisi(depan=kuas_panel_depan("kanan"), lain=kuas_jas(tepi="")))
    m.kubus("body", [-4.1, 11.45, -2.45], [2.6, 6.65, 0.45], kuas_per_sisi(depan=kuas_panel_depan("kanan"), lain=kuas_jas(tepi="")))
    m.kubus("body", [1.45, 17.95, -2.6], [2.85, 5.4, 0.5], kuas_per_sisi(depan=kuas_panel_depan("kiri"), lain=kuas_jas(tepi="")))
    m.kubus("body", [1.5, 11.45, -2.45], [2.6, 6.65, 0.45], kuas_per_sisi(depan=kuas_panel_depan("kiri"), lain=kuas_jas(tepi="")))
    # sisi dalam (lapisan) yang terlihat di tepi bukaan

    # kancing emas (sisi kiri pemakai, x positif)
    kc = kuas_logam(EMAS, "#fff6cf")
    for y in (22.2, 20.15, 18.0, 15.9, 13.8):
        z = -2.85 if y > 18.05 else -2.7
        m.kubus("body", [1.8, y - 0.3, z], [0.6, 0.6, 0.3], kc)
    # saku dada (kiri) & saku samping (penutup 3D)
    m.kubus("body", [2.15, 20.6, -2.7], [1.7, 0.18, 0.15], kuas_jas(JAS_G, JAS_G, tepi=""))
    m.cermin("body", [-3.85, 14.6, -2.6], [2.1, 0.55, 0.2], kuas_jas(tepi="lrb", gradasi=0.05))

    # kerah tegak gakuran (mengelilingi leher, terbuka di depan)
    kj = kuas_kerah_jas()
    m.kubus("body", [-2.4, 22.6, 0.85], [4.8, 0.85, 0.45], kj)
    m.cermin("body", [-2.55, 22.55, -1.7], [0.45, 0.85, 2.7], kj)
    untai(m, "body", (-1.25, 23.45, -2.35), (-2.25, 22.35, -2.1), 1.1, 0.4, kj, hadap="samping", cermin=True)
    m.cermin("body", [-2.35, 22.4, -2.65], [0.9, 1.05, 0.65], kj, rot=[0, -25, 0])
    # lencana kerah (emas kecil di kerah kiri)
    m.kubus("body", [1.95, 22.65, -2.98], [0.35, 0.35, 0.12], kuas_logam(EMAS, "#fff6cf"))

    # sabuk & gesper (terlihat di bukaan)
    m.kubus("body", [-1.65, 12.0, -2.5], [3.3, 0.75, 0.15], kuas_sabuk())
    m.kubus("body", [-0.45, 11.95, -2.63], [0.9, 0.85, 0.15], kuas_logam(PERAK, gelap=0.5))

    # ujung bawah jas belakang (sedikit melebar)
    m.kubus("body", [-4.1, 11.4, 1.85], [8.2, 1.2, 0.4], kuas_jas(tepi="b", gradasi=0.1))


def lengan(m):
    jas = kuas_jas(lipatan=0.1, gradasi=0.12, tepi="")
    # lengan atas + kepala lengan (bahu lebar)
    m.cermin("rightArm", [-8.0, 17.0, -2.0], [4.0, 6.0, 4.0], kuas_per_sisi(
        kanan=kuas_jas(lipatan=0.1, gradasi=0.12, tepi="", jahit="t"), lain=jas))
    m.cermin("rightArm", [-8.25, 20.7, -2.2], [4.35, 2.6, 4.4], kuas_jas(gradasi=0.2, tepi="b"))
    # siku (lipatan)
    m.cermin("rightArm", [-8.08, 16.7, -2.04], [4.13, 0.7, 4.08], kuas_jas(lipatan=0.25, gradasi=0.3, tepi="tb"))
    m.cermin("rightForearm", [-7.9, 13.2, -1.9], [3.8, 4.0, 3.8], kuas_jas(lipatan=0.12, gradasi=0.12, tepi=""))
    # manset jas + kancing emas
    m.cermin("rightForearm", [-8.05, 12.5, -2.05], [4.1, 1.45, 4.1], kuas_jas(lipatan=0.03, gradasi=0.05, tepi="tb", jahit="t"))
    for z in (0.45, 1.25):
        m.cermin("rightForearm", [-8.3, 12.95, z], [0.3, 0.45, 0.45], kuas_logam(EMAS, "#fff6cf"))
    # manset kemeja
    m.cermin("rightForearm", [-7.6, 12.05, -1.6], [3.2, 0.6, 3.2], kuas_kerah_putih("tb"))
    # tangan
    m.cermin("rightForearm", [-7.5, 10.75, -1.5], [3.0, 1.55, 3.0], kuas_tangan())
    m.cermin("rightForearm", [-7.4, 10.0, -1.4], [2.75, 0.85, 2.7], kuas_per_sisi(
        depan=kuas_tangan(jari=True), belakang=kuas_tangan(jari=True), kiri=kuas_tangan(jari=True), lain=kuas_tangan(buku=True)))
    m.cermin("rightForearm", [-4.85, 10.5, -1.75], [0.75, 1.5, 0.9], kuas_tangan())  # ibu jari


def kaki(m):
    # paha (celana agak longgar)
    m.cermin("rightLeg", [-3.95, 6.0, -2.0], [3.95, 6.3, 4.0], kuas_celana())
    # lutut
    m.cermin("rightShin", [-4.03, 5.0, -2.05], [3.93, 1.4, 3.95], kuas_lutut())
    m.cermin("rightShin", [-3.9, 1.6, -1.95], [3.85, 4.5, 3.9], kuas_celana(0.12))
    # ujung celana (sedikit melebar menutupi sepatu)
    m.cermin("rightShin", [-4.0, 1.0, -2.1], [4.0, 1.25, 4.15], kuas_celana(0.05, tepi_bawah=True))
    # sepatu kulit
    m.cermin("rightShin", [-3.85, 0.0, -3.3], [3.75, 0.35, 4.3], kuas_sepatu(SOL, jahit=False, kilap=False))
    m.cermin("rightShin", [-3.75, 0.3, -2.95], [3.55, 1.3, 4.75], kuas_sepatu())
    m.cermin("rightShin", [-3.55, 0.25, -3.25], [3.15, 1.0, 0.5], kuas_sepatu(jahit=False))
    m.cermin("rightShin", [-3.3, 0.2, -3.5], [2.65, 0.75, 0.35], kuas_sepatu(jahit=False))
    m.cermin("rightShin", [-3.62, 1.4, -2.55], [3.3, 0.35, 1.3], kuas_sepatu(ubah(rgb(SEPATU), 0.8), jahit=False))  # lidah
    m.cermin("rightShin", [-3.8, 0.0, 1.0], [3.7, 0.55, 1.05], kuas_sepatu(SOL, jahit=False, kilap=False))  # hak


def buat():
    m = Model("rintaro", "Rintaro Tsumugi", "Rintaro Tsumugi (Seragam Chidori)", skala=1.06,
              deskripsi="Tokoh utama pria dari SMA Chidori: tinggi 190 cm, rambut pirang jabrik, mata tajam & tiga anting "
                        "perak - tampak seram tapi baik hati. Gakuran hitam terbuka di atas kemeja putih.")
    kepala(m)
    mahkota(m)
    poni(m)
    duri_atas(m)
    rambut_belakang(m)
    rambut_samping(m)
    badan(m)
    lengan(m)
    kaki(m)
    return [m]
