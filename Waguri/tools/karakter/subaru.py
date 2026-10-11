"""Subaru Hoshina (Seragam Kikyo) - model detail ala Yes Steve Model.

Rambut perak panjang diikat ekor kuda tinggi (ikat rambut biru tua), poni
menjuntai menutupi sebagian mata kanan, helai samping wajah. Seragam pelaut
Kikyo merah muda pudar: kerah pelaut putih bergaris gelap (V di depan, flap
persegi di punggung), pita hitam, lengan menggembung, manset putih, rok lipit di
bawah lutut, stoking hitam, loafer cokelat.
"""
import math

from inti import (Model, K, KOSONG, campur, isi_rect, kuas_kain, kuas_kulit, kuas_lapis, kuas_per_sisi, kuas_polos, kuas_rect,
                  kuas_poni, kuas_rambut, kuas_strip_h, kuas_tepi, kuas_wajah, pasang_mata, rgb, titik, ubah)

# ---------------------------------------------------------------------------
# Palet
# ---------------------------------------------------------------------------
KULIT = "#fbe3d6"
RAMBUT = ("#d9dce4", "#a9aebc", "#ffffff")
RAMBUT_GARIS = "#8b90a2"
IRIS = "#3fb8c4"
BAJU = "#c98f9b"
BAJU_G = "#9f6874"
PUTIH = "#f7f4f2"
GARIS = "#4a3a46"
PITA = "#1c1a22"
KANCING = "#3a2a34"
KAUS = "#24212b"
SEPATU = "#4b2f22"
SOL = "#2a1a14"
IKAT = "#2b4a7a"


# ===========================================================================
# Kuas khusus Subaru (tanda tangan f(img, X, Y, W, H, rnd), piksel)
# ===========================================================================
def kuas_helai(r=RAMBUT, runcing=0.45, kilau=0.22, miring=0.0, gelap_ujung=0.22, tepi=RAMBUT_GARIS, garis=True):
    """Satu helai rambut: bayangan silinder, garis helai halus, pita kilau
    bergerigi, ujung runcing (bagian bawah transparan) dan outline tipis.

    runcing: bagian bawah (relatif) yang meruncing; 0 = ujung tumpul.
    miring : -1..1 menggeser titik ujung ke kiri/kanan tekstur."""
    c, g, t = rgb(r[0]), rgb(r[1]), rgb(r[2])
    ct = rgb(tepi)

    def f(img, X, Y, W, H, rnd):
        if W <= 0 or H <= 0:
            return
        kolom = []
        for x in range(W):
            u = (x + 0.5) / W
            s = 0.84 + 0.2 * math.sin(math.pi * u)
            if garis and W >= 6 and rnd.random() < 0.22:
                s *= 0.9
            kolom.append(s)
        yk = kilau * H if kilau is not None else -99
        tebal_k = max(1, H // 22)
        geser = [0] * W
        for x in range(1, W):
            geser[x] = max(-2, min(2, geser[x - 1] + rnd.choice((-1, 0, 0, 1))))
        y0_r = (1 - runcing) * H if runcing > 0 else H + 1
        tampak = [[False] * W for _ in range(H)]
        for y in range(H):
            gd = 1 - gelap_ujung * (y / max(1, H - 1))
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
                w = campur(g, c, min(1.0, kolom[x] - 0.55) / 0.45) if kolom[x] < 1.0 else c
                w = ubah(w, gd * kolom[x] / max(0.9, kolom[x]) * (1 + rnd.uniform(-0.015, 0.015)))
                if abs(y - (yk + geser[x])) <= tebal_k * 0.5 + 0.2 and 0.12 < u < 0.88:
                    w = campur(w, t, 0.7)
                elif abs(y - (yk + geser[x] + tebal_k + 1)) < 0.6 and 0.12 < u < 0.88:
                    w = campur(w, t, 0.3)
                img.putpixel((X + x, Y + y), w)
        if tepi and W >= 3:
            for y in range(H):
                for x in range(W):
                    if not tampak[y][x]:
                        continue
                    if x == 0 or x == W - 1 or not tampak[y][x - 1] or not tampak[y][x + 1] or \
                            (y + 1 < H and not tampak[y + 1][x]):
                        img.putpixel((X + x, Y + y), campur(img.getpixel((X + x, Y + y)), ct, 0.65))
    return f


def kuas_rambut_halus(r=RAMBUT, kilau=0.25):
    """Permukaan rambut (kepala) dengan outline tipis."""
    return kuas_lapis(kuas_rambut(r, kilau=kilau, gradasi=0.12, lebar_helai=3))


def kuas_sisi_kepala(sisi):
    """Sisi kepala: rambut di atas & belakang, kulit pipi/rahang di depan bawah."""
    dasar = kuas_rambut(RAMBUT, kilau=0.2, gradasi=0.12)
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        lebar_kulit = int(W * 0.36)
        y0 = int(H * 0.5)
        for y in range(y0, H):
            for i in range(lebar_kulit):
                x = X + W - 1 - i if sisi == "kanan" else X + i
                # batas rambut miring
                if i > lebar_kulit - 3 - (y - y0) // 6:
                    continue
                img.putpixel((x, Y + y), ubah(kc, 0.97 - 0.06 * (y - y0) / max(1, H - y0)))
    return f


def kuas_muka():
    """Muka: kuas_wajah + bayangan lembut di bawah poni & di tepi rahang."""
    dasar = kuas_wajah(KULIT, RAMBUT[1], "senyum")
    kc = rgb(KULIT)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        y0 = int(H * 0.12) + 2
        for i, a in enumerate((0.55, 0.35, 0.18)):
            for x in range(W):
                yy = Y + y0 + i
                p = img.getpixel((X + x, yy))
                if abs(p[0] - kc[0]) < 20:
                    img.putpixel((X + x, yy), campur(p, ubah(kc, 0.8), a))
        for x in range(2):
            for y in range(int(H * 0.45), H):
                for xx in (X + x, X + W - 1 - x):
                    img.putpixel((xx, Y + y), campur(img.getpixel((xx, Y + y)), ubah(kc, 0.85), 0.5 - 0.2 * x))
    return f


def kuas_bawah_kepala():
    kul = kuas_kulit(KULIT)
    rmb = kuas_rambut(RAMBUT, kilau=-1)

    def f(img, X, Y, W, H, rnd):
        rmb(img, X, Y, W, H, rnd)
        kul(img, X, Y, W, int(H * 0.55), rnd)
    return f


def kuas_kain2(warna, gelap, lipatan=0.06, gradasi=0.14, tepi=True, sisi="lrtb"):
    """Kain dengan lipatan lembut, gradasi, dan outline gelap tipis."""
    ks = [kuas_kain(warna, lipatan=lipatan, gradasi=gradasi)]
    if tepi:
        ks.append(kuas_tepi(campur(rgb(gelap), rgb(warna), 0.25), 1, sisi))
    return kuas_lapis(*ks)


def kuas_kerah(putih=PUTIH, garis=GARIS, sisi="lrb", inset=2, ganda=False):
    """Kain kerah pelaut putih dengan garis tepi gelap."""
    cp, cg = rgb(putih), rgb(garis)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                img.putpixel((X + x, Y + y), ubah(cp, (0.99 - 0.06 * y / max(1, H - 1)) * (1 + rnd.uniform(-0.01, 0.01))))
        abu = campur(cp, cg, 0.35)
        kuas_tepi(abu, 1, sisi)(img, X, Y, W, H, rnd)
        for j in ([inset, inset + 2] if ganda else [inset]):
            if "l" in sisi:
                isi_rect(img, X + j, Y + (j if "t" in sisi else 0), 1, H - j - (j if "t" in sisi else 0), cg)
            if "r" in sisi:
                isi_rect(img, X + W - 1 - j, Y + (j if "t" in sisi else 0), 1, H - j - (j if "t" in sisi else 0), cg)
            if "b" in sisi:
                isi_rect(img, X + j, Y + H - 1 - j, W - 2 * j, 1, cg)
            if "t" in sisi:
                isi_rect(img, X + j, Y + j, W - 2 * j, 1, cg)
    return f


def kuas_pita(warna=PITA, potong=False):
    """Kain pita hitam mengilap; potong=True -> ujung bawah berbentuk V."""
    c = rgb(warna)
    kil = campur(c, rgb("#6a6478"), 0.6)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                u = (x + 0.5) / W
                w = ubah(c, 0.9 + 0.35 * math.sin(math.pi * u))
                if abs(u - 0.35) < 0.1 and 0.1 < y / max(1, H) < 0.7:
                    w = campur(w, kil, 0.6)
                img.putpixel((X + x, Y + y), w)
        kuas_tepi(ubah(c, 0.6), 1)(img, X, Y, W, H, rnd)
        if potong:
            d = max(2, W // 2)
            for x in range(W):
                k = int(d * (1 - abs((x + 0.5) / W - 0.5) * 2))
                isi_rect(img, X + x, Y + H - k, 1, k, KOSONG)
    return f


def kuas_panel_rok(warna=BAJU, gelap=BAJU_G, sisi_terang=True):
    """Satu lipit rok: gradasi melintang (terang -> gelap), garis lipit, tepi bawah."""
    c, g = rgb(warna), rgb(gelap)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            u = (x + 0.5) / W
            t = u if sisi_terang else 1 - u
            for y in range(H):
                v = y / max(1, H - 1)
                w = campur(ubah(c, 1.06), campur(c, g, 0.55), t * 0.8)
                w = ubah(w, (1 - 0.1 * v) * (1 + rnd.uniform(-0.012, 0.012)))
                img.putpixel((X + x, Y + y), w)
        # garis lipit gelap & sisi terang
        isi_rect(img, X + (W - 1 if sisi_terang else 0), Y, 1, H, ubah(g, 0.85))
        isi_rect(img, X + (0 if sisi_terang else W - 1), Y, 1, H, ubah(c, 1.12))
        # tepi bawah (jahitan keliman)
        isi_rect(img, X, Y + H - 1, W, 1, ubah(g, 0.75))
        isi_rect(img, X, Y + H - 4, W, 1, campur(c, g, 0.6))
    return f


def kuas_gembung(warna=BAJU, gelap=BAJU_G):
    """Bahu menggembung: kerut vertikal di atas & bayangan di tepi bawah."""
    c, g = rgb(warna), rgb(gelap)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            lip = 1 + 0.1 * math.sin(x * 1.3)
            for y in range(H):
                v = y / max(1, H - 1)
                w = ubah(c, lip * (1.05 - 0.15 * v))
                img.putpixel((X + x, Y + y), w)
        for x in range(1, W, 3):
            isi_rect(img, X + x, Y, 1, max(1, H // 3), campur(c, g, 0.5))
        isi_rect(img, X, Y + H - 1, W, 1, ubah(g, 0.85))
        isi_rect(img, X, Y + H - 2, W, 1, campur(c, g, 0.5))
    return f


def kuas_stoking(warna=KAUS):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            u = (x + 0.5) / W
            s = 0.85 + 0.35 * math.sin(math.pi * u) ** 3
            for y in range(H):
                img.putpixel((X + x, Y + y), ubah(c, s * (1 + rnd.uniform(-0.03, 0.03))))
        for x in range(W):
            if abs((x + 0.5) / W - 0.45) < 0.08:
                isi_rect(img, X + x, Y, 1, H, campur(c, rgb("#5a5466"), 0.55))
    return f


def kuas_sepatu(warna=SEPATU, jahit=True):
    c = rgb(warna)
    gelap = ubah(c, 0.65)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                v = y / max(1, H - 1)
                img.putpixel((X + x, Y + y), ubah(c, (1.12 - 0.25 * v) * (1 + rnd.uniform(-0.02, 0.02))))
        if jahit and H >= 4:
            for x in range(1, W - 1, 2):
                titik(img, X + x, Y + 1, ubah(c, 1.45))
        if W >= 4 and H >= 3:
            isi_rect(img, X + W // 4, Y + 1, max(1, W // 6), 1, ubah(c, 1.6))
        kuas_tepi(gelap, 1)(img, X, Y, W, H, rnd)
    return f


def kuas_tangan(jari=False):
    kc = rgb(KULIT)
    bay = ubah(kc, 0.86)

    def f(img, X, Y, W, H, rnd):
        kuas_kulit(KULIT, 0.08)(img, X, Y, W, H, rnd)
        if jari:
            for x in range(W // 4, W, W // 4 if W >= 4 else 1):
                isi_rect(img, X + x, Y + H // 3, 1, H - H // 3, bay)
        isi_rect(img, X, Y + H - 1, W, 1, ubah(kc, 0.9))
    return f


def kuas_badan_depan():
    """Depan dada: kain merah muda, bayangan bawah dada, garis tengah."""
    dasar = kuas_kain2(BAJU, BAJU_G, lipatan=0.04, gradasi=0.1, sisi="lr")
    c, g = rgb(BAJU), rgb(BAJU_G)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        isi_rect(img, X + 2, Y + H - 3, W - 4, 1, campur(c, g, 0.5))
        isi_rect(img, X + 3, Y + H - 2, W - 6, 1, campur(c, g, 0.3))
    return f


def kuas_pinggang(depan=False):
    dasar = kuas_kain2(BAJU, BAJU_G, lipatan=0.08, gradasi=0.08, sisi="lr")
    c, g = rgb(BAJU), rgb(BAJU_G)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        # lipatan ke arah sabuk
        for i, x in enumerate(range(W // 5, W, W // 5 if W >= 5 else 1)):
            for y in range(H // 2, H):
                if (y + i) % 1 == 0:
                    titik(img, X + x + (y - H // 2) // 5 * (1 if i % 2 else -1), Y + y, campur(c, g, 0.45))
        if depan:
            isi_rect(img, X + W // 2, Y, 1, H, campur(c, g, 0.55))
    return f


# ===========================================================================
# Helper geometri
# ===========================================================================
def _arah(A, B):
    """Panjang & rotasi [rx, ry, rz] agar sumbu -y kubus mengarah dari A ke B.

    Helai yang hampir mendatar ke arah z memakai rx+ry (bukan rz) supaya
    penampangnya tidak terpuntir."""
    d = [B[i] - A[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    dx, dy, dz = [v / L for v in d]
    if abs(dz) > 0.6 and abs(dz) > abs(dx):
        rx = math.degrees(math.atan2(math.sqrt(dx * dx + dz * dz), -dy))
        ry = math.degrees(math.atan2(dx, dz))
        if dz < 0:  # helai ke depan: rx negatif
            rx = -rx
            ry = math.degrees(math.atan2(-dx, -dz))
        return L, [rx, ry, 0.0]
    cr = math.sqrt(dx * dx + dy * dy)
    rx = math.degrees(math.atan2(dz, cr))
    rz = math.degrees(math.atan2(-dx, -dy)) if cr > 1e-9 else 0.0
    return L, [rx, 0.0, rz]


def untai(m, bone, A, B, w, t, kuas, hadap="depan", cermin=False, inflate=0.0):
    """Kubus memanjang dari titik A (pangkal, pivot) ke titik B (ujung).

    hadap='depan': muka lebar menghadap -z; 'samping': muka lebar menghadap +-x."""
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


def helai_semua_sisi(r=RAMBUT, **kw):
    """Kuas per sisi untuk helai: empat sisi meruncing, atas rambut, bawah kosong."""
    h = kuas_helai(r, **kw)
    bawah = kuas_rambut(r, kilau=-1) if kw.get("runcing", 0.45) <= 0 else (lambda img, X, Y, W, H, rnd: isi_rect(img, X, Y, W, H, KOSONG))
    return kuas_per_sisi(depan=h, belakang=h, kanan=h, kiri=h, atas=kuas_rambut(r, kilau=-1), bawah=bawah)


# ===========================================================================
# Bagian tubuh
# ===========================================================================
def kepala(m):
    rmb = kuas_rambut_halus()
    m.kubus("head", [-4.5, 23.5, -4.5], [9, 9, 9], kuas_per_sisi(
        depan=kuas_muka(),
        kanan=kuas_sisi_kepala("kanan"), kiri=kuas_sisi_kepala("kiri"),
        bawah=kuas_bawah_kepala(), lain=rmb))
    pasang_mata(m, KULIT, IRIS, RAMBUT[1], gaya="putri")
    # telinga
    m.cermin("head", [-4.75, 25.5, -0.6], [0.35, 1.6, 1.1], kuas_per_sisi(
        kanan=kuas_lapis(kuas_kulit(KULIT, 0.12), kuas_rect(ubah(rgb(KULIT), 0.9), 0.3, 0.25, 0.7, 0.75)),
        lain=kuas_kulit(KULIT, 0.12)))
    # leher
    m.kubus("body", [-1.0, 22.6, -1.0], [2.0, 1.2, 2.0], kuas_per_sisi(
        depan=kuas_lapis(kuas_kulit(KULIT, 0.2), kuas_tepi(ubah(rgb(KULIT), 0.85), 1, "t")), lain=kuas_kulit(KULIT, 0.2)))

    # --- mahkota membulat ---
    rmb0 = kuas_rambut(RAMBUT, kilau=-1, gradasi=0.05)
    m.kubus("head", [-4.2, 32.5, -4.3], [8.4, 0.55, 8.6], rmb0)
    m.kubus("head", [-3.3, 33.0, -3.4], [6.6, 0.45, 6.8], rmb0)
    for z in (-3.95, 3.95):  # tepi atas depan & belakang (miring 45)
        m.kubus("head", [-4.3, 32.0 - 0.9, z - 0.9], [8.6, 1.8, 1.8], rmb0, rot=[45, 0, 0])
    m.cermin("head", [-3.95 - 0.9, 32.0 - 0.9, -4.3], [1.8, 1.8, 8.6], rmb0, rot=[0, 0, 45])
    m.cermin("head", [-4.2 - 0.65, 24.3, 4.2 - 0.65], [1.3, 8.0, 1.3], rmb, rot=[0, 45, 0])

    # helai di atas mahkota (disisir ke belakang)
    for x, w in ((-2.55, 2.2), (-0.85, 2.1)):
        untai(m, "head", (x, 33.25, -3.7), (x * 0.75, 33.5, 2.8), w, 0.3, helai_semua_sisi(runcing=0.35, kilau=0.3), cermin=True)

    # --- helai samping disisir ke belakang (menuju ikat rambut) ---
    sisi = [((-4.72, 32.0, -3.6), (-4.72, 30.4, 4.7), 1.7),
            ((-4.78, 30.9, -3.2), (-4.78, 29.6, 4.7), 1.6),
            ((-4.72, 29.9, -2.6), (-4.72, 28.6, 4.6), 1.5),
            ((-4.66, 28.9, -1.4), (-4.66, 27.7, 4.6), 1.2)]
    for A, B, w in sisi:
        untai(m, "head", A, B, w, 0.4, helai_semua_sisi(runcing=0.25, kilau=0.3), hadap="samping", cermin=True)

    # sisi belakang bawah: rambut tengkuk disisir naik
    for A, B, w in (((-4.66, 23.9, 0.9), (-4.66, 28.4, 4.5), 1.5), ((-4.7, 23.8, 2.6), (-4.7, 27.6, 4.7), 1.4)):
        untai(m, "head", A, B, w, 0.35, helai_semua_sisi(runcing=0.4, kilau=0.5), hadap="samping", cermin=True)

    # --- belakang kepala: helai dari tengkuk naik ke ikat rambut ---
    for x in (-3.5, -1.8):
        untai(m, "head", (x, 23.9, 4.62), (x * 0.22, 29.6, 4.9), 2.0, 0.4, helai_semua_sisi(runcing=0.35, kilau=0.55), cermin=True)
    untai(m, "head", (0, 23.9, 4.66), (0, 29.4, 4.95), 2.0, 0.4, helai_semua_sisi(runcing=0.35, kilau=0.55))
    # dari mahkota turun ke ikat rambut
    for x in (-3.0, -1.2):
        untai(m, "head", (x, 33.0, 3.4), (x * 0.25, 30.4, 4.95), 1.8, 0.4, helai_semua_sisi(runcing=0.3, kilau=0.3), cermin=True)
    # anak rambut tengkuk
    for x, L in ((-3.3, 1.4), (-1.7, 1.9), (0.0, 1.5)):
        A = (x, 24.4, 4.35)
        B = (x * 1.05, 24.4 - L, 4.2)
        if x == 0:
            untai(m, "head", A, B, 1.5, 0.4, helai_semua_sisi(runcing=0.6, kilau=None))
        else:
            untai(m, "head", A, B, 1.5, 0.4, helai_semua_sisi(runcing=0.6, kilau=None), cermin=True)


def poni(m):
    m.kubus("head", [-4.55, 29.6, -4.85], [9.1, 3.0, 0.3], kuas_per_sisi(
        depan=kuas_poni(RAMBUT, ujung=(0.55, 1.0), helai_px=6), belakang=kuas_poni(RAMBUT, ujung=(0.55, 1.0), helai_px=6),
        lain=kuas_rambut(RAMBUT, kilau=-1)))
    # (x_pangkal, x_ujung, y_ujung, lebar, z_depan, miring)
    daftar = [
        (3.7, 4.3, 28.5, 1.5, -5.0, 0.4),
        (2.5, 2.7, 28.6, 1.8, -5.05, 0.2),
        (1.3, 0.9, 28.3, 1.8, -5.0, -0.3),
        (0.1, -0.7, 27.9, 1.9, -5.05, -0.5),
        (-1.1, -2.2, 26.6, 1.9, -5.0, -0.5),
        (-1.7, -2.7, 25.5, 1.4, -5.25, -0.6),   # menutupi sebagian mata kanan
        (-2.6, -3.6, 26.6, 1.7, -5.05, -0.5),
        (-3.8, -4.5, 27.4, 1.5, -5.0, -0.4),
        (0.8, -0.3, 28.9, 1.3, -5.3, -0.4),     # lapisan depan
        (2.9, 3.4, 29.2, 1.3, -5.3, 0.3),
        (-0.4, -1.5, 27.3, 1.2, -5.35, -0.5),
    ]
    for xa, xb, yb, w, z, mir in daftar:
        untai(m, "head", (xa, 32.75, z + 0.2), (xb, yb, z), w, 0.35,
              helai_semua_sisi(runcing=0.55, kilau=0.18, miring=mir))


def rambut_samping(m):
    """Jumbai samping wajah (tulang rambut_kanan / rambut_kiri)."""
    jumbai = [((-4.25, 31.6, -4.62), (-4.55, 21.8, -4.1), 1.6, 0.5, 0.45),
              ((-4.85, 31.2, -3.7), (-5.35, 22.8, -3.0), 1.5, 0.5, 0.5),
              ((-4.95, 30.4, -2.5), (-5.25, 25.0, -1.9), 1.3, 0.5, 0.55),
              ((-3.75, 31.8, -4.8), (-3.9, 24.6, -4.75), 1.0, 0.35, 0.6),
              ((-4.6, 30.6, -4.35), (-5.2, 20.6, -3.7), 0.9, 0.4, 0.7),
              ((-5.05, 29.4, -3.2), (-5.7, 23.6, -2.6), 0.9, 0.4, 0.7)]
    for A, B, w, t, rc in jumbai:
        untai(m, "rambut_kanan", A, B, w, t, helai_semua_sisi(runcing=rc, kilau=0.2, miring=0.3), cermin=True)


def ekor_kuda(m):
    """Ekor kuda tinggi + ikat rambut biru tua."""
    ikat = kuas_lapis(kuas_kain(IKAT, lipatan=0.25, gradasi=0.25), kuas_tepi(ubah(rgb(IKAT), 0.6)),
                      kuas_strip_h(campur(rgb(IKAT), rgb("#ffffff"), 0.3), 1, 1, 0.1, 0.9))
    m.kubus("ekor_kuda", [-1.2, 28.95, 4.45], [2.4, 1.9, 1.3], ikat)  # pangkal di kepala
    m.kubus("ekor_kuda", [-2.0, 29.5, 4.6], [4.0, 1.2, 3.8], ikat)     # cincin ikat rambut
    m.kubus("ekor_kuda", [-0.45, 29.75, 8.35], [0.9, 0.75, 0.3], kuas_lapis(kuas_kain(ubah(rgb(IKAT), 0.8), 0, 0.2),
                                                                          kuas_tepi(ubah(rgb(IKAT), 0.5))))
    # gumpalan di atas ikat (rambut naik sedikit lalu jatuh)
    untai(m, "ekor_kuda", (0, 30.5, 6.5), (0, 32.3, 7.1), 3.4, 2.6, helai_semua_sisi(runcing=0, kilau=0.45))
    untai(m, "ekor_kuda", (0, 30.5, 6.6), (0, 22.8, 6.0), 3.8, 2.8, helai_semua_sisi(runcing=0, kilau=0.1))
    # helai luar bagian atas: keluar dari bawah ikat, melebar ke bawah
    atas = [((-1.3, 29.9, 7.6), (-2.4, 22.4, 7.3), 1.8, 0.6, 0.3),
            ((-1.5, 29.9, 5.4), (-2.5, 23.0, 4.9), 1.6, 0.6, 0.3),
            ((-1.6, 29.9, 6.5), (-2.75, 22.6, 6.0), 0.6, 1.8, 0.3),
            ((0.0, 29.9, 7.8), (0.0, 22.0, 7.6), 2.0, 0.6, 0.3),
            ((-0.6, 29.9, 7.9), (-1.1, 22.8, 8.0), 1.4, 0.5, 0.35),
            ((-0.9, 31.9, 7.5), (-1.5, 30.0, 8.9), 1.4, 0.5, 0.5),
            ((0.0, 32.1, 7.4), (0.0, 30.4, 9.2), 1.6, 0.5, 0.5)]
    for A, B, w, t, rc in atas:
        untai(m, "ekor_kuda", A, B, w, t, helai_semua_sisi(runcing=rc, kilau=0.2), cermin=(A[0] != 0))
    # ekor kuda bawah (meruncing, sampai punggung bawah)
    untai(m, "ekor_kuda2", (0, 23.6, 6.0), (0, 14.4, 3.9), 3.2, 2.4, helai_semua_sisi(runcing=0.5, kilau=0.12))
    bawah = [((-1.6, 23.6, 7.0), (-1.3, 13.6, 4.6), 1.6, 0.6, 0.6, 0.3),
             ((-1.9, 23.4, 5.2), (-1.0, 15.0, 3.4), 1.4, 0.6, 0.6, 0.3),
             ((-2.4, 23.5, 6.1), (-1.7, 15.6, 4.1), 0.6, 1.5, 0.65, 0.0),
             ((0.0, 23.7, 7.6), (0.3, 12.4, 4.8), 1.9, 0.6, 0.65, -0.3),
             ((-0.8, 23.6, 7.5), (-0.5, 13.0, 5.2), 1.3, 0.5, 0.7, 0.4),
             ((0.0, 23.4, 4.6), (0.1, 14.2, 3.0), 1.6, 0.5, 0.6, 0.0)]
    for A, B, w, t, rc, mir in bawah:
        untai(m, "ekor_kuda2", A, B, w, t, helai_semua_sisi(runcing=rc, kilau=0.12, miring=mir), cermin=(A[0] != 0))


def badan(m):
    # dada / pinggang / pinggul (meruncing)
    m.kubus("body", [-3.5, 18.5, -2.0], [7.0, 4.5, 4.0], kuas_per_sisi(
        depan=kuas_badan_depan(), lain=kuas_kain2(BAJU, BAJU_G, sisi="lr")))
    m.kubus("body", [-2.9, 18.65, -2.35], [5.8, 2.5, 0.5], kuas_kain2(BAJU, BAJU_G, gradasi=0.2))
    m.kubus("body", [-3.0, 14.2, -1.8], [6.0, 4.4, 3.6], kuas_per_sisi(
        depan=kuas_pinggang(True), lain=kuas_pinggang(False)))
    m.kubus("body", [-2.8, 12.4, -1.65], [5.6, 2.0, 3.3], kuas_kain2(BAJU, BAJU_G))
    # kancing gelap (dua baris)
    kc = kuas_lapis(kuas_kain(KANCING, lipatan=0, gradasi=0.3), kuas_tepi(ubah(rgb(KANCING), 0.6)))
    for y in (17.2, 15.6):
        m.cermin("body", [-1.75, y, -2.0], [0.55, 0.55, 0.3], kc)

    # lambang sekolah (dada kiri)
    m.kubus("body", [1.8, 19.95, -2.47], [0.85, 0.85, 0.15], kuas_lapis(kuas_polos("#d8b45a", 0.02, 0.2), kuas_tepi("#8a6a2a"),
                                                                       kuas_rect("#f7f4f2", 0.4, 0.3, 0.6, 0.7)))
    # --- kerah pelaut ---
    bahu = kuas_kerah(sisi="lr", inset=2)
    m.cermin("body", [-3.65, 22.95, -2.25], [2.6, 0.35, 4.5], kuas_per_sisi(
        atas=kuas_kerah(sisi="l", inset=2), lain=kuas_kerah(sisi="", inset=2)))
    # V di depan
    untai(m, "body", (-2.55, 23.1, -2.18), (-0.12, 19.3, -2.62), 1.7, 0.25,
          kuas_per_sisi(depan=kuas_kerah(sisi="lb", inset=2), lain=kuas_kerah(sisi="")), cermin=True)
    # tepi kerah di bahu (sisi lengan)
    m.cermin("body", [-3.75, 20.9, -2.12], [0.3, 2.3, 4.24], kuas_per_sisi(kanan=kuas_kerah(sisi="lrb", inset=2), lain=kuas_kerah(sisi="")))
    # flap persegi di punggung (bergoyang di tulang jubah)
    m.kubus("jubah", [-3.75, 18.2, 2.1], [7.5, 4.95, 0.3], kuas_per_sisi(
        belakang=kuas_kerah(sisi="lrb", inset=2, ganda=True), depan=kuas_kerah(sisi=""), lain=kuas_kerah(sisi="")),
        rot=[5, 0, 0], pivot=[0, 23.15, 2.25])
    m.kubus("jubah", [-1.2, 22.7, 2.05], [2.4, 0.5, 0.4], kuas_kerah(sisi=""))

    # --- pita hitam ---
    pita = kuas_pita()
    m.kubus("body", [-0.55, 19.0, -3.0], [1.1, 1.0, 0.55], pita)
    untai(m, "body", (-0.4, 19.5, -2.8), (-2.2, 19.9, -2.7), 1.4, 0.45, pita, cermin=True)
    untai(m, "body", (-0.5, 19.3, -2.78), (-1.9, 18.6, -2.72), 0.9, 0.4, pita, cermin=True)
    untai(m, "pita", (-0.2, 19.3, -2.85), (-0.85, 15.4, -2.75), 1.0, 0.3, kuas_per_sisi(
        depan=kuas_pita(potong=True), belakang=kuas_pita(potong=True), lain=kuas_pita()), cermin=True)

    # --- sabuk kain (cincin 8 sisi) ---
    sabuk = kuas_lapis(kuas_kain(campur(rgb(BAJU), rgb(BAJU_G), 0.45), lipatan=0.03, gradasi=0.1),
                       kuas_tepi(ubah(rgb(BAJU_G), 0.7), 1, "tb"))
    for i in range(8):
        a = i * 45
        x, z = 3.62 * math.sin(math.radians(a)), -2.38 * math.cos(math.radians(a))
        lebar = 2.95 if i % 2 == 0 else 2.75
        if i in (0, 4):
            lebar = 3.0
        if i in (2, 6):
            lebar = 2.0
        m.kubus("rok", [x - lebar / 2, 13.75, z - 0.2], [lebar, 0.95, 0.4], sabuk, rot=[0, -a, 0], pivot=[x, 14.2, z])
    # gesper kecil
    m.kubus("rok", [-0.6, 13.65, -2.82], [1.2, 1.15, 0.3], kuas_lapis(kuas_kain(BAJU_G, 0, 0.2), kuas_tepi(ubah(rgb(BAJU_G), 0.7)),
                                                                    kuas_rect(campur(rgb(BAJU), rgb(BAJU_G), 0.3), 0.3, 0.3, 0.7, 0.7)))


def lengan(m):
    kain = kuas_kain2(BAJU, BAJU_G, lipatan=0.08, gradasi=0.1)
    m.cermin("rightArm", [-7.0, 17.0, -1.5], [3.0, 4.0, 3.0], kain)
    m.cermin("rightArm", [-7.35, 20.55, -1.85], [3.6, 2.6, 3.7], kuas_gembung())
    m.cermin("rightArm", [-6.95, 23.1, -1.4], [2.75, 0.35, 2.8], kuas_kain2(BAJU, BAJU_G, gradasi=0.0))
    m.cermin("rightForearm", [-6.9, 13.6, -1.4], [2.8, 3.7, 2.8], kuas_kain2(BAJU, BAJU_G, lipatan=0.1, gradasi=0.12))
    # manset putih
    m.cermin("rightForearm", [-7.1, 12.7, -1.6], [3.2, 1.1, 3.2], kuas_per_sisi(
        atas=kuas_kerah(sisi=""), bawah=kuas_kerah(sisi=""), lain=kuas_kerah(sisi="tb", inset=1)))
    m.cermin("rightForearm", [-7.25, 13.05, -0.3], [0.2, 0.45, 0.45], kuas_lapis(kuas_kain(KANCING, 0, 0.2)))
    # tangan
    m.cermin("rightForearm", [-6.7, 10.95, -1.2], [2.4, 2.0, 2.4], kuas_tangan())
    m.cermin("rightForearm", [-6.6, 10.35, -1.05], [2.15, 0.7, 2.0], kuas_tangan(jari=True))
    m.cermin("rightForearm", [-4.95, 11.2, -1.55], [0.75, 1.35, 0.8], kuas_tangan())


def kaki(m):
    st = kuas_stoking()
    m.cermin("rightLeg", [-3.4, 6.2, -1.5], [3.0, 5.8, 3.0], st)
    m.cermin("rightShin", [-3.3, 1.2, -1.4], [2.8, 5.3, 2.8], st)
    m.cermin("rightShin", [-3.2, 2.8, -1.25], [2.6, 2.4, 2.85], st)
    # loafer
    m.cermin("rightShin", [-3.55, 0.0, -2.55], [3.3, 0.35, 4.15], kuas_sepatu(SOL, jahit=False))
    m.cermin("rightShin", [-3.45, 0.3, -2.3], [3.1, 1.3, 3.8], kuas_sepatu())
    m.cermin("rightShin", [-3.25, 0.25, -2.5], [2.7, 1.0, 0.35], kuas_sepatu())
    m.cermin("rightShin", [-3.0, 0.2, -2.68], [2.2, 0.8, 0.3], kuas_sepatu(jahit=False))
    m.cermin("rightShin", [-3.15, 0.06, -2.82], [2.5, 0.22, 0.5], kuas_sepatu(SOL, jahit=False))
    m.cermin("rightShin", [-3.52, 1.45, -1.95], [3.24, 0.3, 1.05], kuas_sepatu(ubah(rgb(SEPATU), 0.75), jahit=False))
    m.cermin("rightShin", [-3.52, 0.4, 0.9], [3.24, 1.6, 0.75], kuas_sepatu())


def rok(m):
    """Rok lipit di bawah lutut: 20 panel melebar, dibagi ke rok_depan/belakang/kanan/kiri."""
    n = 20
    y_atas, panjang, mekar = 14.25, 9.75, 10.0
    for i in range(n):
        a = (i + 0.5) * 360.0 / n - 180.0  # -180..180, 0 = depan
        luar = 0.12 if i % 2 == 0 else -0.05
        rx_, rz_ = 3.72 + luar, 2.42 + luar
        x, z = rx_ * math.sin(math.radians(a)), -rz_ * math.cos(math.radians(a))
        if abs(a) <= 45:
            bone = "rok_depan"
        elif abs(a) >= 135:
            bone = "rok_belakang"
        elif a < 0:
            bone = "rok_kanan"
        else:
            bone = "rok_kiri"
        w = 1.7
        kuas = kuas_per_sisi(depan=kuas_panel_rok(sisi_terang=(i % 2 == 0)), belakang=kuas_panel_rok(BAJU_G, ubah(rgb(BAJU_G), 0.8)),
                             lain=kuas_panel_rok(sisi_terang=True))
        m.kubus(bone, [x - w / 2, y_atas - panjang, z - 0.2], [w, panjang, 0.4], kuas,
                rot=[-mekar, -a, 0], pivot=[x, y_atas, z])


def buat():
    m = Model("subaru", "Subaru Hoshina", "Subaru Hoshina (Seragam Kikyo)", skala=0.92,
              deskripsi="Sahabat Kaoruko di Kikyo: anggun & tenang, rambut perak ekor kuda tinggi, seragam pelaut Kikyo merah muda.")
    kepala(m)
    poni(m)
    rambut_samping(m)
    ekor_kuda(m)
    badan(m)
    lengan(m)
    kaki(m)
    rok(m)
    return [m]
