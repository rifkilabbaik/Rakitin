"""Kaoruko Waguri (Kaoru Hana wa Rin to Saku) - model detail ala Yes Steve Model.

Dua model berbagi kepala/rambut/wajah yang sama (fungsi kepala()):
  * kaoruko         : seragam Kikyo Private Academy (pelaut merah muda pudar).
  * kaoruko_kasual  : gaya kencan feminin (blus krem, rok panjang lavender).

Rambut panjang bergelombang dibangun dari banyak helai tipis berotasi:
  - mahkota berbentuk kubah oktagonal bertingkat + bevel (kepala tidak kotak),
  - poni 9 helai runcing, helai pembingkai pipi, tirai samping,
  - jumbai depan bahu bergelombang (rambut_kanan / rambut_kiri),
  - lapisan belakang atas (rambut_belakang) & bawah berombak S (rambut_belakang2).
"""
import math

from inti import (Model, rgb, ubah, campur, titik, isi_rect, KOSONG, kuas_kosong, kuas_lapis, kuas_kain,
                  kuas_wajah, kuas_kulit, kuas_per_sisi, kuas_polos, kuas_strip_h, pasang_mata)

# ---------------------------------------------------------------------------
# Palet
# ---------------------------------------------------------------------------
RAMBUT = ("#2f2338", "#1e1625", "#6a5684")
KULIT = "#fce4d6"
IRIS = "#3a4d8f"

# seragam Kikyo
PINK = "#c98f9b"
PINK_G = "#9f6874"
PUTIH = "#f7f4f2"
GARIS = "#4a3a46"
HITAM = "#1c1a22"
STOKING = "#24212b"
LOAFER = "#4b2f22"

# kasual
BANDO_PINK = "#e58fa6"
KREM = "#f5ead9"
KREM_G = "#d9c8b0"
RENDA = "#ffffff"
LAVENDER = "#b9a6d6"
LAVENDER_G = "#9583b8"
SEPATU_BEIGE = "#c8a98a"
KARDIGAN = "#f0d4da"
KARDIGAN_G = "#cfa3ae"


# ===========================================================================
# Kuas tambahan (tanda tangan f(img, X, Y, W, H, rnd), koordinat piksel)
# ===========================================================================
def _potong_ujung(img, X, Y, W, H, pola, pmin, gelap, fase=0.0):
    """Potong tepi bawah muka (ujung helai) menurut pola + beri garis gelap di ujung."""
    if not pola:
        return
    for x in range(W):
        p = (x + 0.5) / W
        if pola == "runcing":
            t = 1 - abs(2 * p - 1)
        elif pola == "ikal":
            t = math.sqrt(max(0.0, 1 - (2 * p - 1) ** 2))
        elif pola == "gelombang":
            t = 0.5 + 0.5 * math.sin(p * 6.28 + fase)
        elif pola == "miring":
            t = p
        elif pola == "miring_kiri":
            t = 1 - p
        elif pola == "takik":  # ujung pita berlekuk V ke dalam
            t = abs(2 * p - 1)
        else:
            t = 1.0
        panjang = int(round(H * (pmin + (1 - pmin) * t)))
        panjang = max(1, min(H, panjang))
        isi_rect(img, X + x, Y + panjang, 1, H - panjang, KOSONG)
        if panjang >= 2 and gelap is not None:
            titik(img, X + x, Y + panjang - 1, gelap)


def kuas_helai(r=RAMBUT, pola="runcing", pmin=0.6, kilau=0.22, gelombang=0.07, gradasi=0.22, gelap=1.0,
               tepi=True, akar=0.12):
    """Helai rambut: guratan vertikal, tepi gelap, pita kilau zig-zag, bayangan akar,
    gelombang terang-gelap miring (rambut berombak), ujung runcing/ikal/gelombang."""
    c, g, t = (ubah(rgb(x), gelap) for x in r)

    terang = campur(c, t, 0.32)
    mid = campur(c, t, 0.12)

    def f(img, X, Y, W, H, rnd):
        fase = rnd.uniform(0, 6.28)
        # guratan helai: tiap kolom terang / sedang / gelap
        jenis = []
        for x in range(W):
            if x % 2 and rnd.random() < 0.75:
                jenis.append(jenis[-1])
                continue
            v = math.sin(x * 1.2 + fase) + rnd.uniform(-0.6, 0.6)
            jenis.append(2 if v > 0.8 else (0 if v < -0.85 else 1))
        yk = int(H * kilau) + rnd.randint(-1, 1) if kilau is not None else -999
        tk = max(1, H // 16)
        # panjang garis kilau vertikal di bawah/atas cincin kilau
        ekor = [rnd.randint(0, max(1, H // 6)) if jenis[x] == 2 else rnd.randint(0, 2) for x in range(W)]
        for y in range(H):
            ty = y / max(1, H - 1)
            for x in range(W):
                dasar = (terang, mid, g)[2 - jenis[x]] if jenis[x] != 0 else campur(c, g, 0.45)
                gd = (1 - gradasi * ty)
                gd *= 1 + gelombang * math.sin((y + x * 0.7) / 10.0 * 6.28 + fase)
                if akar and ty < akar:
                    gd *= 0.82 + 0.18 * (ty / akar)
                w = ubah(dasar, gd * (1 + rnd.uniform(-0.02, 0.02)))
                if H >= 12 and kilau is not None:
                    yy = yk + ((x // 2) % 2)
                    dy = y - yy
                    if 0 <= dy < tk + 1 and (x + y) % 5 != 0:
                        w = campur(w, t, 0.8 if dy < tk else 0.45)
                    elif (-ekor[x] <= dy < 0 or tk + 1 <= dy <= tk + ekor[x]) and jenis[x] >= 1:
                        w = campur(w, t, 0.38 if jenis[x] == 2 else 0.2)
                if tepi and (x == 0 or x == W - 1):
                    w = campur(w, g, 0.7)
                img.putpixel((X + x, Y + y), w)
        _potong_ujung(img, X, Y, W, H, pola, pmin, ubah(g, 0.9), fase)
    return f


def k_helai(pola="runcing", pmin=0.6, kilau=0.22, gelombang=0.07, gelap=1.0, r=RAMBUT):
    """Kuas per sisi untuk satu helai: muka luar berkilau, dalam lebih gelap, bawah kosong."""
    luar = kuas_helai(r, pola, pmin, kilau, gelombang, gelap=gelap)
    dalam = kuas_helai(r, pola, pmin, None, gelombang, gelap=gelap * 0.78)
    samping = kuas_helai(r, pola, pmin, kilau, gelombang, gelap=gelap * 0.9, tepi=False)
    return kuas_per_sisi(depan=luar, belakang=dalam, kanan=samping, kiri=samping,
                         atas=kuas_helai(r, None, kilau=None, gelap=gelap * 0.95), bawah=kuas_kosong())


def k_rambut_padat(gelap=1.0, kilau=0.3, r=RAMBUT):
    return kuas_helai(r, None, kilau=kilau, gelap=gelap, akar=0.0)


def kuas_kain2(warna, gelap=None, lipatan=0.05, gradasi=0.1, tepi="lr", kuat_tepi=0.55):
    """Kain + garis tepi lembut (outline) di sisi yang dipilih (l, r, t, b)."""
    c = rgb(warna)
    g = rgb(gelap) if gelap else ubah(c, 0.72)
    dasar = kuas_kain(warna, lipatan, gradasi)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        for y in range(H):
            for x in range(W):
                tep = (("l" in tepi and x == 0) or ("r" in tepi and x == W - 1) or
                       ("t" in tepi and y == 0) or ("b" in tepi and y == H - 1))
                if tep:
                    img.putpixel((X + x, Y + y), campur(img.getpixel((X + x, Y + y)), g, kuat_tepi))
    return f


def kuas_lipit2(warna, gelap, hem=None, jahitan=None, terang=1.1):
    """Satu panel lipit rok: sisi kiri terang, lipatan gelap di kanan, jahitan & keliman bawah."""
    c, g = rgb(warna), rgb(gelap)
    hm = rgb(hem) if hem else ubah(g, 0.9)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            p = x / max(1, W - 1)
            if x == 0:
                b = ubah(c, terang)
            elif x >= W - 2:
                b = campur(c, g, 0.75 if x == W - 1 else 0.45)
            else:
                b = campur(ubah(c, 1.04), c, p)
            for y in range(H):
                ty = y / max(1, H - 1)
                gd = 1 - 0.1 * ty
                if y < 2:
                    gd *= 0.88  # bayangan di bawah sabuk
                img.putpixel((X + x, Y + y), ubah(b, gd * (1 + rnd.uniform(-0.012, 0.012))))
        if H >= 8:
            if jahitan:
                for x in range(0, W, 2):
                    titik(img, X + x, Y + H - 4, jahitan)
            isi_rect(img, X, Y + H - 2, W, 1, campur(c, g, 0.35))
            isi_rect(img, X, Y + H - 1, W, 1, hm)
    return f


def kuas_kerah(putih, garis, sisi="lrb", inset=2, tebal=1, dasar_gelap=0.97):
    """Kain kerah pelaut putih dengan garis tepi gelap sejajar tepi (inset piksel)."""
    p, g = rgb(putih), rgb(garis)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                img.putpixel((X + x, Y + y), ubah(p, (1 - 0.06 * y / max(1, H - 1)) * dasar_gelap
                                                  * (1 + rnd.uniform(-0.01, 0.01))))
        for i in range(tebal):
            if "l" in sisi:
                isi_rect(img, X + inset + i, Y, 1, H - (inset if "b" in sisi else 0), g)
            if "r" in sisi:
                isi_rect(img, X + W - 1 - inset - i, Y, 1, H - (inset if "b" in sisi else 0), g)
            if "b" in sisi:
                x0 = X + (inset if "l" in sisi else 0)
                x1 = X + W - (inset if "r" in sisi else 0)
                isi_rect(img, x0, Y + H - 1 - inset - i, x1 - x0, 1, g)
            if "t" in sisi:
                isi_rect(img, X, Y + inset + i, W, 1, g)
        # bayangan tepi luar sangat tipis
        for x in range(W):
            titik(img, X + x, Y + H - 1, ubah(p, 0.86))
    return f


def kuas_renda(warna, dasar=None, lubang=True, garis="#d9c3c8"):
    """Renda: tepi bawah bergerigi bulat + lubang kecil + garis tepi lembut."""
    c = rgb(warna)
    d = rgb(dasar) if dasar else ubah(c, 0.9)
    gr = rgb(garis)

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X, Y, W, H, c)
        isi_rect(img, X, Y, W, 1, d)
        for x in range(W):
            a = 1 if (x % 4) in (0, 3) else 0
            if H >= 3:
                isi_rect(img, X + x, Y + H - a, 1, a, KOSONG)
                titik(img, X + x, Y + H - a - 1, gr)
            if lubang and H >= 4 and x % 4 == 1:
                titik(img, X + x, Y + H - 2, d)
        if H > 4:
            for y in range(1, H - 2):
                titik(img, X + W // 2, Y + y, d) if y % 3 == 0 else None
    return f


def kuas_pita(warna, kilap=None, lipatan=True):
    """Kain pita/dasi satin: kilap diagonal + bayangan tepi."""
    c = rgb(warna)
    kl = rgb(kilap) if kilap else campur(c, "#ffffff", 0.22)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                w = c
                if lipatan and (x + y) % 7 in (0, 1) and 0 < x < W - 1:
                    w = campur(c, kl, 0.55)
                if x == 0 or x == W - 1 or y == H - 1:
                    w = ubah(c, 0.7)
                img.putpixel((X + x, Y + y), w)
    return f


def kuas_rajut(warna, gelap, vertikal=True):
    """Rajutan rib (manset/kelim kardigan): garis vertikal berselang."""
    c, g = rgb(warna), rgb(gelap)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                k = (x if vertikal else y) % 2
                img.putpixel((X + x, Y + y), ubah(campur(c, g, 0.35 if k else 0.0), 1 + rnd.uniform(-0.02, 0.02)))
    return f


def kuas_kardigan_depan(warna, gelap, buka=0.36, kancing=None):
    """Muka depan kardigan terbuka: dua panel tepi berkelim rajut, bagian tengah kosong."""
    kain = kuas_kain2(warna, gelap, lipatan=0.05, tepi="")
    c, g = rgb(warna), rgb(gelap)

    def f(img, X, Y, W, H, rnd):
        kain(img, X, Y, W, H, rnd)
        lebar = int(W * (1 - buka) / 2)
        for y in range(H):
            # bukaan melebar sedikit ke atas (kerah V)
            tambah = int((1 - y / max(1, H - 1)) * W * 0.06)
            x0, x1 = X + lebar - tambah, X + W - lebar + tambah
            isi_rect(img, x0, Y + y, x1 - x0, 1, KOSONG)
            for d in (1, 2):
                titik(img, x0 - d, Y + y, campur(c, g, 0.45 if (y % 2) else 0.25))
                titik(img, x1 - 1 + d, Y + y, campur(c, g, 0.45 if (y % 2) else 0.25))
            titik(img, x0 - 3, Y + y, ubah(g, 0.9))
            titik(img, x1 + 2, Y + y, ubah(g, 0.9))
        for x in range(W):  # kelim rajut bawah
            for y in range(H - 3, H):
                if img.getpixel((X + x, Y + y))[3]:
                    img.putpixel((X + x, Y + y), campur(c, g, 0.4 if x % 2 else 0.15))
        if kancing:
            for i in range(3):
                yy = Y + int(H * (0.3 + 0.22 * i))
                isi_rect(img, X + lebar - 8 + 3, yy, 2, 2, kancing)
    return f


def kuas_jahit_v(warna, posisi=(0.25, 0.75)):
    """Garis jahitan/princess seam vertikal halus."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for p in posisi:
            x = X + int(W * p)
            for y in range(H):
                w = img.getpixel((x, Y + y))
                img.putpixel((x, Y + y), campur(w, c, 0.55))
                w2 = img.getpixel((x + 1, Y + y))
                img.putpixel((x + 1, Y + y), ubah(w2, 1.05))
    return f


def kuas_kulit2(kulit, bayang_atas=0):
    """Kulit dengan gradasi; bayang_atas = baris piksel atas yang lebih gelap (bayangan)."""
    dasar = kuas_kulit(kulit, 0.08)
    kc = rgb(kulit)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        for y in range(min(H, bayang_atas)):
            isi_rect(img, X, Y + y, W, 1, ubah(kc, 0.86 + 0.04 * y))
    return f


def kuas_tangan(kulit, jari=True):
    """Telapak/punggung tangan dengan garis jari."""
    kc = rgb(kulit)
    dasar = kuas_kulit(kulit, 0.06)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        if jari and W >= 6:
            for x in range(2, W - 1, 2):
                isi_rect(img, X + x, Y + H // 2, 1, H - H // 2, ubah(kc, 0.88))
        isi_rect(img, X, Y + H - 1, W, 1, ubah(kc, 0.9))
    return f


def kuas_wajah_detail(kulit):
    """Lapisan tambahan wajah: rona pipi bergaris, hidung kecil, bayangan poni di dahi."""
    kc = rgb(kulit)
    pink = rgb("#f49aa9")
    garis = rgb("#e46f82")

    def f(img, X, Y, W, H, rnd):
        cx = X + W // 2
        # bayangan poni di dahi
        for y in range(int(H * 0.12), int(H * 0.32)):
            for x in range(W):
                w = img.getpixel((X + x, Y + y))
                if w[3]:
                    img.putpixel((X + x, Y + y), campur(w, ubah(kc, 0.84), 0.5))
        # rona pipi (oval) + garis-garis malu
        for sx in (-1, 1):
            x0 = cx + sx * 11 - (1 if sx < 0 else 0)
            for dx in range(-3, 4):
                for dy in (0, 1):
                    a = (0.62 if abs(dx) < 2 else 0.38) * (1.0 if dy == 0 else 0.65)
                    titik(img, x0 + dx, Y + 29 + dy, campur(kc, pink, a))
            for i in (-2, 0, 2):
                titik(img, x0 + i + 1, Y + 29, campur(kc, garis, 0.7))
                titik(img, x0 + i, Y + 30, campur(kc, garis, 0.5))
        # hidung
        titik(img, cx, Y + 29, ubah(kc, 0.86))
        titik(img, cx - 1, Y + 29, ubah(kc, 0.94))
        # bayangan rahang di sisi
        for y in range(int(H * 0.55), H):
            titik(img, X, Y + y, ubah(kc, 0.92))
            titik(img, X + W - 1, Y + y, ubah(kc, 0.92))
    return f


def kuas_kaus_kaki(warna, rajut=True, tepi_atas=None):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                w = ubah(c, (1 - 0.08 * y / max(1, H - 1)) * (0.94 if (rajut and x % 3 == 0) else 1.0)
                         * (1 + rnd.uniform(-0.015, 0.015)))
                img.putpixel((X + x, Y + y), w)
        if tepi_atas:
            isi_rect(img, X, Y, W, 1, tepi_atas)
    return f


def kuas_stoking(warna, kilap_lutut=False):
    """Stoking hitam semi-tipis: sedikit terang di tengah (kesan silinder)."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for x in range(W):
            p = x / max(1, W - 1)
            k = 1 + 0.16 * (1 - abs(2 * p - 1) ** 1.5)
            for y in range(H):
                w = ubah(c, k * (1 - 0.06 * y / max(1, H - 1)) * (1 + rnd.uniform(-0.02, 0.02)))
                img.putpixel((X + x, Y + y), w)
        if kilap_lutut:
            isi_rect(img, X + W // 2 - 1, Y + 1, 2, 2, ubah(c, 1.45))
    return f


def kuas_kulit_sepatu(warna, kilap=True, jahitan=None):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                img.putpixel((X + x, Y + y), ubah(c, (1.05 - 0.15 * y / max(1, H - 1)) * (1 + rnd.uniform(-0.02, 0.02))))
        if kilap and W > 4:
            isi_rect(img, X + 1, Y + 1, max(1, W // 3), 1, ubah(c, 1.35))
        if jahitan and H > 3:
            for x in range(1, W - 1, 2):
                titik(img, X + x, Y + H - 2, jahitan)
        isi_rect(img, X, Y + H - 1, W, 1, ubah(c, 0.7))
    return f


# ===========================================================================
# Helper geometri
# ===========================================================================
def helai(m, bone, cx, ytop, cz, w, h, t, kuas, rot=None, cermin=False, pivot=None):
    """Helai/kubus dengan pivot di tengah-atas (berayun dari pangkalnya)."""
    origin = [cx - w / 2, ytop - h, cz - t / 2]
    piv = pivot or [cx, ytop, cz]
    if cermin:
        return m.cermin(bone, origin, [w, h, t], kuas, rot=rot, pivot=piv if rot else None)
    return m.kubus(bone, origin, [w, h, t], kuas, rot=rot, pivot=piv if rot else None)


def helai_s(m, bone, cx, ytop, cz, w, h1, h2, t, rz1, rz2, kuas1, kuas2, ry=0, rx=0, cermin=False):
    """Helai berombak dua ruas (S): ruas atas rz1, ruas bawah rz2 menyambung di ujungnya.

    ry = arah hadap helai (0 = depan menghadap -z). Kemiringan rz dihitung pada
    bidang helai."""
    helai(m, bone, cx, ytop, cz, w, h1, t, kuas1, rot=[rx, ry, rz1], cermin=cermin)
    # ujung ruas atas = pangkal ruas bawah (dihitung dengan matriks rotasi Bedrock)
    import inti as _inti
    v = _inti._rot_bedrock([rx, ry, rz1]) @ [0.0, -(h1 - 0.45), 0.0]
    nrm = _inti._rot_bedrock([rx, ry, rz1]) @ [0.0, 0.0, -1.0]
    x2, y2, z2 = cx + v[0] - nrm[0] * t * 0.3, ytop + v[1], cz + v[2] - nrm[2] * t * 0.3
    helai(m, bone, x2, y2, z2, w * 0.92, h2, t * 0.95, kuas2, rot=[rx * 1.5, ry, rz2], cermin=cermin)


def batang_xy(m, bone, p0, p1, z0, kedalaman, tebal, kuas, cermin=False, perpanjang=0.0):
    """Balok dari titik p0 ke p1 (bidang xy), tebal tegak lurus, kedalaman sepanjang z (z0..z0+kedalaman)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) + 2 * perpanjang
    cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    rz = -math.degrees(math.atan2(dy, dx))
    origin = [cx - L / 2, cy - tebal / 2, z0]
    piv = [cx, cy, z0 + kedalaman / 2]
    f = m.cermin if cermin else m.kubus
    return f(bone, origin, [L, tebal, kedalaman], kuas, rot=[0, 0, rz], pivot=piv)


def batang_zy(m, bone, p0, p1, x0, lebar, tebal, kuas, perpanjang=0.0):
    """Balok dari (z, y) p0 ke p1, lebar sepanjang x (x0..x0+lebar)."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dz, dy) + 2 * perpanjang
    cz, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    rx = math.degrees(math.atan2(dy, dz))
    origin = [x0, cy - tebal / 2, cz - L / 2]
    piv = [x0 + lebar / 2, cy, cz]
    return m.kubus(bone, origin, [lebar, tebal, L], kuas, rot=[rx, 0, 0], pivot=piv)


def lapis_oktagon(m, bone, y0, h, a, c, kuas, kuas_depan=None, y0_depan=None):
    """Satu lapis kubah: penampang oktagon (2 balok bersilang + 4 pelat diagonal)."""
    m.kubus(bone, [-a, y0, -c], [2 * a, h, 2 * c], kuas)
    yd = y0 if y0_depan is None else y0_depan
    kb = kuas
    if kuas_depan:
        kb = kuas_per_sisi(depan=kuas_depan, lain=kuas)
    m.kubus(bone, [-c, yd, -a], [2 * c, (y0 + h + 0.06) - yd, 2 * a], kb)
    L = (a - c) * math.sqrt(2)
    t = (a - c) / math.sqrt(2)
    for sx, sz, ry in ((-1, -1, 45), (1, -1, -45), (-1, 1, 135), (1, 1, -135)):
        mx, mz = sx * (a + c) / 2, sz * (a + c) / 2
        cx = mx - sx * (t / 2) / math.sqrt(2)
        cz = mz - sz * (t / 2) / math.sqrt(2)
        hh = h - 0.11
        m.kubus(bone, [cx - L / 2, y0 + 0.05, cz - t / 2], [L, hh, t], kuas, rot=[0, ry, 0],
                pivot=[cx, y0 + 0.05 + hh / 2, cz])


# ===========================================================================
# Kepala, wajah & rambut (dipakai kedua model)
# ===========================================================================
def kepala(m, warna_bando, bando_kilap):
    R = RAMBUT
    wajah = kuas_lapis(kuas_wajah(KULIT, R[0], mulut="tawa", pipi=False, hidung=False, y_mulut=0.862),
                       kuas_wajah_detail(KULIT))
    m.kubus("head", [-4.5, 23.5, -4.5], [9, 9, 9], kuas_per_sisi(
        depan=wajah, bawah=kuas_kulit2(KULIT), lain=k_rambut_padat(0.8, None)))
    pasang_mata(m, KULIT, IRIS, R[0], gaya="putri", lebar=2.5, tinggi=2.6, jarak=0.6, y_bawah=25.3)

    # --- mahkota: kubah oktagonal bertingkat -----------------------------------
    padat = k_rambut_padat(1.0, 0.35)
    poni_dasar = kuas_helai(R, "gelombang", 0.35, kilau=0.25)
    lapis_oktagon(m, "head", 27.4, 4.8, 4.95, 4.2, padat, kuas_depan=poni_dasar, y0_depan=28.9)
    lapis_oktagon(m, "head", 32.2, 0.7, 4.4, 3.6, k_rambut_padat(1.05, 0.5))
    lapis_oktagon(m, "head", 32.9, 0.52, 3.3, 2.5, k_rambut_padat(1.1, 0.5))
    # bevel atas (menutup pangkal poni & tirai samping, membulatkan siluet)
    bevel = kuas_per_sisi(atas=kuas_helai(R, None, kilau=0.55, akar=0), lain=k_rambut_padat(0.9, None))
    batang_zy(m, "head", (-5.4, 31.6), (-4.25, 32.95), -4.35, 8.7, 0.5, bevel, perpanjang=0.1)
    batang_xy(m, "head", (-5.5, 31.35), (-4.35, 32.95), -4.1, 6.8, 0.5, bevel, cermin=True, perpanjang=0.1)

    # --- poni: 9 helai runcing dengan panjang bervariasi -----------------------
    poni = [  # (x tengah, lebar, y ujung, z)
        (-4.15, 1.4, 27.9, -5.15), (-3.2, 1.5, 27.6, -5.33), (-2.15, 1.5, 28.0, -5.18),
        (-1.15, 1.5, 27.45, -5.36), (0.0, 1.5, 27.75, -5.17), (1.1, 1.5, 27.35, -5.36),
        (2.15, 1.5, 28.05, -5.18), (3.2, 1.5, 27.55, -5.33), (4.15, 1.4, 27.95, -5.15),
    ]
    for i, (x, w, yu, z) in enumerate(poni):
        h = 32.0 - yu
        rz = -x * 2.6
        helai(m, "head", x, 32.0, z, w, h, 0.45, k_helai("runcing", 0.45 + 0.1 * (i % 2), kilau=0.3),
              rot=[2, 0, rz])
    # helai pembingkai pipi (di depan sudut wajah, tidak menutupi mata)
    helai(m, "head", -4.2, 31.2, -4.88, 1.3, 7.2, 0.4, k_helai("runcing", 0.5), rot=[0, 0, -3], cermin=True)

    # --- tirai samping (menutupi telinga, berakhir di atas bahu) ----------------
    for x, z, w, h, rz, dry in ((-5.2, -3.55, 1.9, 7.4, 4, 8), (-5.35, -1.85, 1.9, 7.9, 7, -5),
                                (-5.15, -0.1, 1.9, 7.6, 6, 6), (-5.3, 1.5, 1.8, 7.0, 8, -7)):
        helai(m, "head", x, 31.4, z, w, h, 0.5, k_helai("runcing", 0.55), rot=[0, 90 + dry, rz], cermin=True)
    # helai luar pendek di sisi (lapisan, menambah volume)
    for z, h, rz in ((-2.7, 4.6, 12), (0.8, 5.0, 13)):
        helai(m, "head", -5.6, 31.3, z, 1.6, h, 0.45, k_helai("runcing", 0.45), rot=[0, 90, rz], cermin=True)

    # --- jumbai depan bahu (rambut_kanan / rambut_kiri), berombak -------------
    helai_s(m, "rambut_kanan", -4.05, 30.0, -2.75, 1.7, 8.6, 6.4, 0.55, -2, 7,
            k_helai(None, kilau=0.25), k_helai("ikal", 0.5, kilau=None), rx=-4, cermin=True)
    helai_s(m, "rambut_kanan", -4.85, 29.6, -2.2, 1.4, 7.8, 5.0, 0.5, 4, -5,
            k_helai(None, kilau=0.3, gelap=0.9), k_helai("runcing", 0.5, kilau=None, gelap=0.9), rx=-3, cermin=True)
    helai_s(m, "rambut_kanan", -3.35, 29.8, -3.05, 1.2, 7.2, 3.8, 0.45, -5, 6,
            k_helai(None, kilau=0.3, gelap=1.05), k_helai("runcing", 0.45, kilau=None, gelap=1.05), rx=-5,
            cermin=True)

    # --- rambut belakang atas (rambut_belakang) --------------------------------
    m.kubus("rambut_belakang", [-4.7, 20.6, 4.2], [9.4, 11.2, 0.9], k_rambut_padat(0.7, None))
    for x, z, yu, dry in ((-3.4, 5.45, 20.7, 6), (-1.7, 5.25, 20.2, -4), (0.0, 5.5, 20.9, 0),
                          (1.7, 5.25, 20.3, 4), (3.4, 5.45, 20.6, -6)):
        helai(m, "rambut_belakang", x, 31.9, z, 2.0, 31.9 - yu + 1.8, 0.55, k_helai("runcing", 0.84, kilau=0.12),
              rot=[-3, 180 + dry, x * 1.3])
    # lapisan luar pendek (rambut berlapis, mengembang)
    for x, yu, dry in ((-2.6, 24.6, 5), (-0.85, 23.8, -3), (0.9, 24.2, 3), (2.6, 24.9, -5)):
        helai(m, "rambut_belakang", x, 31.95, 5.85, 1.8, 31.95 - yu, 0.5, k_helai("runcing", 0.5, kilau=0.12),
              rot=[-3, 180 + dry, x * 1.6])
    helai(m, "rambut_belakang", -4.8, 31.6, 4.8, 2.0, 12.6, 0.5, k_helai("runcing", 0.84, kilau=0.12),
          rot=[-3, 135, 4], cermin=True)
    for z, yu, rz, dry in ((2.4, 20.8, 6, -6), (3.75, 20.4, 5, 5)):
        helai(m, "rambut_belakang", -5.25, 31.4, z, 1.8, 31.4 - yu + 1.6, 0.5, k_helai("runcing", 0.82, kilau=0.12),
              rot=[0, 90 + dry, rz], cermin=True)
    batang_zy(m, "rambut_belakang", (6.1, 31.75), (4.3, 32.95), -4.35, 8.7, 0.5, bevel, perpanjang=0.1)

    # --- rambut belakang bawah (rambut_belakang2): helai berombak S ------------
    m.kubus("rambut_belakang2", [-5.0, 13.4, 4.3], [10.0, 8.0, 0.9], k_rambut_padat(0.65, None))
    bawah = [  # (x, z, h1, h2, rz1, rz2)
        (-4.3, 5.05, 4.6, 4.9, 9, -6), (-2.9, 4.85, 4.8, 4.6, 6, -5), (-1.45, 5.1, 4.6, 5.0, 3, -6),
        (0.0, 4.85, 4.9, 4.4, -2, 4), (1.45, 5.1, 4.6, 5.1, -3, 6), (2.9, 4.85, 4.8, 4.5, -6, 5),
        (4.3, 5.05, 4.6, 4.9, -9, 6),
    ]
    for i, (x, z, h1, h2, r1, r2) in enumerate(bawah):
        pola = "ikal" if i % 2 else "runcing"
        helai_s(m, "rambut_belakang2", x, 21.8, z, 2.0, h1, h2, 0.55, -r1, -r2,
                k_helai(None, kilau=0.1), k_helai(pola, 0.5, kilau=None, gelombang=0.12), ry=180, rx=-5)
    helai_s(m, "rambut_belakang2", -4.7, 21.6, 4.6, 2.0, 4.8, 4.6, 0.5, 4, -7,
            k_helai(None, kilau=0.1), k_helai("runcing", 0.5, kilau=None, gelombang=0.12), ry=135, rx=-3, cermin=True)
    for x, z, h1, h2, r1, r2 in ((-5.0, 2.5, 4.4, 4.0, 9, -4), (-5.18, 3.85, 4.6, 4.4, 7, -6)):
        helai_s(m, "rambut_belakang2", x, 21.4, z, 1.8, h1, h2, 0.5, r1, r2,
                k_helai(None, kilau=0.1), k_helai("ikal", 0.5, kilau=None, gelombang=0.12), ry=90, cermin=True)

    # --- bando: melengkung di atas kepala dari telinga ke telinga --------------
    kb = kuas_per_sisi(atas=kuas_pita(warna_bando, bando_kilap), lain=kuas_pita(warna_bando, bando_kilap, False))
    z0, dz = -1.75, 0.95
    titik_b = [(-5.75, 28.6), (-5.75, 31.25), (-4.6, 33.05), (-3.3, 33.6)]
    for i, (a, b) in enumerate(zip(titik_b, titik_b[1:])):
        e = 0.06 * (i % 2)  # selang-seling kedalaman: sambungan tanpa z-fighting
        batang_xy(m, "head", a, b, z0 - e, dz + 2 * e, 0.36, kb, cermin=True, perpanjang=0.12)
    batang_xy(m, "head", (-3.4, 33.6), (3.4, 33.6), z0 - 0.06, dz + 0.12, 0.36, kb)


# ===========================================================================
# Tubuh bersama
# ===========================================================================
def leher(m):
    m.kubus("body", [-1.0, 22.6, -1.0], [2.0, 1.2, 2.0], kuas_kulit2(KULIT, bayang_atas=2))


def lengan(m, kain, kain_g, manset, manset_g, kancing=None, renda=False, puff=True, manset_rajut=False):
    """Lengan putri (lebar 3, x -7..-4) dengan bahu menggembung, manset, tangan + ibu jari."""
    k_lengan = kuas_per_sisi(depan=kuas_kain2(kain, kain_g), belakang=kuas_kain2(kain, kain_g),
                             kanan=kuas_kain2(kain, kain_g), kiri=kuas_kain2(ubah(rgb(kain), 0.93), kain_g),
                             lain=kuas_polos(ubah(rgb(kain), 0.9)))
    m.cermin("rightArm", [-6.9, 17.0, -1.4], [2.8, 5.7, 2.8], k_lengan)
    # bahu menggembung (2 tingkat agar membulat)
    if puff:
        m.cermin("rightArm", [-7.2, 19.9, -1.68], [3.3, 3.0, 3.36], kuas_per_sisi(
            atas=kuas_polos(kain, 0.02), lain=kuas_kain2(kain, kain_g, lipatan=0.12, tepi="b")))
        m.cermin("rightArm", [-6.95, 22.9, -1.43], [2.8, 0.38, 2.86], kuas_polos(ubah(rgb(kain), 1.04), 0.02))
    else:
        m.cermin("rightArm", [-6.98, 21.6, -1.48], [2.96, 1.5, 2.96], kuas_per_sisi(
            atas=kuas_polos(kain, 0.02), lain=kuas_kain2(kain, kain_g, lipatan=0.05, tepi="b", kuat_tepi=0.3)))
    # lengan bawah
    m.cermin("rightForearm", [-6.85, 13.05, -1.35], [2.7, 4.05, 2.7], k_lengan)
    # manset
    k_manset = kuas_per_sisi(depan=kuas_kerah(manset, manset_g, "t", inset=1),
                             belakang=kuas_kerah(manset, manset_g, "t", inset=1),
                             kanan=kuas_kerah(manset, manset_g, "t", inset=1),
                             kiri=kuas_kerah(manset, manset_g, "t", inset=1),
                             lain=kuas_polos(ubah(rgb(manset), 0.9)))
    if manset_rajut:
        k_manset = kuas_per_sisi(lain=kuas_rajut(manset, manset_g), atas=kuas_polos(manset_g), bawah=kuas_polos(manset_g))
    m.cermin("rightForearm", [-7.05, 12.1, -1.55], [3.1, 1.15, 3.1], k_manset)
    if renda:
        m.cermin("rightForearm", [-7.15, 11.65, -1.65], [3.3, 0.5, 3.3],
                 kuas_per_sisi(atas=kuas_kosong(), bawah=kuas_kosong(), lain=kuas_renda(RENDA)))
    if kancing:
        m.cermin("rightForearm", [-4.0, 12.4, -0.35], [0.15, 0.5, 0.5], kuas_polos(kancing))
    # tangan
    m.cermin("rightForearm", [-6.6, 10.75, -1.05], [2.2, 1.45, 2.1], kuas_per_sisi(
        atas=kuas_kulit(KULIT), lain=kuas_kulit2(KULIT, bayang_atas=1)))
    m.cermin("rightForearm", [-6.5, 10.15, -0.95], [1.95, 0.65, 1.85], kuas_tangan(KULIT))
    m.cermin("rightForearm", [-4.95, 10.75, -1.33], [0.63, 1.15, 0.62], kuas_kulit2(KULIT),
             rot=[0, 0, -8], pivot=[-4.6, 11.9, -1.0])


def rok_lipit(m, warna, gelap, y_atas, y_hem, a0, b0, a1, b1, n=20, tebal=0.36, jahitan=None):
    """Rok lipit: n panel menyebar (flare) mengelilingi elips; panel dibagi ke tulang
    rok_depan / rok_kiri / rok_belakang / rok_kanan."""
    import inti as _i
    perim1 = 2 * math.pi * math.sqrt((a1 * a1 + b1 * b1) / 2)
    lebar = perim1 / n * 1.18
    k_luar = kuas_lipit2(warna, gelap, jahitan=jahitan)
    k_dalam = kuas_polos(ubah(rgb(gelap), 0.8), 0.02, 0.1)
    k = kuas_per_sisi(depan=k_luar, belakang=k_dalam, kanan=kuas_polos(gelap, 0.02), kiri=kuas_polos(gelap, 0.02),
                      atas=kuas_polos(gelap, 0.02), bawah=kuas_polos(ubah(rgb(gelap), 0.85), 0.02))
    for i in range(n):
        a = i * 360.0 / n
        ar = math.radians(a)
        dalam = 0.88 if i % 2 else 1.0  # lipatan berselang masuk-keluar
        tx, tz = a0 * math.sin(ar) * dalam, -b0 * math.cos(ar) * dalam
        hx, hz = a1 * math.sin(ar) * (0.97 if i % 2 else 1.0), -b1 * math.cos(ar) * (0.97 if i % 2 else 1.0)
        d = math.hypot(hx - tx, hz - tz)
        H = y_atas - y_hem
        L = math.hypot(d, H)
        phi = math.degrees(math.atan2(d, H))
        an = math.degrees(math.atan2(hx - tx, -(hz - tz))) if d > 1e-6 else a
        aa = a % 360
        if aa >= 315 or aa < 45:
            bone = "rok_depan"
        elif aa < 135:
            bone = "rok_kiri"
        elif aa < 225:
            bone = "rok_belakang"
        else:
            bone = "rok_kanan"
        t = tebal
        m.kubus(bone, [tx - lebar / 2, y_atas - L, tz - t / 2], [lebar, L, t], k,
                rot=[-phi, -an, 0], pivot=[tx, y_atas, tz])


# ===========================================================================
# Model 1: seragam Kikyo
# ===========================================================================
def badan_seragam(m):
    leher(m)
    kain = kuas_per_sisi(depan=kuas_kain2(PINK, PINK_G, lipatan=0.04), belakang=kuas_kain2(PINK, PINK_G, lipatan=0.04),
                         kanan=kuas_kain2(ubah(rgb(PINK), 0.92), PINK_G), kiri=kuas_kain2(ubah(rgb(PINK), 0.92), PINK_G),
                         lain=kuas_polos(ubah(rgb(PINK), 0.9)))
    # badan meruncing: dada - pinggang - pinggul
    m.kubus("body", [-3.5, 18.6, -2.0], [7.0, 4.4, 4.0], kain)
    m.kubus("body", [-2.85, 19.05, -2.4], [5.7, 2.65, 0.5], kuas_per_sisi(
        depan=kuas_kain2(PINK, PINK_G, tepi="b", lipatan=0.03), lain=kuas_polos(ubah(rgb(PINK), 0.88))))
    pinggang = dict(kain)
    pinggang["depan"] = kuas_lapis(kuas_kain2(PINK, PINK_G, lipatan=0.04), kuas_jahit_v(PINK_G, (0.22, 0.78)))
    pinggang["belakang"] = kuas_lapis(kuas_kain2(PINK, PINK_G, lipatan=0.04), kuas_jahit_v(PINK_G, (0.25, 0.75)))
    m.kubus("body", [-3.05, 14.4, -1.8], [6.1, 4.3, 3.6], pinggang)
    m.kubus("body", [-3.3, 12.0, -1.9], [6.6, 2.2, 3.8], kain)
    # sabuk pinggang
    m.kubus("body", [-3.4, 13.7, -2.05], [6.8, 0.8, 4.1], kuas_per_sisi(
        depan=kuas_kain2(ubah(rgb(PINK), 0.88), PINK_G, tepi="tb", kuat_tepi=0.7),
        lain=kuas_kain2(ubah(rgb(PINK), 0.85), PINK_G, tepi="tb", kuat_tepi=0.7)))
    # kancing gelap di depan
    for y in (15.0, 15.95):
        m.kubus("body", [-0.27, y, -2.02], [0.54, 0.54, 0.25], kuas_lapis(kuas_polos(GARIS), kuas_rect("#7b6672", 0.1, 0.1, 0.45, 0.45)))
    # kerah pelaut putih: di bahu, flap persegi di punggung (jubah), V di depan
    m.cermin("body", [-3.75, 22.95, -2.25], [2.6, 0.42, 4.78], kuas_per_sisi(
        atas=kuas_kerah(PUTIH, GARIS, "l", inset=2), lain=kuas_kerah(PUTIH, GARIS, "", inset=1)))
    m.kubus("jubah", [-3.75, 18.1, 2.1], [7.5, 5.25, 0.35], kuas_per_sisi(
        belakang=kuas_kerah(PUTIH, GARIS, "lrb", inset=2), depan=kuas_polos(ubah(rgb(PUTIH), 0.9)),
        lain=kuas_polos(ubah(rgb(PUTIH), 0.92))))
    lapel = kuas_per_sisi(depan=kuas_kerah(PUTIH, GARIS, "b", inset=1), lain=kuas_polos(ubah(rgb(PUTIH), 0.9)))
    batang_xy(m, "body", (-2.75, 23.05), (-0.25, 19.6), -2.7, 0.32, 1.25, lapel, perpanjang=0.2)
    batang_xy(m, "body", (2.75, 23.05), (0.25, 19.6), -2.77, 0.39, 1.25, lapel, perpanjang=0.2)
    m.kubus("body", [-1.1, 19.45, -2.47], [2.2, 3.3, 0.1], kuas_kain2(PINK, PINK_G, tepi=""))  # panel V
    # pita hitam: simpul + 2 lingkar + 2 ekor (ekor di tulang pita)
    pita = kuas_pita(HITAM, "#4b4656")
    m.kubus("body", [-0.55, 19.25, -3.05], [1.1, 1.0, 0.6], pita)
    m.cermin("body", [-2.05, 19.0, -2.88], [1.6, 1.5, 0.42], pita, rot=[0, 0, 12], pivot=[-0.5, 19.75, -2.67])
    for sx in (-1, 1):
        x0 = -0.95 if sx < 0 else 0.2
        m.kubus("pita", [x0, 16.35, -2.88], [0.75, 3.0, 0.24], kuas_lapis(kuas_pita(HITAM, "#4b4656"),
                lambda img, X, Y, W, H, rnd: _potong_ujung(img, X, Y, W, H, "takik", 0.82, None)),
                rot=[-4, 0, 7 * -sx], pivot=[x0 + 0.375, 19.35, -2.76])

    lengan(m, PINK, PINK_G, PUTIH, GARIS, kancing=GARIS)

    # kaki: stoking hitam + loafer cokelat
    st = kuas_per_sisi(lain=kuas_stoking(STOKING), atas=kuas_polos(STOKING), bawah=kuas_polos(STOKING))
    m.cermin("rightLeg", [-3.35, 6.0, -1.45], [2.9, 6.1, 2.9], st)
    m.cermin("rightShin", [-3.3, 4.9, -1.4], [2.8, 1.25, 2.8], kuas_per_sisi(
        depan=kuas_stoking(STOKING, kilap_lutut=True), lain=kuas_stoking(STOKING)))
    m.cermin("rightShin", [-3.25, 1.4, -1.33], [2.7, 3.55, 2.66], st)
    m.cermin("rightShin", [-3.08, 2.4, 0.4], [2.36, 2.2, 1.12], st)  # betis
    sepatu(m, LOAFER, ubah(rgb(LOAFER), 0.55), loafer=True)

    rok_lipit(m, PINK, PINK_G, 13.75, 4.5, 3.45, 2.1, 5.3, 3.95, n=20, jahitan=ubah(rgb(PINK_G), 0.95))


def sepatu(m, warna, sol, loafer=True, tali=None):
    ks = kuas_per_sisi(depan=kuas_kulit_sepatu(warna), belakang=kuas_kulit_sepatu(warna), kanan=kuas_kulit_sepatu(warna),
                       kiri=kuas_kulit_sepatu(warna), atas=kuas_polos(ubah(rgb(warna), 0.6)), bawah=kuas_polos(sol))
    m.cermin("rightShin", [-3.5, 0.0, -2.35], [3.2, 0.45, 3.95], kuas_polos(sol, 0.03, tepi=ubah(rgb(sol), 0.7)))
    m.cermin("rightShin", [-3.45, -0.06, 0.6], [3.1, 0.8, 1.06], kuas_polos(sol, 0.03))  # hak
    m.cermin("rightShin", [-3.38, 0.45, -2.2], [2.96, 1.3, 3.6], ks)
    m.cermin("rightShin", [-3.18, 0.45, -2.5], [2.56, 1.0, 0.4], kuas_per_sisi(
        atas=kuas_kulit_sepatu(warna), lain=kuas_kulit_sepatu(warna)))  # ujung membulat
    if loafer:
        m.cermin("rightShin", [-3.45, 1.4, -1.85], [3.1, 0.45, 0.95], kuas_per_sisi(
            atas=kuas_lapis(kuas_polos(ubah(rgb(warna), 0.75)), kuas_rect("#1f140f", 0.3, 0.3, 0.7, 0.7)),
            lain=kuas_polos(ubah(rgb(warna), 0.75))))
    if tali:
        m.cermin("rightShin", [-3.45, 1.55, -1.25], [3.1, 0.32, 0.6], kuas_polos(tali))
        m.cermin("rightShin", [-0.4, 1.4, -1.2], [0.12, 0.5, 0.5], kuas_polos("#f2e6d0"))


def kuas_rect(warna, x0, y0, x1, y1):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        isi_rect(img, X + int(W * x0), Y + int(H * y0), max(1, int(W * x1) - int(W * x0)),
                 max(1, int(H * y1) - int(H * y0)), c)
    return f


# ===========================================================================
# Model 2: kasual
# ===========================================================================
def badan_kasual(m):
    leher(m)
    kain = kuas_per_sisi(depan=kuas_kain2(KREM, KREM_G, lipatan=0.05), belakang=kuas_kain2(KREM, KREM_G, lipatan=0.05),
                         kanan=kuas_kain2(ubah(rgb(KREM), 0.94), KREM_G), kiri=kuas_kain2(ubah(rgb(KREM), 0.94), KREM_G),
                         lain=kuas_polos(ubah(rgb(KREM), 0.9)))
    m.kubus("body", [-3.5, 18.6, -2.0], [7.0, 4.4, 4.0], kain)
    m.kubus("body", [-2.85, 19.05, -2.4], [5.7, 2.65, 0.5], kuas_per_sisi(
        depan=kuas_kain2(KREM, KREM_G, tepi="b", lipatan=0.04), lain=kuas_polos(ubah(rgb(KREM), 0.9))))
    m.kubus("body", [-3.05, 15.2, -1.8], [6.1, 3.5, 3.6], kain)
    m.kubus("body", [-3.3, 12.0, -1.9], [6.6, 3.3, 3.8], kain)
    # garis kancing mutiara di depan
    for y in (16.6, 17.8, 20.9):
        m.kubus("body", [-0.25, y, -2.02 if y < 19 else -2.5], [0.5, 0.5, 0.25],
                kuas_lapis(kuas_polos("#fffaf2"), kuas_rect("#d8cbb8", 0.5, 0.5, 1.0, 1.0)))
    m.kubus("body", [-0.08, 15.3, -1.86], [0.16, 3.3, 0.08], kuas_polos(KREM_G))  # plaket
    # sabuk rok tinggi (lavender) + pita kecil
    m.kubus("body", [-3.4, 14.8, -2.05], [6.8, 1.0, 4.1], kuas_per_sisi(
        depan=kuas_kain2(LAVENDER_G, ubah(rgb(LAVENDER_G), 0.75), tepi="tb", kuat_tepi=0.6),
        lain=kuas_kain2(ubah(rgb(LAVENDER_G), 0.95), ubah(rgb(LAVENDER_G), 0.75), tepi="tb", kuat_tepi=0.6)))
    # kerah renda putih (bulat, tepi bergerigi) di depan, bahu & belakang
    renda = kuas_per_sisi(depan=kuas_renda(RENDA), belakang=kuas_renda(RENDA), atas=kuas_polos(RENDA),
                          lain=kuas_polos(ubah(rgb(RENDA), 0.92)))
    m.cermin("body", [-3.35, 21.55, -2.95], [3.05, 1.55, 0.3], renda, rot=[0, 0, -10], pivot=[-0.3, 23.1, -2.8])
    m.cermin("body", [-3.65, 23.2, -2.3], [2.5, 0.35, 4.9], kuas_polos(RENDA, 0.02))
    m.kubus("body", [-3.55, 21.6, 2.3], [7.1, 1.5, 0.3], kuas_per_sisi(
        belakang=kuas_renda(RENDA), lain=kuas_polos(ubah(rgb(RENDA), 0.92))))
    # pita kecil merah muda di kerah
    pita = kuas_pita(BANDO_PINK, "#f6c3cf")
    m.kubus("body", [-0.42, 21.55, -3.4], [0.84, 0.8, 0.45], pita)
    m.cermin("body", [-1.45, 21.4, -3.3], [1.1, 1.1, 0.35], pita, rot=[0, 0, 14], pivot=[-0.35, 21.95, -3.12])
    for sx in (-1, 1):
        x0 = -0.62 if sx < 0 else 0.07
        m.kubus("pita", [x0, 19.85, -3.27], [0.55, 1.8, 0.2], kuas_lapis(pita,
                lambda img, X, Y, W, H, rnd: _potong_ujung(img, X, Y, W, H, "takik", 0.8, None)),
                rot=[-6, 0, 9 * -sx], pivot=[x0 + 0.275, 21.65, -3.17])

    # kardigan tipis merah muda pucat (terbuka di depan)
    kd = kuas_per_sisi(depan=kuas_kardigan_depan(KARDIGAN, KARDIGAN_G, kancing="#fff7f0"),
                       belakang=kuas_lapis(kuas_kain2(KARDIGAN, KARDIGAN_G, lipatan=0.05),
                                           kuas_strip_h(KARDIGAN_G, -3, 1), kuas_strip_h(KARDIGAN_G, -1, 1)),
                       kanan=kuas_kain2(ubah(rgb(KARDIGAN), 0.94), KARDIGAN_G),
                       kiri=kuas_kain2(ubah(rgb(KARDIGAN), 0.94), KARDIGAN_G),
                       atas=kuas_polos(KARDIGAN, 0.02), bawah=kuas_kosong())
    m.kubus("body", [-3.68, 15.55, -2.6], [7.36, 7.6, 4.84], kd)
    lengan(m, KARDIGAN, KARDIGAN_G, KARDIGAN, KARDIGAN_G, renda=True, puff=False, manset_rajut=True)

    # kaki: kulit + kaus kaki putih berenda + sepatu beige bertali (Mary Jane)
    kl = kuas_per_sisi(lain=kuas_kulit2(KULIT), atas=kuas_kulit(KULIT), bawah=kuas_kulit(KULIT))
    m.cermin("rightLeg", [-3.35, 6.0, -1.45], [2.9, 6.1, 2.9], kl)
    m.cermin("rightShin", [-3.3, 4.9, -1.4], [2.8, 1.25, 2.8], kl)
    m.cermin("rightShin", [-3.25, 2.6, -1.33], [2.7, 2.4, 2.66], kl)
    m.cermin("rightShin", [-3.08, 2.6, 0.4], [2.36, 2.0, 1.12], kl)
    m.cermin("rightShin", [-3.32, 0.9, -1.36], [2.84, 1.75, 2.82], kuas_per_sisi(
        lain=kuas_kaus_kaki("#fbfbf8"), atas=kuas_polos("#fbfbf8")))
    m.cermin("rightShin", [-3.45, 2.45, -1.55], [3.1, 0.5, 3.2], kuas_per_sisi(
        atas=kuas_kosong(), bawah=kuas_kosong(), lain=kuas_renda(RENDA)))
    sepatu(m, SEPATU_BEIGE, "#8a6f58", loafer=False, tali=ubah(rgb(SEPATU_BEIGE), 0.82))

    rok_lipit(m, LAVENDER, LAVENDER_G, 15.0, 2.9, 3.45, 2.1, 5.6, 4.3, n=20,
              jahitan=campur(LAVENDER, "#ffffff", 0.35))


# ===========================================================================
# buat()
# ===========================================================================
def buat():
    m1 = Model("kaoruko", "Kaoruko Waguri", "Kaoruko Waguri (Seragam Kikyo)", skala=0.84,
               deskripsi="Kaoruko Waguri, gadis mungil yang ceria & suka kue. Rambut panjang bergelombang hitam "
                         "keunguan dengan bando hitam, seragam pelaut merah muda Kikyo Private Academy.")
    kepala(m1, HITAM, "#5a5566")
    badan_seragam(m1)

    m2 = Model("kaoruko_kasual", "Kaoruko Waguri (Casual)", "Kaoruko Waguri (Kasual)", skala=0.84,
               deskripsi="Kaoruko Waguri bergaya kencan: bando merah muda, blus krem berkerah renda dengan pita, "
                         "rok panjang lavender berlipit, kaus kaki putih & sepatu beige.")
    kepala(m2, BANDO_PINK, "#f8c6d2")
    badan_kasual(m2)
    return [m1, m2]
