"""Generator addon "Waguri YSM" untuk Minecraft Bedrock.

Konsep: meniru mod Java *Yes Steve Model* (YSM), yaitu mengganti tubuh pemain
dengan model 3D bergaya anime yang bisa dipilih tiap pemain. Bedrock tidak bisa
memakai mod, jadi addon ini:

  * menimpa entitas pemain (BP player.json) untuk menambah property
    `waguri:model` (model terpilih) dan `waguri:emote` (emote yang diputar);
  * menimpa client entity pemain (RP player.entity.json): bila model > 0,
    render controller skin vanilla dimatikan dan geometri model yang dipilih
    digambar. Semua tulang memakai nama & pivot yang sama dengan skin vanilla
    (root, waist, body, head, rightArm, leftArm, rightLeg, leftLeg, rightItem,
    leftItem) sehingga SEMUA animasi vanilla (jalan, lari, jongkok, berenang,
    tidur, menyerang, memegang item, busur, crossbow, perisai, dll.) tetap jalan;
  * menambah animasi khas YSM: kedip mata, rambut & rok bergoyang, skala tinggi
    badan sesuai karakter, dan emote.

Karakter dari *Kaoru Hana wa Rin to Saku* (Saka Mikami / Kodansha).
Semua tekstur pixel art dibuat prosedural oleh skrip ini.

Jalankan dari folder Waguri:  python3 tools/buat_waguri.py
Butuh paket: pip install pillow
"""

import copy
import json
import math
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VANILLA = os.path.join(os.path.dirname(__file__), "vanilla")
RP = os.path.join(ROOT, "Waguri_RP")
BP = os.path.join(ROOT, "Waguri_BP")
DOCS = os.path.join(ROOT, "docs")

ENGINE = [1, 26, 30]
UUID = {
    "rp_header": "97a61f27-8cac-42ba-8600-7f369f60f5bf",
    "rp_module": "c78b2708-2e10-427f-830d-e4335e67cb12",
    "bp_header": "7da3e9ba-43a4-49e5-ac32-7952beb16419",
    "bp_module": "2f0ce5b9-37e3-4527-9e4b-79eca58d2f9b",
    "bp_script": "f011d4b9-98c4-4ae0-9fd7-120c2df071b5",
}

K = 2  # piksel tekstur per unit model (tekstur HD 2x seperti model YSM)
TEX_UNIT = (128, 128)  # ukuran tekstur dalam unit model -> gambar 256x256

KOSONG = (0, 0, 0, 0)


# ===========================================================================
# Alat dasar
# ===========================================================================
def rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ubah(w, f):
    r, g, b, a = w
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


def campur(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(4))


def tulis_json(data, *bagian):
    path = os.path.join(*bagian)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def tulis_teks(isi, *bagian):
    path = os.path.join(*bagian)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(isi)


def simpan(img, *bagian):
    path = os.path.join(*bagian)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def kotak_uv(u, v, w, h, d):
    """Sisi kubus pada tata letak box-UV (satuan unit)."""
    return {
        "atas": (u + d, v, w, d),
        "bawah": (u + d + w, v, w, d),
        "kanan": (u, v + d, d, h),
        "depan": (u + d, v + d, w, h),
        "kiri": (u + d + w, v + d, d, h),
        "belakang": (u + d + w + d, v + d, w, h),
    }


class Penata:
    """Penempatan UV sederhana (rak)."""

    def __init__(self, lebar, tinggi):
        self.x = self.y = self.t = 0
        self.lebar, self.tinggi = lebar, tinggi

    def tempat(self, fw, fh):
        if self.x + fw > self.lebar:
            self.x, self.y, self.t = 0, self.y + self.t, 0
        u, v = self.x, self.y
        assert v + fh <= self.tinggi, "tekstur penuh"
        self.x += fw
        self.t = max(self.t, fh)
        return u, v


# ===========================================================================
# Kuas: pelukis sisi kubus (koordinat piksel)
# ===========================================================================
def titik(img, x, y, w):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), w)


def polos(warna, derau=0.035, gradasi=0.0):
    """Isi rata + derau halus + gradasi gelap ke bawah."""
    c = rgb(warna) if isinstance(warna, str) else warna

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            g = 1 - gradasi * (y / max(1, H - 1))
            for x in range(W):
                titik(img, X + x, Y + y, ubah(c, g * (1 + rnd.uniform(-derau, derau))))
    return f


def transparan():
    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                titik(img, X + x, Y + y, KOSONG)
    return f


def lapis(*kuas):
    def f(img, X, Y, W, H, rnd):
        for k in kuas:
            k(img, X, Y, W, H, rnd)
    return f


def helai(r):
    """Rambut berhelai vertikal dengan pita kilau anime."""
    c, g, t = rgb(r[0]), rgb(r[1]), rgb(r[2])

    def f(img, X, Y, W, H, rnd):
        kilau = int(H * 0.28)
        for x in range(W):
            gelap = (x // 2 + rnd.randint(0, 1)) % 3 == 0
            for y in range(H):
                w = g if gelap else c
                if abs(y - kilau) <= 1 and (x + y) % 3 != 0:
                    w = t
                titik(img, X + x, Y + y, ubah(w, 1 + rnd.uniform(-0.03, 0.03)))
    return f


def ujung_helai(r, minimal=0.55, gelombang=False):
    """Rambut dengan tepi bawah runcing/bergelombang (sisanya transparan)."""
    dasar = helai(r)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        for x in range(W):
            if gelombang:
                p = H - 1 - int((math.sin(x * 0.9) * 0.5 + 0.5) * H * (1 - minimal))
            else:
                p = H - 1 - (x % 4 in (0, 3)) * int(H * (1 - minimal) * rnd.uniform(0.5, 1))
            for y in range(p + 1, H):
                titik(img, X + x, Y + y, KOSONG)
    return f


def poni(r, panjang=(4, 7), kulit=None):
    """Poni (bangs): helai menjuntai dengan ujung runcing tak rata."""
    dasar = helai(r)

    def f(img, X, Y, W, H, rnd):
        dasar(img, X, Y, W, H, rnd)
        lo, hi = panjang
        for x in range(W):
            p = lo + int((hi - lo) * (0.5 + 0.5 * math.sin(x * 1.3 + 0.7)))
            p = min(H, p + rnd.randint(-1, 0))
            for y in range(p, H):
                titik(img, X + x, Y + y, KOSONG if kulit is None else kulit)
    return f


def garis_h(warna, y0, tebal, dari=0.0, sampai=1.0):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(y0, y0 + tebal):
            for x in range(int(W * dari), int(W * sampai)):
                if 0 <= y < H:
                    titik(img, X + x, Y + y, ubah(c, 1 + rnd.uniform(-0.03, 0.03)))
    return f


def garis_h_bawah(warna, tebal):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H - tebal, H):
            for x in range(W):
                titik(img, X + x, Y + y, ubah(c, 1 + rnd.uniform(-0.03, 0.03)))
    return f


def lipit(warna_gelap, jarak=3):
    """Lipit rok / kain vertikal."""
    c = rgb(warna_gelap)

    def f(img, X, Y, W, H, rnd):
        for x in range(1, W, jarak):
            for y in range(H):
                titik(img, X + x, Y + y, c)
    return f


def kancing(warna, x_rel=0.5, jarak=6, mulai=3, ukuran=2):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        x0 = int(W * x_rel) - ukuran // 2
        for y in range(mulai, H - 2, jarak):
            for dy in range(ukuran):
                for dx in range(ukuran):
                    titik(img, X + x0 + dx, Y + y + dy, c)
    return f


def jalur_v(warna, x0_rel, x1_rel):
    """Strip vertikal (mis. kemeja putih di balik jaket terbuka)."""
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(int(W * x0_rel), int(W * x1_rel)):
                titik(img, X + x, Y + y, ubah(c, 1 + rnd.uniform(-0.03, 0.03)))
    return f


def kerah_pelaut(putih, garis, ke=0.5):
    """Kerah pelaut (sailor collar) berbentuk V di depan."""
    cp, cg = rgb(putih), rgb(garis)

    def f(img, X, Y, W, H, rnd):
        dalam = int(H * ke)
        for y in range(dalam):
            t = y / max(1, dalam)
            kiri = int((W / 2) * t * 0.95)
            for lebar_ in range(3):
                for x in (kiri + lebar_, W - 1 - kiri - lebar_):
                    titik(img, X + x, Y + y, cg if lebar_ == 2 else cp)
    return f


def kotak_px(warna, x0, y0, x1, y1):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(y0, y1):
            for x in range(x0, x1):
                titik(img, X + x, Y + y, c)
    return f


# ---------------------------------------------------------------------------
# Wajah anime
# ---------------------------------------------------------------------------
def wajah(p):
    """Wajah anime 2x. p: dict kulit, rambut, mata, gaya (putri/putra/tajam),
    mulut (senyum/tawa/datar/lebar), pipi (bool), poni (rentang px)."""
    kulit = rgb(p["kulit"])
    bayang = ubah(kulit, 0.9)
    garis_mata = rgb("#2a1c22")
    iris = rgb(p["mata"])
    iris_gelap = ubah(iris, 0.55)
    iris_terang = ubah(iris, 1.35)
    putih = rgb("#ffffff")
    mulut_c = rgb("#b5545e")
    lidah = rgb("#e8909a")
    pipi = rgb("#f3a6ae")
    alis = ubah(rgb(p["rambut"][0]), 0.8)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                titik(img, X + x, Y + y, ubah(kulit, 1 + rnd.uniform(-0.015, 0.015)))
        # garis rambut di dahi (terlihat bila poni pendek)
        rambut_c = rgb(p["rambut"][0])
        for x in range(W):
            for y in range(3 + (x % 3 == 1)):
                titik(img, X + x, Y + y, ubah(rambut_c, 1 + rnd.uniform(-0.05, 0.05)))
        # bayangan di bawah poni
        for x in range(W):
            titik(img, X + x, Y + 7, bayang)
        cx = W // 2
        gaya = p.get("gaya", "putri")
        tinggi_mata = 5 if gaya == "putri" else 4
        ey = 9 if gaya == "putri" else 10
        for sisi in (-1, 1):
            # mata: lebar 4 px, berjarak 2 px dari tengah
            x0 = cx + 1 if sisi == 1 else cx - 5
            for i in range(4):
                for j in range(tinggi_mata):
                    t = j / max(1, tinggi_mata - 1)
                    w = campur(iris_gelap, iris_terang, t)
                    titik(img, X + x0 + i, Y + ey + j, w)
            # bulu mata atas (lebih panjang ke luar)
            for i in range(-1 if sisi == -1 else 0, 5 if sisi == 1 else 4):
                titik(img, X + x0 + i, Y + ey - 1, garis_mata)
            if gaya == "putri":
                luar = x0 - 1 if sisi == -1 else x0 + 4
                titik(img, X + luar, Y + ey, garis_mata)
            if gaya == "tajam":  # mata tajam: kelopak atas menurun ke dalam
                dalam = x0 + 3 if sisi == -1 else x0
                titik(img, X + dalam, Y + ey, garis_mata)
            # pupil & kilau
            titik(img, X + x0 + 1, Y + ey + 1, putih)
            titik(img, X + x0 + 2, Y + ey + tinggi_mata - 2, ubah(iris_gelap, 0.6))
            if gaya == "putri":
                titik(img, X + x0 + 2, Y + ey + 3, ubah(putih, 0.95))
            # alis
            ay = ey - 3
            for i in range(4):
                miring = (i if sisi == -1 else 3 - i) // 2 if gaya == "tajam" else 0
                titik(img, X + x0 + i, Y + ay + miring, alis)
            # pipi merona
            if p.get("pipi"):
                px_ = x0 - 1 if sisi == -1 else x0 + 2
                for i in range(3):
                    titik(img, X + px_ + i, Y + ey + tinggi_mata + 1, pipi)
        # hidung
        titik(img, X + cx, Y + ey + tinggi_mata + 1, bayang)
        # mulut
        my = ey + tinggi_mata + 3
        m = p.get("mulut", "senyum")
        if m == "senyum":
            for x, y in ((-2, 0), (-1, 1), (0, 1), (1, 0)):
                titik(img, X + cx + x, Y + my + y, mulut_c)
        elif m == "tawa":
            for x in range(-2, 2):
                titik(img, X + cx + x, Y + my, mulut_c)
            for x in range(-1, 1):
                titik(img, X + cx + x, Y + my + 1, lidah)
        elif m == "lebar":
            for x in range(-3, 3):
                titik(img, X + cx + x, Y + my, putih)
                titik(img, X + cx + x, Y + my + 1, mulut_c)
            titik(img, X + cx - 4, Y + my - 1, mulut_c)
            titik(img, X + cx + 3, Y + my - 1, mulut_c)
        else:
            for x in range(-1, 1):
                titik(img, X + cx + x, Y + my, ubah(mulut_c, 0.9))
    return f


def kelopak(kulit):
    """Kelopak mata tertutup (dipakai saat berkedip)."""
    c = rgb(kulit)
    g = rgb("#2a1c22")

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                titik(img, X + x, Y + y, c)
        cx = W // 2
        for x0 in (cx - 5, cx + 1):
            for i in range(4):
                titik(img, X + x0 + i, Y + H - 2 - (1 if i in (1, 2) else 0), g)
        for x in range(W):
            if not (cx - 6 <= x <= cx + 5):
                titik(img, X + x, Y, KOSONG)
    return f


def anting(warna):
    c = rgb(warna)

    def f(img, X, Y, W, H, rnd):
        for y in range(H):
            for x in range(W):
                titik(img, X + x, Y + y, ubah(c, 1.2 if (x + y) % 2 else 0.9))
    return f


# ===========================================================================
# Pembangun model
# ===========================================================================
class Model:
    def __init__(self, id_, nama, nama_id, skala, deskripsi):
        self.id = id_
        self.nama = nama
        self.nama_id = nama_id
        self.skala = skala
        self.deskripsi = deskripsi
        self.kubus = []  # dict

    def tambah(self, bone, origin, size, kuas, inflate=0.0, mirror=False, rot=None, pivot=None, datar=False):
        """kuas: satu fungsi (semua sisi) atau dict sisi->fungsi ('_' = bawaan)."""
        self.kubus.append(dict(bone=bone, origin=list(origin), size=list(size), kuas=kuas, inflate=inflate,
                               mirror=mirror, rot=rot, pivot=pivot, datar=datar))

    def cermin(self, bone_kiri, origin, size, kuas, **kw):
        """Tambah kubus di sisi kanan (x negatif) dan cerminannya di kiri."""
        bone_kanan = kw.pop("bone_kanan", None)
        self.tambah(bone_kanan or bone_kiri.replace("left", "right"), origin, size, kuas, **kw)
        o2 = [-(origin[0] + size[0]), origin[1], origin[2]]
        rot = kw.get("rot")
        piv = kw.get("pivot")
        if rot:
            kw["rot"] = [rot[0], -rot[1], -rot[2]]
        if piv:
            kw["pivot"] = [-piv[0], piv[1], piv[2]]
        kw["mirror"] = True
        self.tambah(bone_kiri, o2, size, kuas, **kw)


TULANG = [
    # nama, induk, pivot (sama dengan geometry.humanoid.custom vanilla)
    ("root", None, [0, 0, 0]),
    ("waist", "root", [0, 12, 0]),
    ("body", "waist", [0, 24, 0]),
    ("head", "body", [0, 24, 0]),
    ("rightArm", "body", [-5, 22, 0]),
    ("rightItem", "rightArm", [-5.5, 14, 1]),
    ("leftArm", "body", [5, 22, 0]),
    ("leftItem", "leftArm", [5.5, 14, 1]),
    ("rightLeg", "root", [-1.9, 12, 0]),
    ("leftLeg", "root", [1.9, 12, 0]),
    # tulang tambahan khas YSM
    ("rambut", "head", [0, 31, 4.5]),
    ("rok", "waist", [0, 12, 0]),
    ("kelopak", "head", [0, 26.5, -4.6]),
]


def bangun(model, penata, img, rnd):
    """Tempatkan UV, lukis tekstur, dan kembalikan geometri JSON."""
    tulang = {}
    uv_cache = {}
    for k in model.kubus:
        w, h, d = [max(1, math.ceil(s)) for s in k["size"]]
        kunci = (id(k["kuas"]), w, h, d)
        if k["datar"]:
            u, v = penata.tempat(w, h)
            k["kuas"](img, u * K, v * K, w * K, h * K, rnd)
            cube = {"origin": k["origin"], "size": [k["size"][0], k["size"][1], 0],
                    "uv": {"north": {"uv": [u, v], "uv_size": [w, h]}}}
            k["uv"] = ("datar", u, v)
        else:
            if kunci in uv_cache:  # kubus cermin memakai UV yang sama
                u, v = uv_cache[kunci]
            else:
                u, v = penata.tempat(2 * (w + d), h + d)
                uv_cache[kunci] = (u, v)
                kuas = k["kuas"]
                for nama, (fx, fy, fw, fh) in kotak_uv(u, v, w, h, d).items():
                    f = kuas.get(nama, kuas.get("_")) if isinstance(kuas, dict) else kuas
                    if f is None:
                        f = transparan()
                    f(img, fx * K, fy * K, fw * K, fh * K, rnd)
            cube = {"origin": k["origin"], "size": k["size"], "uv": [u, v]}
            k["uv"] = ("kotak", u, v)
        if k["inflate"]:
            cube["inflate"] = k["inflate"]
        if k["mirror"]:
            cube["mirror"] = True
        if k["rot"]:
            cube["rotation"] = k["rot"]
            cube["pivot"] = k["pivot"]
        tulang.setdefault(k["bone"], []).append(cube)
    bones = []
    for nama, induk, pivot in TULANG:
        b = {"name": nama, "pivot": pivot}
        if induk:
            b["parent"] = induk
        if nama in tulang:
            b["cubes"] = tulang[nama]
        bones.append(b)
    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.waguri.{model.id}",
                "texture_width": TEX_UNIT[0], "texture_height": TEX_UNIT[1],
                "visible_bounds_width": 3, "visible_bounds_height": 3.5,
                "visible_bounds_offset": [0, 1.5, 0],
            },
            "bones": bones,
        }],
    }


# ===========================================================================
# Templat tubuh
# ===========================================================================
def kepala(m, p, rambut_panjang=False):
    """Kepala anime 9x9x9 + poni 3D + kelopak kedip."""
    r = p["rambut"]
    if rambut_panjang:
        kanan = kiri = helai(r)
    else:  # rambut pendek: telinga & pipi samping terlihat di bawah depan
        kanan = lapis(helai(r), kotak_px(p["kulit"], 10, 10, 18, 18), kotak_px(ubah_hex(p["kulit"], 0.9), 11, 12, 13, 15))
        kiri = lapis(helai(r), kotak_px(p["kulit"], 0, 10, 8, 18), kotak_px(ubah_hex(p["kulit"], 0.9), 5, 12, 7, 15))
    m.tambah("head", [-4.5, 23.5, -4.5], [9, 9, 9], {
        "depan": wajah(p),
        "atas": helai(r),
        "belakang": helai(r),
        "kanan": kanan,
        "kiri": kiri,
        "bawah": polos(p["kulit"]),
    })
    # poni 3D di depan dahi
    m.tambah("head", [-4.75, 28.5, -5.0], [9.5, 4, 1], {
        "depan": poni(r, p.get("poni", (4, 7))),
        "belakang": poni(r, p.get("poni", (4, 7))),
        "atas": helai(r), "kanan": helai(r), "kiri": helai(r),
    })
    # kelopak mata (hanya terlihat saat animasi kedip)
    m.tambah("kelopak", [-4.5, 25.0, -4.6], [9, 3, 0], kelopak(p["kulit"]), datar=True)


def ubah_hex(h, f):
    c = ubah(rgb(h), f)
    return "#%02x%02x%02x" % c[:3]


def tubuh_putri(m, p, baju, lengan, kaki):
    """Tubuh ramping (putri): badan 7x11x4, lengan 3x11x3, kaki 3x12x3."""
    m.tambah("body", [-1, 23, -1], [2, 1, 2], polos(p["kulit"]))  # leher
    m.tambah("body", [-3.5, 12, -2], [7, 11, 4], baju)
    m.cermin("leftArm", [-7, 12, -1.5], [3, 11, 3], lengan)
    m.cermin("leftLeg", [-3.4, 0, -1.5], [3, 12, 3], kaki, bone_kanan="rightLeg")


def tubuh_putra(m, p, baju, lengan, kaki):
    """Tubuh pria: badan 8x12x4, lengan 3.5 -> 4x12x4 sedikit ramping, kaki 4x12x4."""
    m.tambah("body", [-1, 23.5, -1], [2, 1, 2], polos(p["kulit"]))
    m.tambah("body", [-4, 12, -2], [8, 12, 4], baju)
    m.cermin("leftArm", [-8, 12, -2], [4, 12, 4], lengan)
    m.cermin("leftLeg", [-3.9, 0, -2], [4, 12, 4], kaki, bone_kanan="rightLeg")


def lengan_baju(warna, kulit, manset=None, panjang_tangan=4):
    """Lengan: kain di atas, (manset), tangan kulit di bawah (piksel)."""
    def f(img, X, Y, W, H, rnd):
        polos(warna, gradasi=0.08)(img, X, Y, W, H, rnd)
        if manset:
            garis_h(manset, H - panjang_tangan - 3, 3)(img, X, Y, W, H, rnd)
        for y in range(H - panjang_tangan, H):
            for x in range(W):
                titik(img, X + x, Y + y, ubah(rgb(kulit), 1 + rnd.uniform(-0.02, 0.02)))
    return {"_": f, "atas": polos(warna), "bawah": polos(kulit)}


def kaki_dengan(atas, bawah, sepatu, tinggi_kaus=0.75, tinggi_sepatu=4):
    """Kaki: bagian atas (kulit/celana), kaus kaki/stoking, sepatu (piksel)."""
    def f(img, X, Y, W, H, rnd):
        batas = int(H * (1 - tinggi_kaus))
        polos(atas)(img, X, Y, W, batas, rnd)
        polos(bawah, gradasi=0.05)(img, X, Y + batas, W, H - batas, rnd)
        polos(sepatu)(img, X, Y + H - tinggi_sepatu, W, tinggi_sepatu, rnd)
        for x in range(W):
            titik(img, X + x, Y + H - tinggi_sepatu, ubah(rgb(sepatu), 1.25))
    return {"_": f, "atas": polos(atas), "bawah": polos(ubah_hex(sepatu, 0.7))}


def rok(m, warna, gelap, panjang=3, lebar_bawah=10):
    """Rok lipit 3 susun mengembang (tulang 'rok' ikut bergoyang)."""
    sisi = lapis(polos(warna, gradasi=0.1), lipit(gelap, 3), garis_h_bawah(gelap, 1))
    kuas = {"_": sisi, "atas": polos(warna), "bawah": polos(gelap)}
    y = 13
    tingkat = [(8, 5), (9, 6), (lebar_bawah, 7)][:panjang]
    for i, (w, d) in enumerate(tingkat):
        y -= 3
        m.tambah("rok", [-w / 2, y, -d / 2], [w, 3, d], kuas, inflate=0.05 * i)


# ===========================================================================
# Karakter
# ===========================================================================
KULIT_PUTRI = "#f8dccb"
KULIT_PUTRA = "#f2cfb6"

# Seragam Kikyo: merah muda pudar, kerah pelaut putih bergaris gelap, pita hitam
KIKYO = {"baju": "#c98f9b", "gelap": "#9f6874", "kerah": "#f7f4f2", "garis": "#4a3a46", "pita": "#1c1a22"}
# Seragam Chidori: gakuran hitam, kancing emas
GAKURAN = {"baju": "#1f2029", "gelap": "#121219", "kancing": "#d9b45a", "kemeja": "#f4f4f2"}


def seragam_kikyo(m, p, kaus="#24212b", sepatu="#4b2f22"):
    k = KIKYO
    baju = {
        "depan": lapis(polos(k["baju"], gradasi=0.08), kerah_pelaut(k["kerah"], k["garis"], 0.55),
                       kancing("#3a2a32", 0.5, 5, 13, 2)),
        "belakang": lapis(polos(k["baju"], gradasi=0.08), kotak_px(k["kerah"], 0, 0, 14, 10),
                          garis_h(k["garis"], 8, 1)),
        "_": polos(k["baju"], gradasi=0.08),
        "atas": polos(k["kerah"]),
    }
    lengan = lengan_baju(k["baju"], p["kulit"], manset=k["kerah"])
    kaki = kaki_dengan(p["kulit"], kaus, sepatu, tinggi_kaus=0.9)
    tubuh_putri(m, p, baju, lengan, kaki)
    # lengan sedikit menggembung (puffy) di bahu
    m.cermin("leftArm", [-7.25, 19.5, -1.75], [3, 3, 3], lapis(polos(k["baju"]), lipit(k["gelap"], 2)), inflate=0.25)
    # pita hitam di dada (kupu-kupu)
    m.tambah("body", [-1.5, 18.5, -2.6], [3, 1, 1], polos(k["pita"]))
    m.cermin("body", [-2.5, 18, -2.5], [1, 2, 1], polos(k["pita"]), bone_kanan="body")
    m.tambah("body", [-0.5, 16, -2.4], [1, 2, 1], polos(k["pita"]))
    # kerah pelaut di punggung (menonjol)
    m.tambah("body", [-3.5, 18, 2.0], [7, 5, 1], {"belakang": lapis(polos(k["kerah"]), garis_h(k["garis"], 8, 1)),
                                                   "_": polos(k["kerah"])}, inflate=0.1)
    rok(m, k["baju"], k["gelap"], 3, 10)


def waguri(seragam=True):
    if seragam:
        m = Model("kaoruko", "Kaoruko Waguri", "Kaoruko Waguri (Seragam Kikyo)", 0.84,
                  "Rambut hitam keunguan bergelombang sepinggul, bando hitam, seragam pelaut merah muda Kikyo.")
    else:
        m = Model("kaoruko_kasual", "Kaoruko Waguri (Casual)", "Kaoruko Waguri (Kasual)", 0.84,
                  "Gaya kencan: blus krem berenda, rok panjang lavender, bando merah muda.")
    p = {"kulit": KULIT_PUTRI, "rambut": ("#2f2338", "#1e1625", "#5a4670"), "mata": "#3a4d8f",
         "gaya": "putri", "mulut": "tawa", "pipi": True, "poni": (5, 8)}
    kepala(m, p, rambut_panjang=True)
    r = p["rambut"]
    # rambut panjang bergelombang sampai pinggul (tulang 'rambut' bergoyang)
    m.tambah("rambut", [-5, 13, 3.5], [10, 19, 2], {"_": ujung_helai(r, 0.8, gelombang=True),
                                                     "atas": helai(r)})
    # jumbai samping menjuntai ke bahu (ikut kepala)
    m.cermin("head", [-5.4, 18, -3.5], [1, 10, 6], ujung_helai(r, 0.7, gelombang=True), bone_kanan="head")
    # bando
    bando = "#1b1820" if seragam else "#e58fa6"
    m.tambah("head", [-4.5, 32.6, -1.0], [9, 1, 2], polos(bando), inflate=0.15)
    m.cermin("head", [-5.25, 27.5, -1.0], [1, 5, 2], polos(bando), bone_kanan="head")
    if seragam:
        seragam_kikyo(m, p)
    else:
        blus = "#f5ead9"
        baju = {"depan": lapis(polos(blus, gradasi=0.06), kerah_pelaut("#ffffff", "#e3cbb5", 0.25),
                               kancing("#c9a27e", 0.5, 5, 10, 2)),
                "_": polos(blus, gradasi=0.06), "atas": polos("#ffffff")}
        lengan = lengan_baju(blus, p["kulit"], manset="#ffffff")
        kaki = kaki_dengan(p["kulit"], "#fbfbfb", "#c8a98a", tinggi_kaus=0.3)
        tubuh_putri(m, p, baju, lengan, kaki)
        m.cermin("leftArm", [-7.25, 19.5, -1.75], [3, 3, 3], polos(blus), inflate=0.25)
        # pita kecil merah muda di kerah
        m.tambah("body", [-1, 21.5, -2.5], [2, 1, 1], polos("#e58fa6"))
        rok(m, "#b9a6d6", "#9583b8", 3, 11)
        # rok panjang: tambahan susun ke 4 sampai betis
        m.tambah("rok", [-5.5, 1, -4], [11, 3, 8], lapis(polos("#b9a6d6", gradasi=0.1), lipit("#9583b8", 3)),
                 inflate=0.15)
    return m


def subaru():
    m = Model("subaru", "Subaru Hoshina", "Subaru Hoshina (Seragam Kikyo)", 0.92,
              "Rambut perak panjang diikat ekor kuda tinggi, poni menutupi mata kanan, mata biru laut.")
    p = {"kulit": "#fae3d6", "rambut": ("#d9dce4", "#a9aebc", "#ffffff"), "mata": "#3fb8c4",
         "gaya": "putri", "mulut": "senyum", "pipi": True, "poni": (4, 7)}
    kepala(m, p, rambut_panjang=True)
    r = p["rambut"]
    # poni panjang menutupi mata kanan (sisi x negatif)
    m.tambah("head", [-4.75, 25.0, -5.2], [4, 4, 1], ujung_helai(r, 0.4))
    # ekor kuda tinggi
    m.tambah("head", [-1, 30, 4.4], [2, 2, 1], polos("#2b4a7a"))  # ikat rambut
    m.tambah("rambut", [-1.75, 16, 4.6], [3.5, 15, 2.5], {"_": ujung_helai(r, 0.6), "atas": helai(r)})
    m.tambah("rambut", [-2.5, 24, 4.4], [5, 7, 2], helai(r), inflate=0.1)
    m.cermin("head", [-5.3, 21, -3], [1, 8, 3], ujung_helai(r, 0.6), bone_kanan="head")
    seragam_kikyo(m, p)
    return m


def rambut_runcing(m, r, banyak, tinggi=3):
    """Rambut jabrik: duri-duri kecil di atas kepala."""
    rnd = random.Random(len(m.id) * 7 + banyak)
    for i in range(banyak):
        x = -4 + (i % 4) * 2.2 + rnd.uniform(-0.4, 0.4)
        z = -4 + (i // 4) * 2.6 + rnd.uniform(-0.3, 0.3)
        ax, az = rnd.uniform(-35, 35), rnd.uniform(-35, 35)
        m.tambah("head", [x, 32.0, z], [2, tinggi, 2], helai(r), rot=[ax, 0, az], pivot=[x + 1, 32.0, z + 1])


def gakuran(m, p, terbuka=False, dalaman=None, celana="#1b1c24", sepatu="#3a2a20"):
    g = GAKURAN
    if terbuka:
        depan = lapis(polos(g["baju"], gradasi=0.06), jalur_v(dalaman or g["kemeja"], 0.32, 0.68),
                      kancing(g["kancing"], 0.22, 6, 4, 2), kancing(g["kancing"], 0.78, 6, 4, 2))
    else:
        depan = lapis(polos(g["baju"], gradasi=0.06), kancing(g["kancing"], 0.5, 5, 3, 2),
                      garis_h(g["gelap"], 0, 2))
    baju = {"depan": depan, "_": polos(g["baju"], gradasi=0.06), "atas": polos(g["gelap"])}
    lengan = lengan_baju(g["baju"], p["kulit"], manset=g["gelap"])
    kaki = kaki_dengan(celana, celana, sepatu, tinggi_kaus=0.2, tinggi_sepatu=4)
    tubuh_putra(m, p, baju, lengan, kaki)
    # kerah tegak gakuran
    m.tambah("body", [-2.5, 23, -2.4], [5, 1, 4.6], polos(g["gelap"]), inflate=0.1)


def rintaro():
    m = Model("rintaro", "Rintaro Tsumugi", "Rintaro Tsumugi (Seragam Chidori)", 1.06,
              "190 cm, rambut pirang jabrik (dicat), tiga anting, gakuran Chidori terbuka.")
    p = {"kulit": KULIT_PUTRA, "rambut": ("#ecc75e", "#c2952f", "#fff1b0"), "mata": "#7a4a2a",
         "gaya": "tajam", "mulut": "datar", "pipi": False, "poni": (3, 6)}
    kepala(m, p)
    rambut_runcing(m, p["rambut"], 8, 3)
    # anting: 1 di telinga kiri, 2 di telinga kanan
    m.tambah("head", [4.5, 25.5, -0.5], [1, 1, 1], anting("#d8d8e0"), inflate=-0.2)
    m.tambah("head", [-5.5, 25.5, -0.5], [1, 1, 1], anting("#d8d8e0"), inflate=-0.2)
    m.tambah("head", [-5.5, 26.6, 0.3], [1, 1, 1], anting("#d8d8e0"), inflate=-0.25)
    gakuran(m, p, terbuka=True)
    return m


def saku():
    m = Model("saku", "Saku Natsusawa", "Saku Natsusawa (Kardigan)", 0.97,
              "Poni hitam panjang sampai pangkal hidung, kemeja putih & kardigan abu-abu, celana hitam.")
    p = {"kulit": "#f6dccb", "rambut": ("#1f1d27", "#121117", "#4a4860"), "mata": "#2b2b38",
         "gaya": "putra", "mulut": "datar", "pipi": False, "poni": (8, 11)}
    kepala(m, p)
    r = p["rambut"]
    m.cermin("head", [-5.2, 24, -3.5], [1, 6, 5], ujung_helai(r, 0.6), bone_kanan="head")
    m.tambah("head", [-4.5, 24.5, 4.0], [9, 7, 1], ujung_helai(r, 0.6))
    kardigan = "#8b8e96"
    baju = {"depan": lapis(polos(kardigan, gradasi=0.06), kerah_pelaut("#f4f4f2", "#d4d4d0", 0.3),
                           kancing("#5b5e66", 0.5, 4, 8, 2)),
            "_": polos(kardigan, gradasi=0.06), "atas": polos("#f4f4f2")}
    lengan = lengan_baju(kardigan, p["kulit"], manset="#f4f4f2")
    kaki = kaki_dengan("#1b1c24", "#1b1c24", "#6b4229", tinggi_kaus=0.2)
    tubuh_putra(m, p, baju, lengan, kaki)
    return m


def usami():
    m = Model("usami", "Shohei Usami", "Shohei Usami (Gakuran + Hoodie)", 0.96,
              "Rambut jahe jabrik, selalu tersenyum, gakuran terbuka di atas hoodie kuning.")
    p = {"kulit": KULIT_PUTRA, "rambut": ("#d4642c", "#a5461d", "#f39a5e"), "mata": "#3a2a24",
         "gaya": "putra", "mulut": "lebar", "pipi": False, "poni": (3, 6)}
    kepala(m, p)
    rambut_runcing(m, p["rambut"], 10, 3)
    gakuran(m, p, terbuka=True, dalaman="#f2c53d")
    # tudung hoodie di punggung
    m.tambah("body", [-3.5, 19.5, 2.0], [7, 4, 2], polos("#e2b22f"), inflate=0.1)
    return m


def ayato():
    m = Model("ayato", "Ayato Yorita", "Ayato Yorita (Seragam Chidori)", 0.90,
              "163 cm, rambut hitam rapi, tenang & ramah, gakuran Chidori dikancing.")
    p = {"kulit": KULIT_PUTRA, "rambut": ("#24222c", "#15141b", "#5a5770"), "mata": "#2a2a33",
         "gaya": "putra", "mulut": "senyum", "pipi": False, "poni": (4, 6)}
    kepala(m, p)
    r = p["rambut"]
    m.tambah("head", [-4.5, 24.5, 4.0], [9, 7, 1], ujung_helai(r, 0.7))
    m.cermin("head", [-5.0, 25, -3.0], [1, 6, 4], ujung_helai(r, 0.7), bone_kanan="head")
    gakuran(m, p, terbuka=False)
    return m


def semua_model():
    return [waguri(True), waguri(False), subaru(), rintaro(), saku(), usami(), ayato()]


# ===========================================================================
# Animasi khas YSM
# ===========================================================================
def ekspresi_skala(models):
    """Molang: skala tinggi badan sesuai karakter (property waguri:model)."""
    e = "1.0"
    for i, m in reversed(list(enumerate(models, start=1))):
        e = f"(q.property('waguri:model') == {i} ? {m.skala} : {e})"
    return e


EMOTE = [
    # id property, kunci, nama tombol
    (1, "lambai", "Melambai"),
    (2, "ojigi", "Membungkuk (ojigi)"),
    (3, "kue", "Makan kue"),
    (4, "senang", "Lompat senang"),
]


def animasi_json(models):
    return {
        "format_version": "1.10.0",
        "animations": {
            "animation.waguri.skala": {
                "loop": True,
                "bones": {"root": {"scale": ekspresi_skala(models)}},
            },
            "animation.waguri.kedip": {
                "loop": True,
                "bones": {"kelopak": {"scale": "math.mod(q.life_time + q.property('waguri:model') * 0.37, 3.6) < 0.13 ? 1 : 0"}},
            },
            "animation.waguri.fisika": {
                "loop": True,
                "bones": {
                    # rambut terdorong ke belakang saat bergerak, sedikit berayun saat diam
                    "rambut": {"rotation": [
                        "math.clamp(q.modified_move_speed * 30, 0, 22) + math.sin(q.life_time * 90) * 2 - math.min(q.target_x_rotation, 0) * 0.3",
                        0,
                        "math.sin(q.life_time * 70) * 1.5",
                    ]},
                    # rok mengikuti ayunan kaki
                    "rok": {"rotation": [
                        "variable.tcos0 * 0.12",
                        0,
                        "math.sin(q.life_time * 110) * 1.2 * q.modified_move_speed",
                    ]},
                    # napas halus saat diam
                    "body": {"scale": [1, "1 + math.sin(q.life_time * 120) * 0.008", 1]},
                },
            },
            "animation.waguri.emote.lambai": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "rightArm": {"rotation": [-160, 0, "math.sin(q.life_time * 540) * 22"]},
                    "head": {"rotation": [0, 0, "math.sin(q.life_time * 270) * 4"]},
                },
            },
            "animation.waguri.emote.ojigi": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "waist": {"rotation": ["math.min(q.anim_time * 160, 40)", 0, 0]},
                    "rightArm": {"rotation": [-10, 0, -8]},
                    "leftArm": {"rotation": [-10, 0, 8]},
                },
            },
            "animation.waguri.emote.kue": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "rightArm": {"rotation": ["-115 + math.sin(q.life_time * 600) * 6", 28, 0]},
                    "leftArm": {"rotation": [-40, -20, 0]},
                    "head": {"rotation": [8, 0, "math.sin(q.life_time * 200) * 5"]},
                },
            },
            "animation.waguri.emote.senang": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "root": {"position": [0, "math.abs(math.sin(q.life_time * 360)) * 2.5", 0]},
                    "rightArm": {"rotation": [0, 0, "130 + math.sin(q.life_time * 720) * 10"]},
                    "leftArm": {"rotation": [0, 0, "-130 - math.sin(q.life_time * 720) * 10"]},
                },
            },
        },
    }


# ===========================================================================
# Pemain (RP & BP) — dibuat dari salinan file vanilla
# ===========================================================================
def player_entity_rp(models):
    with open(os.path.join(VANILLA, "player.entity.json"), encoding="utf-8") as f:
        d = json.load(f)
    desc = d["minecraft:client_entity"]["description"]
    for m in models:
        desc["geometry"][f"waguri_{m.id}"] = f"geometry.waguri.{m.id}"
    for m in models:
        desc["textures"][f"waguri_{m.id}"] = f"textures/entity/waguri/{m.id}"
    desc["animations"].update({
        "waguri.skala": "animation.waguri.skala",
        "waguri.kedip": "animation.waguri.kedip",
        "waguri.fisika": "animation.waguri.fisika",
        **{f"waguri.emote.{k}": f"animation.waguri.emote.{k}" for _i, k, _n in EMOTE},
    })
    aktif = "q.property('waguri:model') > 0"
    desc["scripts"]["animate"] += [
        {"waguri.skala": f"{aktif} && !variable.is_first_person"},
        {"waguri.kedip": aktif},
        {"waguri.fisika": f"{aktif} && !variable.is_first_person"},
    ] + [
        {f"waguri.emote.{k}": f"{aktif} && !variable.is_first_person && q.property('waguri:emote') == {i}"}
        for i, k, _n in EMOTE
    ]
    vanilla_mati = "q.property('waguri:model') == 0"
    rc = []
    for item in desc["render_controllers"]:
        (nama, syarat), = item.items()
        if nama in ("controller.render.player.first_person", "controller.render.player.third_person"):
            syarat = f"({syarat}) && {vanilla_mati}"
        rc.append({nama: syarat})
    rc += [
        {"controller.render.waguri.first_person": f"variable.is_first_person && !query.is_spectator && {aktif}"},
        {"controller.render.waguri.third_person": f"!variable.is_first_person && !variable.map_face_icon && !query.is_spectator && {aktif}"},
    ]
    desc["render_controllers"] = rc
    return d


def render_controller_json(models):
    with open(os.path.join(VANILLA, "player.render_controllers.json"), encoding="utf-8") as f:
        v = json.load(f)["render_controllers"]
    fp_vanilla = v["controller.render.player.first_person"]["part_visibility"]
    # visibilitas tangan orang pertama sama persis dengan vanilla (tanpa sleeve)
    fp = [x for x in fp_vanilla if not any(k.endswith("Sleeve") for k in x)]
    larik = {"Array.model": [f"Geometry.waguri_{m.id}" for m in models]}
    larik_tex = {"Array.kulit": [f"Texture.waguri_{m.id}" for m in models]}
    idx = "math.clamp(q.property('waguri:model') - 1, 0, %d)" % (len(models) - 1)
    geo = f"Array.model[{idx}]"
    tex = f"Array.kulit[{idx}]"
    return {
        "format_version": "1.8.0",
        "render_controllers": {
            "controller.render.waguri.first_person": {
                "arrays": {"geometries": larik, "textures": larik_tex},
                "geometry": geo,
                "materials": [{"*": "Material.default"}],
                "textures": [tex],
                "part_visibility": fp,
            },
            "controller.render.waguri.third_person": {
                "arrays": {"geometries": larik, "textures": larik_tex},
                "geometry": geo,
                "materials": [{"*": "Material.default"}],
                "textures": [tex],
                "part_visibility": [{"*": True}],
            },
        },
    }


def player_bp(models):
    with open(os.path.join(VANILLA, "player.json"), encoding="utf-8") as f:
        d = json.load(f)
    d["minecraft:entity"]["description"]["properties"] = {
        "waguri:model": {"type": "int", "range": [0, len(models)], "default": 0, "client_sync": True},
        "waguri:emote": {"type": "int", "range": [0, len(EMOTE)], "default": 0, "client_sync": True},
    }
    return d


# ===========================================================================
# Item lemari, teks, manifest
# ===========================================================================
def ikon_lemari():
    img = Image.new("RGBA", (16, 16), KOSONG)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 1, 12, 14], fill=rgb("#b07a52"))
    d.rectangle([4, 2, 7, 13], fill=rgb("#d49ba8"))
    d.rectangle([8, 2, 11, 13], fill=rgb("#d49ba8"))
    d.rectangle([3, 1, 12, 1], fill=rgb("#7a5034"))
    d.rectangle([3, 14, 12, 14], fill=rgb("#7a5034"))
    d.point([(7, 8), (8, 8)], fill=rgb("#f5d36b"))
    d.point([(5, 4), (9, 4)], fill=rgb("#f7e3e8"))
    # bunga kecil (lambang "bunga yang harum")
    d.point([(13, 3), (14, 2), (14, 4), (15, 3)], fill=rgb("#ffffff"))
    d.point([(14, 3)], fill=rgb("#f5d36b"))
    return img


def item_lemari():
    return {
        "format_version": "1.26.30",
        "minecraft:item": {
            "description": {"identifier": "waguri:lemari", "menu_category": {"category": "items"}},
            "components": {
                "minecraft:icon": "waguri_lemari",
                "minecraft:display_name": {"value": "item.waguri:lemari.name"},
                "minecraft:max_stack_size": 1,
                "minecraft:glint": True,
                "waguri:lemari": {},
            },
        },
    }


def resep_lemari():
    return {
        "format_version": "1.20.10",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": "waguri:lemari"},
            "tags": ["crafting_table"],
            "ingredients": [{"item": "minecraft:book"}, {"item": "minecraft:pink_dye"}],
            "unlock": {"context": "AlwaysUnlocked"},
            "result": {"item": "waguri:lemari", "count": 1},
        },
    }


def manifest(nama, deskripsi, header, modul, tipe, dependensi=None):
    m = {
        "format_version": 2,
        "header": {"name": nama, "description": deskripsi, "uuid": header, "version": [1, 0, 0],
                   "min_engine_version": ENGINE},
        "modules": [{"type": tipe, "uuid": modul, "version": [1, 0, 0]}],
        "metadata": {"authors": ["Rakitin"]},
    }
    if dependensi:
        m["dependencies"] = [{"uuid": dependensi, "version": [1, 0, 0]}]
    return m


def data_script(models):
    """Daftar model & emote untuk script (dibuat otomatis agar selalu sinkron)."""
    daftar = [{"nama": "Skin sendiri (bawaan)", "ket": "Kembali ke skin Minecraft-mu."}]
    daftar += [{"nama": m.nama_id, "ket": m.deskripsi} for m in models]
    emote = [{"id": i, "nama": n} for i, _k, n in EMOTE]
    return ("// File ini dibuat otomatis oleh tools/buat_waguri.py. Jangan diedit manual.\n"
            f"export const MODEL = {json.dumps(daftar, ensure_ascii=False, indent=2)};\n\n"
            f"export const EMOTE = {json.dumps(emote, ensure_ascii=False, indent=2)};\n")


# ===========================================================================
# Pratinjau
# ===========================================================================
def render_model(img_tex, m, sisi="depan", S=6):
    """Proyeksi ortografis model (rotasi kubus diabaikan) pada pose diam."""
    lebar, atas, tinggi = 24, 38, 40
    out = Image.new("RGBA", (lebar * S, tinggi * S), KOSONG)
    kubus = [k for k in m.kubus if k["bone"] != "kelopak"]
    if sisi == "depan":
        kubus.sort(key=lambda k: -(k["origin"][2] - k["inflate"]))
    else:
        kubus.sort(key=lambda k: k["origin"][2] + k["size"][2] + k["inflate"])
    for k in kubus:
        jenis, u, v = k["uv"]
        w, h, d = [max(1, math.ceil(s)) for s in k["size"]]
        if jenis == "datar":
            continue
        fx, fy, fw, fh = kotak_uv(u, v, w, h, d)[sisi]
        muka = img_tex.crop((fx * K, fy * K, (fx + fw) * K, (fy + fh) * K))
        if k["mirror"]:
            muka = muka.transpose(Image.FLIP_LEFT_RIGHT)
        inf = k["inflate"]
        pw, ph = (k["size"][0] + 2 * inf) * S, (k["size"][1] + 2 * inf) * S
        if pw < 1 or ph < 1:
            continue
        muka = muka.resize((max(1, round(pw)), max(1, round(ph))), Image.NEAREST)
        x_kiri = k["origin"][0] - inf if sisi == "depan" else -(k["origin"][0] + k["size"][0] + inf)
        ty = k["origin"][1] + k["size"][1] + inf
        out.alpha_composite(muka, (round((x_kiri + lebar / 2) * S), round((atas - ty) * S)))
    # skala tinggi karakter (kaki tetap di lantai)
    if m.skala != 1:
        nw, nh = round(out.width * m.skala), round(out.height * m.skala)
        kecil = out.resize((nw, nh), Image.NEAREST)
        out2 = Image.new("RGBA", out.size, KOSONG)
        lantai = round(atas * S)
        out2.alpha_composite(kecil, ((out.width - nw) // 2, lantai - round(lantai * m.skala)))
        out = out2
    return out


def pratinjau(tekstur, models):
    S = 6
    kol = 24 * S
    img = Image.new("RGBA", (kol * len(models) + 20, 40 * S * 2 + 90), rgb("#f6eef0"))
    dr = ImageDraw.Draw(img)
    for i, m in enumerate(models):
        x = 10 + i * kol
        img.alpha_composite(render_model(tekstur[m.id], m, "depan", S), (x, 30))
        img.alpha_composite(render_model(tekstur[m.id], m, "belakang", S), (x, 40 * S + 60))
        dr.text((x + 6, 8), m.nama, fill=(60, 30, 50, 255))
    dr.text((10, 40 * S + 40), "Tampak belakang", fill=(60, 30, 50, 255))
    return img


# ===========================================================================
# Utama
# ===========================================================================
def main():
    rnd = random.Random(20261009)
    models = semua_model()
    tekstur = {}
    for m in models:  # satu tekstur HD per karakter
        img = Image.new("RGBA", (TEX_UNIT[0] * K, TEX_UNIT[1] * K), KOSONG)
        geo = bangun(m, Penata(*TEX_UNIT), img, rnd)
        tekstur[m.id] = img
        tulis_json(geo, RP, "models", "entity", f"waguri_{m.id}.geo.json")
        simpan(img, RP, "textures", "entity", "waguri", f"{m.id}.png")

    # ---------------- RP ----------------
    tulis_json(player_entity_rp(models), RP, "entity", "player.entity.json")
    tulis_json(render_controller_json(models), RP, "render_controllers", "waguri.render_controllers.json")
    tulis_json(animasi_json(models), RP, "animations", "waguri.animation.json")
    simpan(ikon_lemari(), RP, "textures", "items", "waguri_lemari.png")
    tulis_json({"resource_pack_name": "waguri", "texture_name": "atlas.items",
                "texture_data": {"waguri_lemari": {"textures": "textures/items/waguri_lemari"}}},
               RP, "textures", "item_texture.json")
    tulis_teks("item.waguri:lemari.name=Model Wardrobe\n", RP, "texts", "en_US.lang")
    tulis_teks("item.waguri:lemari.name=Lemari Model\n", RP, "texts", "id_ID.lang")
    tulis_json(["en_US", "id_ID"], RP, "texts", "languages.json")
    tulis_json(manifest("Waguri YSM §dRP", "Model pemain 3D bergaya anime ala Yes Steve Model: Kaoruko Waguri & teman-teman.",
                        UUID["rp_header"], UUID["rp_module"], "resources"), RP, "manifest.json")

    # ---------------- BP ----------------
    tulis_json(player_bp(models), BP, "entities", "player.json")
    tulis_json(item_lemari(), BP, "items", "lemari.json")
    tulis_json(resep_lemari(), BP, "recipes", "lemari.json")
    tulis_teks(data_script(models), BP, "scripts", "data.js")
    mbp = manifest("Waguri YSM §dBP", "Pilih model anime lewat Lemari Model (klik kanan). Tanpa eksperimen.",
                   UUID["bp_header"], UUID["bp_module"], "data", UUID["rp_header"])
    mbp["modules"].append({"type": "script", "language": "javascript", "uuid": UUID["bp_script"],
                           "version": [1, 0, 0], "entry": "scripts/main.js"})
    mbp["dependencies"] = [{"module_name": "@minecraft/server", "version": "2.4.0"},
                           {"module_name": "@minecraft/server-ui", "version": "2.0.0"}] + mbp["dependencies"]
    tulis_json(mbp, BP, "manifest.json")

    # ---------------- ikon pack & pratinjau ----------------
    prev = pratinjau(tekstur, models)
    simpan(prev, DOCS, "pratinjau.png")
    kaoruko = render_model(tekstur["kaoruko"], models[0], "depan", 6)
    bbox = kaoruko.getbbox()
    kep = kaoruko.crop((bbox[0], bbox[1], bbox[2], bbox[1] + (bbox[2] - bbox[0])))
    ikon = Image.new("RGBA", (128, 128), rgb("#f3c9d3"))
    ikon.alpha_composite(kep.resize((112, 112), Image.NEAREST), (8, 8))
    simpan(ikon, RP, "pack_icon.png")
    simpan(ikon, BP, "pack_icon.png")
    simpan(tekstur["kaoruko"].resize((512, 512), Image.NEAREST), DOCS, "tekstur_kaoruko_x2.png")
    print("Selesai:", ", ".join(m.nama for m in models))


if __name__ == "__main__":
    main()
