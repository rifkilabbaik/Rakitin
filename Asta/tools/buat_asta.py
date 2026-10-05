"""Generator paket Asta (Black Clover) untuk Minecraft Bedrock.

Membuat:
  Asta_Skin/  skin pack Asta (64x64, model klasik Steve)
  Asta_RP/    resource pack: armor Demon (menggantikan tekstur armor Netherite),
              elytra sayap iblis, 4 pedang iblis (ikon + model 3D ukuran besar)
  Asta_BP/    behavior pack: 4 item pedang + resep (pedang apa saja + ingot)
  docs/       gambar pratinjau

Semua gambar dibuat secara prosedural (pixel art). Jalankan dari folder Asta:
    python3 tools/buat_asta.py
Butuh paket: pip install pillow
"""

import json
import math
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIN = os.path.join(ROOT, "Asta_Skin")
RP = os.path.join(ROOT, "Asta_RP")
BP = os.path.join(ROOT, "Asta_BP")
DOCS = os.path.join(ROOT, "docs")

ENGINE = [1, 26, 30]
UUID = {
    "skin_header": "00b78e6d-c323-46e0-ae73-c6b5ce2ca7af",
    "skin_module": "15783c09-cf35-4d41-ba1c-592f39c3f610",
    "rp_header": "99fd278e-fca4-443d-85b3-c81b3eecf5c7",
    "rp_module": "3e9a5ec4-0ea1-44be-afbe-c2031b2dbe4c",
    "bp_header": "8e63df46-074f-4ba6-b764-50761c5d9263",
    "bp_module": "91df387d-3a25-43b7-a043-23004968a1ad",
}

random.seed(20261005)


# ===========================================================================
# Alat dasar
# ===========================================================================
def hex2rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ubah(w, f):
    r, g, b, a = w
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


# Piksel transparan diberi RGB hitam supaya tetap gelap bila material tidak
# memakai alpha test (mis. elytra).
KOSONG = (12, 12, 14, 0)


def kanvas(w, h):
    return Image.new("RGBA", (w, h), KOSONG)


def piksel(img):
    f = getattr(img, "get_flattened_data", None)
    return list(f() if f else img.getdata())


def simpan(img, *bagian):
    path = os.path.join(*bagian)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


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


def grid(img, x0, y0, baris, palet, derau=0.04):
    """Lukis pola karakter. '.' = biarkan (transparan)."""
    for y, s in enumerate(baris):
        for x, c in enumerate(s):
            if c == "." or c == " ":
                continue
            w = palet[c]
            if derau and w[3]:
                w = ubah(w, 1 + random.uniform(-derau, derau))
            img.putpixel((x0 + x, y0 + y), w)


def kotak_uv(u, v, w, h, d):
    """Posisi tiap sisi kubus pada tekstur (tata letak box-UV Minecraft)."""
    return {
        "atas": (u + d, v, w, d),
        "bawah": (u + d + w, v, w, d),
        "kanan": (u, v + d, d, h),
        "depan": (u + d, v + d, w, h),
        "kiri": (u + d + w, v + d, d, h),
        "belakang": (u + d + w + d, v + d, w, h),
    }


def lukis_kubus(img, u, v, w, h, d, sisi, palet, derau=0.04):
    """sisi: dict nama_sisi -> list string (ukuran harus pas)."""
    pos = kotak_uv(u, v, w, h, d)
    for nama, baris in sisi.items():
        x0, y0, fw, fh = pos[nama]
        assert len(baris) == fh and all(len(b) == fw for b in baris), (nama, u, v, len(baris), fw, fh)
        grid(img, x0, y0, baris, palet, derau)


def isi(w, h, c):
    return [c * w for _ in range(h)]


def acak_baris(w, h, pilihan, bobot=None):
    return ["".join(random.choices(pilihan, weights=bobot, k=w)) for _ in range(h)]


# ===========================================================================
# Palet
# ===========================================================================
PALET = {
    # rambut perak Asta
    "H": hex2rgb("#e4e4ea"), "h": hex2rgb("#b9b9c4"), "g": hex2rgb("#8a8a98"),
    # ikat kepala
    "B": hex2rgb("#1d1d20"), "R": hex2rgb("#c3161c"), "r": hex2rgb("#7e0d11"),
    # kulit & wajah
    "S": hex2rgb("#f1c49c"), "s": hex2rgb("#d6a079"), "W": hex2rgb("#f6f6f6"),
    "E": hex2rgb("#3fa64c"), "e": hex2rgb("#1d6b2a"), "M": hex2rgb("#5e2219"), "T": hex2rgb("#fbfbfb"),
    # baju hitam, jubah, emas
    "K": hex2rgb("#24242a"), "k": hex2rgb("#141418"), "G": hex2rgb("#d7ad3c"), "y": hex2rgb("#9c7a22"),
    "C": hex2rgb("#b3262b"),
    # celana & sepatu
    "N": hex2rgb("#2c3449"), "n": hex2rgb("#1d2333"), "L": hex2rgb("#8c5a2c"), "l": hex2rgb("#64401f"),
    # iblis
    "D": hex2rgb("#161618"), "d": hex2rgb("#2c2c33"), "X": hex2rgb("#e3201f"), "x": hex2rgb("#8d0c0e"),
    "o": hex2rgb("#4a4a54"), "O": hex2rgb("#6a6a76"), "Z": hex2rgb("#ff5a3c"),
}


# ===========================================================================
# 1. Skin Asta (64x64, lengan 4 piksel)
# ===========================================================================
def skin_asta():
    img = kanvas(64, 64)
    P = PALET

    # ---------------- kepala (0,0) ----------------
    kepala = {
        "atas": acak_baris(8, 8, "HHHhg", [5, 3, 1, 2, 1]),
        "bawah": ["hSSSSSSh", "hSSSSSSh", "hsSSSSsh", "hSSSSSSh", "hSSSSSSh", "hhSSSShh", "hhhhhhhh", "hhhhhhhh"],
        "depan": [
            "hHHgHHhH",
            "BBRRBBBB",
            "HhSHHShH",
            "SggSSggS",
            "SWESSEWS",
            "SSSssSSS",
            "SsTTTTsS",
            "SSSssSSS",
        ],
        "kanan": [
            "HhHHgHHh",
            "BBBBBBBB",
            "HhHHhHHh",
            "hHHhHHSS",
            "HhHHhsSS",
            "hHHHssSS",
            "HhHhsSSS",
            "hHgHSSSS",
        ],
        "kiri": [
            "hHHgHHhH",
            "BBBBBBBB",
            "hHHhHHhH",
            "SSHHhHHh",
            "SSshHHhH",
            "SSssHHHh",
            "SSSshHhH",
            "SSSSHgHh",
        ],
        "belakang": [
            "HhHHgHHh",
            "BBBBBBBB",
            "HHhBBhHH",
            "hHHBBHhH",
            "HhHHhHHh",
            "hHgHHhHg",
            "HhHHhHHh",
            "hHhHHgHh",
        ],
    }
    lukis_kubus(img, 0, 0, 8, 8, 8, kepala, P)

    # ---------------- lapisan topi (32,0): volume rambut + ikat kepala ----------------
    topi = {
        "atas": acak_baris(8, 8, "HHhg.", [4, 3, 2, 1, 2]),
        "depan": [
            "HhH.HHgH",
            "BBRRBBBB",
            "H.h..H.h",
            "........",
            "........",
            "........",
            "........",
            "........",
        ],
        "kanan": [
            "HhHHgHHh",
            "BBBBBBBB",
            "HhHHhH.h",
            "hHHh.H..",
            "H.Hh....",
            "h.H.....",
            "........",
            "........",
        ],
        "kiri": [
            "hHHgHHhH",
            "BBBBBBBB",
            "h.HhHHhH",
            "..H.hHHh",
            "....hH.H",
            ".....H.h",
            "........",
            "........",
        ],
        "belakang": [
            "HhHHgHHh",
            "BBBBBBBB",
            "HHhBBhHH",
            "hH.BB.hH",
            "H...B..h",
            "h......H",
            "........",
            "........",
        ],
    }
    lukis_kubus(img, 32, 0, 8, 8, 8, topi, P)

    # ---------------- badan (16,16) ----------------
    badan = {
        "atas": ["KKKCCKKK", "KKCCCCKK", "KKCCCCKK", "KKKKKKKK"],
        "bawah": isi(8, 4, "N"),
        "depan": [
            "KKCCCCKK",
            "KKkSSKKK",
            "KKKSsKKK",
            "KKSSSKKK",
            "KkSsSSKK",
            "KKSSsSSK",
            "KsSsSsSK",
            "KSsSsSsK",
            "KKSsSsKK",
            "LLLGGLLL",
            "lLLyyLLl",
            "NNnNNnNN",
        ],
        "kanan": ["KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKKk", "KKKK", "LLLL", "lLLl", "NNnN"],
        "kiri": ["KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "kKKK", "KKKK", "LLLL", "lLLl", "NnNN"],
        "belakang": [
            "KKKCCKKK",
            "KKKKKKKK",
            "KkKKKKkK",
            "KKKKKKKK",
            "KKkKKKKK",
            "KKKKKkKK",
            "KKKKKKKK",
            "KkKKKKkK",
            "KKKKKKKK",
            "LLLLLLLL",
            "lLLLLLLl",
            "NNnNNnNN",
        ],
    }
    lukis_kubus(img, 16, 16, 8, 12, 4, badan, P)

    # lapisan jaket (16,32): jubah Banteng Hitam di bahu kiri Asta (kanan layar)
    jaket = {
        "atas": [".....KKK", ".....KKK", ".....KKK", ".....KKK"],
        "depan": [
            ".....GKK",
            ".....GKK",
            ".....GyK",
            ".....GKK",
            ".....GGG",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
        ],
        "kiri": ["KKKK", "KKKK", "KKKK", "KKKK", "GGGG", "....", "....", "....", "....", "....", "....", "...."],
        "belakang": [
            "KKKK....",
            "KGGK....",
            "GyyG....",
            "KGGK....",
            "KKKK....",
            "GGGG....",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
        ],
    }
    lukis_kubus(img, 16, 32, 8, 12, 4, jaket, P)

    # ---------------- lengan kanan Asta (40,16): lengan hitam + lambang semanggi emas ----------------
    lengan_kanan = {
        "atas": ["KKKK", "KkKK", "KKKK", "KKkK"],
        "bawah": ["SSSS", "SsSS", "SSSS", "SSsS"],
        "depan": ["KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKKK", "kKKk", "KKKK", "SSSS", "SsSS"],
        "kanan": ["KKKK", "KGKK", "GyGK", "KGKK", "KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "kKKk", "SSSS", "SSsS"],
        "kiri": ["KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKKK", "KkKK", "KKKK", "KKKK", "kKKk", "SSSS", "sSSS"],
        "belakang": ["KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKKK", "KKkK", "KKKK", "KKKK", "kKKk", "SSSS", "SSSs"],
    }
    lukis_kubus(img, 40, 16, 4, 12, 4, lengan_kanan, P)

    # ---------------- lengan kiri Asta (32,48) ----------------
    lengan_kiri = {
        "atas": ["KKKK", "KKkK", "KKKK", "KkKK"],
        "bawah": ["SSSS", "SSsS", "SSSS", "SsSS"],
        "depan": ["KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "KKKK", "kKKk", "KKKK", "SSSS", "SSsS"],
        "kanan": ["KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKKK", "KkKK", "KKKK", "KKKK", "kKKk", "SSSS", "sSSS"],
        "kiri": ["KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "kKKk", "SSSS", "SSsS"],
        "belakang": ["KKKK", "KkKK", "KKKK", "KKkK", "KKKK", "KKKK", "KKkK", "KKKK", "KKKK", "kKKk", "SSSS", "SSSs"],
    }
    lukis_kubus(img, 32, 48, 4, 12, 4, lengan_kiri, P)
    # lapisan lengan kiri (48,48): jubah menutupi bahu
    jubah_bahu = {
        "atas": ["KKKK", "KKKK", "KKKK", "KKKK"],
        "depan": ["KKKK", "KKKK", "KKKK", "GGGG"] + ["...."] * 8,
        "kanan": ["KKKK", "KKKK", "KKKK", "GGGG"] + ["...."] * 8,
        "kiri": ["KKKK", "KKKK", "KKKK", "GGGG"] + ["...."] * 8,
        "belakang": ["KKKK", "KKKK", "KKKK", "GGGG"] + ["...."] * 8,
    }
    lukis_kubus(img, 48, 48, 4, 12, 4, jubah_bahu, P)

    # ---------------- kaki ----------------
    def kaki(cermin=False):
        depan = ["NNNN", "NnNN", "NNNN", "NNnN", "NNNN", "nNNN", "GGGG", "LLLL", "LlLL", "LLLL", "LGGL", "lGGl"]
        samping = ["NNNN", "NNnN", "NNNN", "NnNN", "NNNN", "NNNn", "GGGG", "LLLL", "LLlL", "LLLL", "LLLL", "llll"]
        belakang = ["NNNN", "NnNN", "NNNN", "NNNN", "NNnN", "NNNN", "GGGG", "LLLL", "LLLL", "LlLL", "LLLL", "llll"]
        if cermin:
            depan = [b[::-1] for b in depan]
        return {
            "atas": ["NNNN"] * 4,
            "bawah": ["llll", "lLLl", "lLLl", "llll"],
            "depan": depan,
            "kanan": samping,
            "kiri": [b[::-1] for b in samping],
            "belakang": belakang,
        }

    lukis_kubus(img, 0, 16, 4, 12, 4, kaki(), P)
    lukis_kubus(img, 16, 48, 4, 12, 4, kaki(True), P)
    # lapisan celana (manset sepatu menonjol)
    manset = {n: ["...."] * 6 + ["GGGG", "LLLL"] + ["...."] * 4 for n in ("depan", "kanan", "kiri", "belakang")}
    lukis_kubus(img, 0, 32, 4, 12, 4, manset, P)
    lukis_kubus(img, 0, 48, 4, 12, 4, manset, P)
    return img


# ===========================================================================
# 2. Armor iblis (layout 64x32 armor Bedrock) -> netherite_1 & netherite_2
# ===========================================================================
def armor_1():
    """Helm, zirah dada, dan sepatu (Asta mode Devil Union, tanpa sayap)."""
    img = kanvas(64, 32)
    P = PALET
    # ---- helm (kepala 0,0): rambut hitam, ikat merah, mata merah, tanda wajah, tanduk ----
    helm = {
        "atas": acak_baris(8, 8, "Ddo", [5, 3, 1]),
        "bawah": isi(8, 8, "."),
        "depan": [
            "DdDDdDDd",
            "XXDXXxDX",
            "D.dD.dD.",
            "........",
            ".DX..XD.",
            "......D.",
            ".....D..",
            "........",
        ],
        "kanan": [
            "DdDDdDDd",
            "XXDXXXDX",
            "DdDoOo..",
            "DdoO.Oo.",
            "DdDo.Oo.",
            "DdD..o..",
            "Dd......",
            "D.......",
        ],
        "kiri": [
            "dDDdDDdD",
            "XDXXXDXX",
            "..oOoDdD",
            ".oO.OodD",
            ".oO.oDdD",
            "..o..DdD",
            "......dD",
            ".......D",
        ],
        "belakang": [
            "DdDDdDDd",
            "XXXXXXXX",
            "DDdXXdDD",
            "dDDxxDDd",
            "DdDDDDdD",
            "dDdDDdDd",
            "D.dDDd.D",
            "...dD...",
        ],
    }
    lukis_kubus(img, 0, 0, 8, 8, 8, helm, P)
    # lapisan helm (32,0): jambul runcing di atas
    topi = {
        "atas": acak_baris(8, 8, "Dd.", [3, 2, 3]),
        "depan": ["D.dD.Dd.", "........", "........", "........", "........", "........", "........", "........"],
        "kanan": ["DdD.D.dD", "........", "D.......", "........", "........", "........", "........", "........"],
        "kiri": ["Dd.D.DdD", "........", ".......D", "........", "........", "........", "........", "........"],
        "belakang": ["dD.DD.Dd", "........", "D......D", "........", "........", "........", "........", "........"],
    }
    lukis_kubus(img, 32, 0, 8, 8, 8, topi, P)

    # ---- zirah dada (badan 16,16): lambang merah dengan bintang salib hitam ----
    dada = {
        "atas": ["DXDDDDXD", "DDdDDdDD", "DDDdDDDD", "DdDDDDdD"],
        "bawah": ["DDDDDDDD"] * 4,
        "depan": [
            "XDDXXDDX",
            "DXXXXXXD",
            "DXXDDXXD",
            "DXDXXDXD",
            "DXXDDXXD",
            "dDXXXXDd",
            "DdDXXDdD",
            "dDdXXdDd",
            "DxDdXDxD",
            "dDxDDxDd",
            "XdDdDdDX",
            "DXdDDdXD",
        ],
        "kanan": ["XDDD", "DXDd", "DDXD", "dDDX", "DdDx", "DDdD", "xDDD", "DxDd", "DDxD", "dDDx", "DdDD", "XDDX"],
        "kiri": ["DDDX", "dDXD", "DXDD", "XDDd", "xDdD", "DdDD", "DDDx", "dDxD", "DxDD", "xDDd", "DDdD", "XDDX"],
        "belakang": [
            "XDDXXDDX",
            "DXDXXDXD",
            "DDXXXXDD",
            "DdDXXDdD",
            "DDdXXdDD",
            "DxDXXDxD",
            "DDxXXxDD",
            "dDDXXDDd",
            "DdDxxDdD",
            "dDxDDxDd",
            "XDdDDdDX",
            "DXDddDXD",
        ],
    }
    lukis_kubus(img, 16, 16, 8, 12, 4, dada, P)

    # ---- lengan (40,16): pelindung bahu merah, sarung tangan bercakar ----
    lengan = {
        "atas": ["XXXX", "XDDX", "XDDX", "XXXX"],
        "bawah": ["DXDX", "XDXD", "DXDX", "XDXD"],
        "depan": ["XXXX", "DXXD", "DDDD", "DdDD", "DDxD", "DdDD", "DxDD", "DDdD", "DDDD", "XXXX", "DDDD", "XDXD"],
        "kanan": ["XXXX", "DXXD", "DDDD", "DDdD", "DxDD", "DDDd", "DDxD", "dDDD", "DDDD", "XXXX", "DDDD", "XDXD"],
        "kiri": ["XXXX", "DXXD", "DDDD", "DdDD", "DDDD", "DDdD", "dDDD", "DDDd", "DDDD", "XXXX", "DDDD", "DXDX"],
        "belakang": ["XXXX", "DXXD", "DDDD", "DDdD", "DxDD", "DDDD", "DDxD", "dDDD", "DDDD", "XXXX", "DDDD", "DXDX"],
    }
    lukis_kubus(img, 40, 16, 4, 12, 4, lengan, P)

    # ---- sepatu (kaki 0,16; hanya bagian bawah) ----
    k = "...."
    sepatu = {
        "atas": [k] * 4,
        "bawah": ["DDDD", "DxxD", "DxxD", "DDDD"],
        "depan": [k] * 6 + ["XDDX", "DXXD", "DDDD", "DxDD", "DDDD", "XDXD"],
        "kanan": [k] * 6 + ["XDDX", "DXDD", "DDxD", "DDDD", "DdDD", "DDDD"],
        "kiri": [k] * 6 + ["XDDX", "DDXD", "DxDD", "DDDD", "DDdD", "DDDD"],
        "belakang": [k] * 6 + ["XDDX", "DXXD", "DDDD", "DDDD", "DDxD", "DDDD"],
    }
    lukis_kubus(img, 0, 16, 4, 12, 4, sepatu, P)
    return img


def armor_2():
    """Celana zirah (kaki + pinggang)."""
    img = kanvas(64, 32)
    P = PALET
    celana = {
        "atas": ["DDDD"] * 4,
        "bawah": [k for k in ["...."] * 4],
        "depan": ["DDDD", "DxDD", "DdDD", "DDdD", "dDDD", "DXXD", "XDDX", "DDDD", "DdDD", "....", "....", "...."],
        "kanan": ["DDDD", "DDDd", "DxDD", "DDDD", "dDDD", "DDxD", "DXDD", "XDDD", "DDDD", "....", "....", "...."],
        "kiri": ["DDDD", "dDDD", "DDxD", "DDDD", "DDDd", "DxDD", "DDXD", "DDDX", "DDDD", "....", "....", "...."],
        "belakang": ["DDDD", "DdDD", "DDDd", "DxDD", "DDxD", "dDDD", "DDdD", "DxxD", "DDDD", "....", "....", "...."],
    }
    lukis_kubus(img, 0, 16, 4, 12, 4, celana, P)
    pinggang = {
        "depan": ["........"] * 8 + ["DDDDDDDD", "XDDXXDDX", "DXDDDDXD", "DDDXXDDD"],
        "kanan": ["...."] * 8 + ["DDDD", "XDDX", "DXXD", "DDDD"],
        "kiri": ["...."] * 8 + ["DDDD", "XDDX", "DXXD", "DDDD"],
        "belakang": ["........"] * 8 + ["DDDDDDDD", "XDDXXDDX", "DXDDDDXD", "DDDxxDDD"],
    }
    lukis_kubus(img, 16, 16, 8, 12, 4, pinggang, P)
    return img


# ===========================================================================
# 3. Elytra: sayap iblis compang-camping (layout 64x32)
# ===========================================================================
def sayap_muka(cermin=False):
    """Satu muka sayap 10x20: membran hitam, tepi merah, ujung bawah robek."""
    w, h = 10, 20
    m = [["D"] * w for _ in range(h)]
    # tulang sayap merah dari pangkal (kiri atas) menyebar ke bawah
    tulang = [((0, 0), (9, 1)), ((0, 0), (8, 9)), ((0, 0), (5, 16)), ((0, 0), (1, 19))]
    for (ax, ay), (bx, by) in tulang:
        n = max(abs(bx - ax), abs(by - ay))
        for i in range(n + 1):
            x = round(ax + (bx - ax) * i / n)
            y = round(ay + (by - ay) * i / n)
            m[y][x] = "x" if i > n * 0.6 else "X"
    # tepi atas & luar merah
    for x in range(w):
        m[0][x] = "X"
    for y in range(h):
        m[y][w - 1] = "X" if y < 6 else m[y][w - 1]
    # bagian bawah robek: kolom memanjang beda-beda (seperti api hitam)
    panjang = [20, 17, 19, 14, 18, 12, 16, 10, 13, 7]
    for x in range(w):
        for y in range(panjang[x], h):
            m[y][x] = "."
        ujung = panjang[x] - 1
        if 0 < ujung < h and m[ujung][x] != ".":
            m[ujung][x] = "X"
    # sedikit tekstur membran
    for y in range(1, h):
        for x in range(w - 1):
            if m[y][x] == "D" and random.random() < 0.18:
                m[y][x] = "d"
    baris = ["".join(r) for r in m]
    if cermin:
        baris = [b[::-1] for b in baris]
    return baris


def elytra():
    img = kanvas(64, 32)
    depan = sayap_muka()
    belakang = sayap_muka(cermin=True)
    tepi = ["XD"] * 20
    sisi = {
        "atas": ["XXXXXXXXXX", "DDDDDDDDDD"],
        "bawah": ["DDDDDDDDDD", "DDDDDDDDDD"],
        "kanan": tepi,
        "depan": depan,
        "kiri": tepi,
        "belakang": belakang,
    }
    # potong sisi samping supaya ikut robek
    for nama in ("kanan", "kiri"):
        sisi[nama] = [r if y < 14 else ".." for y, r in enumerate(sisi[nama])]
    lukis_kubus(img, 22, 0, 10, 20, 2, sisi, PALET)
    return img


# ===========================================================================
# 4. Empat pedang iblis (sprite 2 piksel per unit model)
# ===========================================================================
PX = 2  # piksel per unit model (1 blok = 16 unit, pemain = 32 unit)
HITAM = hex2rgb("#151517")
HITAM2 = hex2rgb("#26262c")
SOROT = hex2rgb("#3d3d46")
MERAH = hex2rgb("#d41b1b")
MERAH2 = hex2rgb("#8e0b0d")
MERAH3 = hex2rgb("#ff4b33")
GARIS = hex2rgb("#050506")


def outline(img, warna=GARIS):
    salin = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            if salin.getpixel((x, y))[3]:
                continue
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ox, y + oy
                if 0 <= nx < img.width and 0 <= ny < img.height and salin.getpixel((nx, ny))[3]:
                    img.putpixel((x, y), warna)
                    break


def poli(img, titik, warna):
    ImageDraw.Draw(img).polygon(titik, fill=warna)


def rect(img, x0, y0, x1, y1, warna):
    ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], fill=warna)


def garis(img, a, b, warna, lebar=1):
    ImageDraw.Draw(img).line([a, b], fill=warna, width=lebar)


def gagang(img, cx, y0, y1, lebar, warna=HITAM, lilit=HITAM2, aksen=None):
    """Pegangan berlilit; cx = kolom tengah (kiri dari pasangan piksel)."""
    x0 = cx - lebar // 2 + 1
    rect(img, x0, y0, x0 + lebar - 1, y1, warna)
    for y in range(y0, y1 + 1):
        if (y - y0) % 3 == 1:
            rect(img, x0, y, x0 + lebar - 1, y, aksen or lilit)


def sorot_kiri(img, warna=SOROT):
    """Garis terang di sisi kiri tiap baris (kesan logam)."""
    for y in range(img.height):
        for x in range(img.width):
            p = img.getpixel((x, y))
            if p[3] and p[:3] == HITAM[:3]:
                if x == 0 or img.getpixel((x - 1, y))[3] == 0:
                    img.putpixel((x, y), warna)
                break


def pedang_pembasmi():
    """Demon-Slayer Sword: pedang raksasa lebar, ujung runcing pendek, pola akar merah."""
    W, L = 10, 32
    img = kanvas(W * PX, L * PX)
    poli(img, [(2, 6), (9, 0), (10, 0), (17, 6), (17, 45), (2, 45)], HITAM)
    poli(img, [(5, 9), (9, 4), (10, 4), (14, 9), (14, 43), (5, 43)], MERAH)
    # akar/urat hitam bercabang (seperti retakan api)
    rnd = random.Random(7)

    def cabang(x, y, arah, panjang, tebal):
        for _ in range(panjang):
            nx = x + arah + rnd.choice((-1, 0, 0, 1))
            ny = y - 1
            nx = max(5, min(14, nx))
            if ny < 6:
                return
            img.putpixel((nx, ny), HITAM)
            if tebal:
                img.putpixel((min(14, nx + 1), ny), HITAM)
            if rnd.random() < 0.12:
                cabang(nx, ny, rnd.choice((-1, 1)), rnd.randint(3, 7), False)
            x, y = nx, ny

    cabang(9, 44, 0, 36, True)
    for sx in (6, 12):
        cabang(sx, 44, 0, 20, False)
    for y in range(9, 44, 5):
        img.putpixel((7, y), MERAH3)
        img.putpixel((12, y + 2), MERAH3)
    # pelindung tangan, pegangan, pangkal
    poli(img, [(0, 46), (19, 46), (19, 48), (17, 49), (2, 49), (0, 48)], HITAM)
    rect(img, 8, 47, 11, 48, MERAH2)
    gagang(img, 9, 50, 59, 4)
    poli(img, [(7, 60), (12, 60), (13, 62), (10, 63), (9, 63), (6, 62)], HITAM)
    rect(img, 9, 61, 10, 61, MERAH)
    sorot_kiri(img)
    return img, W, L, 27.5  # pusat pegangan (unit dari atas)


def pedang_penghuni():
    """Demon-Dweller Sword: lebar, ujung datar membulat, lambang semanggi merah."""
    W, L = 8, 28
    img = kanvas(W * PX, L * PX)
    poli(img, [(4, 0), (11, 0), (13, 2), (13, 35), (14, 38), (11, 40), (4, 40), (1, 38), (2, 35), (2, 2)], HITAM)
    # lambang keriting/semanggi
    for cx, cy in ((7.5, 5), (5.5, 8), (9.5, 8)):
        ImageDraw.Draw(img).ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6], fill=MERAH)
    rect(img, 7, 8, 8, 12, MERAH)
    rect(img, 6, 12, 9, 12, MERAH)
    # alur tengah
    rect(img, 7, 15, 8, 36, HITAM2)
    for y in range(16, 36, 4):
        img.putpixel((7, y), MERAH2)
    # pelindung tangan melengkung ke bawah
    poli(img, [(0, 41), (15, 41), (15, 44), (13, 43), (2, 43), (0, 44)], HITAM)
    rect(img, 7, 41, 8, 42, MERAH)
    gagang(img, 7, 44, 51, 4)
    poli(img, [(5, 52), (10, 52), (11, 54), (9, 55), (6, 55), (4, 54)], HITAM)
    rect(img, 7, 53, 8, 53, MERAH)
    sorot_kiri(img)
    return img, W, L, 24.0


def pedang_penghancur():
    """Demon-Destroyer Sword: ramping, garis merah di tengah, salib runcing dekat ujung."""
    W, L = 6, 26
    img = kanvas(W * PX, L * PX)
    poli(img, [(5, 0), (6, 0), (8, 5), (8, 38), (3, 38), (3, 5)], HITAM)
    rect(img, 5, 6, 6, 36, MERAH)
    # salib dekat ujung
    poli(img, [(0, 9), (11, 9), (9, 11), (2, 11)], HITAM)
    rect(img, 3, 10, 8, 10, MERAH)
    img.putpixel((5, 3), MERAH)
    img.putpixel((6, 3), MERAH)
    # duri merah di pangkal bilah
    for y in range(29, 37, 3):
        img.putpixel((2, y), MERAH)
        img.putpixel((9, y), MERAH)
        img.putpixel((1, y + 1), MERAH2)
        img.putpixel((10, y + 1), MERAH2)
    # pelindung tangan dengan ujung naik
    poli(img, [(0, 37), (2, 39), (9, 39), (11, 37), (11, 41), (0, 41)], HITAM)
    rect(img, 4, 39, 7, 40, MERAH2)
    gagang(img, 5, 42, 48, 2)
    ImageDraw.Draw(img).ellipse([3, 48, 8, 51], fill=HITAM)
    img.putpixel((5, 49), MERAH)
    img.putpixel((6, 50), MERAH)
    sorot_kiri(img)
    return img, W, L, 22.5


def katana_penebas():
    """Demon-Slasher Katana: bilah melengkung, mata pedang merah bergerigi."""
    W, L = 5, 28
    img = kanvas(W * PX, L * PX)
    panjang_bilah = 41
    for y in range(panjang_bilah):
        t = 1 - y / panjang_bilah
        lengkung = 3.2 * t * t  # melengkung ke kanan di ujung
        x = 2 + round(lengkung)
        if y < 3:  # ujung runcing
            rect(img, x + 2 - y // 2, y, x + 3, y, HITAM)
            if y == 2:
                img.putpixel((x + 1, y), MERAH)
            continue
        rect(img, x + 2, y, x + 4, y, HITAM)  # punggung
        gerigi = 1 if (y // 2) % 2 else 0
        rect(img, x + gerigi, y, x + 1, y, MERAH if y % 4 else MERAH3)
    # habaki & tsuba
    rect(img, 3, 41, 6, 41, MERAH2)
    ImageDraw.Draw(img).ellipse([0, 42, 9, 44], fill=HITAM)
    img.putpixel((2, 43), MERAH)
    img.putpixel((7, 43), MERAH)
    # pegangan berlilit belah ketupat hitam-merah
    rect(img, 3, 45, 6, 53, HITAM)
    for y in range(45, 54):
        img.putpixel((3 + (y % 4 if y % 4 < 4 else 0), y), MERAH2)
    rect(img, 3, 54, 6, 55, HITAM2)
    sorot_kiri(img)
    return img, W, L, 24.5


PEDANG = [
    # id, pembuat sprite, ingot, nama EN, nama ID, damage, durability
    ("demon_destroyer", pedang_penghancur, "iron_ingot", "Demon-Destroyer Sword", "Pedang Penghancur Iblis", 8, 1200),
    ("demon_dweller", pedang_penghuni, "gold_ingot", "Demon-Dweller Sword", "Pedang Penghuni Iblis", 9, 1500),
    ("demon_slayer", pedang_pembasmi, "diamond", "Demon-Slayer Sword", "Pedang Pembasmi Iblis", 10, 2031),
    ("demon_slasher", katana_penebas, "netherite_ingot", "Demon-Slasher Katana", "Katana Penebas Iblis", 11, 2500),
]


def ikon_pedang(sprite, L, ukuran=32):
    """Ikon inventori: sprite diputar 45 derajat, besarnya sesuai panjang asli."""
    besar = sprite.resize((sprite.width * 8, sprite.height * 8), Image.NEAREST)
    putar = besar.rotate(-45, resample=Image.NEAREST, expand=True)
    putar = putar.crop(putar.getbbox())
    sisi = max(10, round((ukuran - 2) * min(1.0, L / 32)))
    skala = sisi / max(putar.size)
    kecil = putar.resize((max(1, round(putar.width * skala)), max(1, round(putar.height * skala))), Image.LANCZOS)
    hasil = kanvas(ukuran, ukuran)
    # ujung pedang di kanan atas, pegangan di kiri bawah
    ox, oy = ukuran - 1 - kecil.width, 1
    hasil.alpha_composite(kecil, (ox, oy))
    data = [(r, g, b, 255) if a >= 110 else KOSONG for (r, g, b, a) in piksel(hasil)]
    hasil.putdata(data)
    return hasil


# ===========================================================================
# 5. Ikon item vanilla yang diganti (armor netherite & elytra)
# ===========================================================================
def ikon_grid(baris):
    img = kanvas(16, 16)
    grid(img, 0, 0, baris, PALET, 0.03)
    return img


IKON_VANILLA = {
    "netherite_helmet": [
        "................",
        "................",
        "...D..D..D..D...",
        "..DD.DDDDDD.DD..",
        "..DDDDDDDDDDDD..",
        ".oDXXXXXXXXXXDo.",
        "oO.XXDXXXXDXX.Oo",
        "o..DD......DD..o",
        "o..DX......XD..o",
        ".o.DD......DD.o.",
        "...DD......DD...",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "netherite_chestplate": [
        "................",
        "..XXX......XXX..",
        ".XDDDXXXXXXDDDX.",
        ".XDDDDXXXXDDDDX.",
        ".XDDDXXDDXXDDDX.",
        ".XDDXXDXXDXXDDX.",
        ".DD.XXXDDXXX.DD.",
        ".DD.DXXXXXXD.DD.",
        "....DDXXXXDD....",
        "....DdDXXDdD....",
        "....DDdXXdDD....",
        "....XDDDDDDX....",
        "....DXDDDDXD....",
        "....DDDDDDDD....",
        "................",
        "................",
    ],
    "netherite_leggings": [
        "................",
        "...DDDDDDDDDD...",
        "...XDDXXXXDDX...",
        "...DXDDDDDDXD...",
        "...DDDD..DDDD...",
        "...DXDD..DDXD...",
        "...DDXD..DXDD...",
        "...DXDD..DDXD...",
        "...XDDX..XDDX...",
        "...DXXD..DXXD...",
        "...DDDD..DDDD...",
        "...DdDD..DDdD...",
        "...DDDD..DDDD...",
        "................",
        "................",
        "................",
    ],
    "netherite_boots": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..XDDX....XDDX..",
        "..DXXD....DXXD..",
        "..DDDD....DDDD..",
        "..DxDD....DDxD..",
        "..DDDD....DDDD..",
        ".DDDDD....DDDDD.",
        "DDDDDD....DDDDDD",
        "XDXDXD....DXDXDX",
        "................",
        "................",
        "................",
    ],
    "elytra": [
        "................",
        ".XXXX......XXXX.",
        "XDDDDX....XDDDDX",
        "XDDDDDX..XDDDDDX",
        "XDXDDDDXXDDDDXDX",
        "XDDXDDDDDDDDXDDX",
        "XDDDXDDDDDDXDDDX",
        "XDdDDXDDDDXDDdDX",
        "XDDDdDX..XDdDDDX",
        ".DDDDDX..XDDDDD.",
        ".DD.DDX..XDD.DD.",
        ".D..DD....DD..D.",
        "....D......D....",
        "................",
        "................",
        "................",
    ],
}


# ===========================================================================
# 6. Pratinjau (tampak depan) untuk dokumentasi
# ===========================================================================
def wajah_depan(tex, u, v, w, h, d):
    x0, y0, fw, fh = kotak_uv(u, v, w, h, d)["depan"]
    return tex.crop((x0, y0, x0 + fw, y0 + fh))


def render_depan(skin, armor1=None, armor2=None):
    """Gambar 16x32 tampak depan (skin + lapisan + armor)."""
    img = Image.new("RGBA", (16, 32), (0, 0, 0, 0))

    def tempel(tex, u, v, w, h, d, x, y, cermin=False):
        if tex is None:
            return
        f = wajah_depan(tex, u, v, w, h, d)
        if cermin:
            f = f.transpose(Image.FLIP_LEFT_RIGHT)
        f = Image.merge("RGBA", f.split()[:3] + (f.split()[3].point(lambda a: 255 if a > 0 else 0),))
        img.alpha_composite(f, (x, y))

    # skin dasar + lapisan kedua
    tempel(skin, 0, 0, 8, 8, 8, 4, 0)
    tempel(skin, 32, 0, 8, 8, 8, 4, 0)
    tempel(skin, 16, 16, 8, 12, 4, 4, 8)
    tempel(skin, 16, 32, 8, 12, 4, 4, 8)
    tempel(skin, 40, 16, 4, 12, 4, 0, 8)
    tempel(skin, 32, 48, 4, 12, 4, 12, 8)
    tempel(skin, 48, 48, 4, 12, 4, 12, 8)
    tempel(skin, 0, 16, 4, 12, 4, 4, 20)
    tempel(skin, 0, 32, 4, 12, 4, 4, 20)
    tempel(skin, 16, 48, 4, 12, 4, 8, 20)
    tempel(skin, 0, 48, 4, 12, 4, 8, 20)
    if armor2 is not None:
        tempel(armor2, 16, 16, 8, 12, 4, 4, 8)
        tempel(armor2, 0, 16, 4, 12, 4, 4, 20)
        tempel(armor2, 0, 16, 4, 12, 4, 8, 20, True)
    if armor1 is not None:
        tempel(armor1, 0, 0, 8, 8, 8, 4, 0)
        tempel(armor1, 32, 0, 8, 8, 8, 4, 0)
        tempel(armor1, 16, 16, 8, 12, 4, 4, 8)
        tempel(armor1, 40, 16, 4, 12, 4, 0, 8)
        tempel(armor1, 40, 16, 4, 12, 4, 12, 8, True)
        tempel(armor1, 0, 16, 4, 12, 4, 4, 20)
        tempel(armor1, 0, 16, 4, 12, 4, 8, 20, True)
    return img


def render_sayap(tex):
    x0, y0, fw, fh = kotak_uv(22, 0, 10, 20, 2)["depan"]
    kanan = tex.crop((x0, y0, x0 + fw, y0 + fh))
    kiri = kanan.transpose(Image.FLIP_LEFT_RIGHT)
    img = Image.new("RGBA", (fw * 2, fh), (0, 0, 0, 0))
    img.alpha_composite(kanan, (0, 0))
    img.alpha_composite(kiri, (fw, 0))
    data = [p if p[3] else (0, 0, 0, 0) for p in piksel(img)]
    img.putdata(data)
    return img


def pratinjau(skin, a1, a2, sayap, sprites):
    S = 8  # piksel layar per unit model
    latar = hex2rgb("#e9e4dc")
    img = Image.new("RGBA", (1000, 360), latar)
    dr = ImageDraw.Draw(img)
    lantai = 320
    asta = render_depan(skin).resize((16 * S, 32 * S), Image.NEAREST)
    img.alpha_composite(asta, (30, lantai - 32 * S))
    # Asta mode iblis dengan sayap elytra di belakang
    s = render_sayap(sayap).resize((20 * S, 20 * S), Image.NEAREST)
    img.alpha_composite(s, (210 - 2 * S, lantai - 32 * S + 6 * S))
    iblis = render_depan(skin, a1, a2).resize((16 * S, 32 * S), Image.NEAREST)
    img.alpha_composite(iblis, (210, lantai - 32 * S))
    # pedang berdiri, skala sama dengan pemain (sprite 2 px/unit -> S/2)
    x = 420
    for (id_, _f, ingot, en, _id, dmg, _dur), (spr, W, L, _hc) in zip(PEDANG, sprites):
        p = spr.resize((spr.width * S // PX, spr.height * S // PX), Image.NEAREST)
        p = Image.merge("RGBA", p.split()[:3] + (p.split()[3].point(lambda a: 255 if a else 0),))
        img.alpha_composite(p, (x, lantai - p.height))
        dr.text((x, lantai + 8), en.replace(" ", "\n", 1), fill=(30, 30, 30, 255))
        x += max(p.width, 90) + 40
    dr.line([(10, lantai), (990, lantai)], fill=(120, 110, 100, 255), width=2)
    dr.text((30, 12), "Asta (skin)", fill=(30, 30, 30, 255))
    dr.text((210, 12), "Armor iblis + elytra", fill=(30, 30, 30, 255))
    dr.text((420, 12), "Pedang (skala sama dengan tinggi pemain = 2 blok)", fill=(30, 30, 30, 255))
    return img


def ikon_pack(skin, a1=None, latar="#1a1a1e"):
    kep = render_depan(skin, a1).crop((4, 0, 12, 8)).resize((96, 96), Image.NEAREST)
    img = Image.new("RGBA", (128, 128), hex2rgb(latar))
    img.alpha_composite(kep, (16, 16))
    ImageDraw.Draw(img).rectangle([0, 0, 127, 127], outline=hex2rgb("#c3161c"), width=6)
    return img


# ===========================================================================
# JSON: manifest, item, resep, attachable, geometri, animasi, teks
# ===========================================================================
def manifest(nama, deskripsi, header, modul, tipe, dependensi=None):
    m = {
        "format_version": 2,
        "header": {
            "name": nama,
            "description": deskripsi,
            "uuid": header,
            "version": [1, 0, 0],
        },
        "modules": [{"type": tipe, "uuid": modul, "version": [1, 0, 0]}],
        "metadata": {"authors": ["Rakitin"]},
    }
    if tipe != "skin_pack":
        m["header"]["min_engine_version"] = ENGINE
    if dependensi:
        m["dependencies"] = [{"uuid": dependensi, "version": [1, 0, 0]}]
    return m


def item_json(id_, dmg, dur):
    return {
        "format_version": "1.26.30",
        "minecraft:item": {
            "description": {"identifier": f"asta:{id_}", "menu_category": {"category": "equipment", "group": "minecraft:itemGroup.name.sword"}},
            "components": {
                "minecraft:icon": f"asta_{id_}",
                "minecraft:display_name": {"value": f"item.asta:{id_}.name"},
                "minecraft:max_stack_size": 1,
                "minecraft:hand_equipped": True,
                "minecraft:damage": dmg,
                "minecraft:durability": {"max_durability": dur},
                "minecraft:enchantable": {"slot": "sword", "value": 15},
                "minecraft:can_destroy_in_creative": False,
                "minecraft:tags": {"tags": ["minecraft:is_sword", "minecraft:is_tool"]},
                "minecraft:repairable": {
                    "repair_items": [{"items": ["minecraft:netherite_ingot"], "repair_amount": "context.other->q.remaining_durability + 0.25 * context.other->q.max_durability"}]
                },
            },
        },
    }


def resep_json(id_, ingot):
    return {
        "format_version": "1.20.10",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": f"asta:{id_}"},
            "tags": ["crafting_table"],
            "ingredients": [
                {"tag": "minecraft:is_sword"},
                {"item": f"minecraft:{ingot}"},
            ],
            "unlock": {"context": "AlwaysUnlocked"},
            "result": {"item": f"asta:{id_}", "count": 1},
        },
    }


# Titik pegangan dibuat sama dengan pegangan trident vanilla (y ~= 4 pada
# geometri trident), sehingga animasi pegang trident bisa dipakai ulang.
GRIP_Y = 4.0


def geometri_json(id_, W, L, hc):
    y0 = GRIP_Y - (L - hc)
    tw, th = W * PX, L * PX
    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": f"geometry.asta.{id_}",
                    "texture_width": tw,
                    "texture_height": th,
                    "visible_bounds_width": 4,
                    "visible_bounds_height": 4,
                    "visible_bounds_offset": [0, 1, 0],
                },
                "bones": [
                    {
                        "name": "pedang",
                        "binding": "q.item_slot_to_bone_name(c.item_slot)",
                        "pivot": [0.0, 24.0, 0.0],
                        "cubes": [
                            {
                                "origin": [-W / 2, y0, -0.125],
                                "size": [W, L, 0.25],
                                "uv": {
                                    "north": {"uv": [0, 0], "uv_size": [tw, th]},
                                    "south": {"uv": [tw, 0], "uv_size": [-tw, th]},
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


def attachable_json(id_):
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": f"asta:{id_}",
                "materials": {"default": "entity_alphatest", "enchanted": "entity_alphatest_glint"},
                "textures": {
                    "default": f"textures/asta/pedang/{id_}",
                    "enchanted": "textures/misc/enchanted_item_glint",
                },
                "geometry": {"default": f"geometry.asta.{id_}"},
                "animations": {
                    "orang_pertama": "animation.asta.pedang.orang_pertama",
                    "orang_ketiga": "animation.asta.pedang.orang_ketiga",
                },
                "scripts": {
                    "animate": [
                        {"orang_pertama": "c.is_first_person"},
                        {"orang_ketiga": "!c.is_first_person"},
                    ]
                },
                "render_controllers": ["controller.render.item_default"],
            }
        },
    }


def animasi_json():
    # Nilai diambil dari animasi pegang trident vanilla (animation.trident.*).
    return {
        "format_version": "1.10.0",
        "animations": {
            "animation.asta.pedang.orang_pertama": {
                "loop": True,
                "bones": {"pedang": {"position": [-7.0, -3.0, -2.0], "rotation": [152.0, -9.0, 25.0]}},
            },
            "animation.asta.pedang.orang_ketiga": {
                "loop": True,
                "bones": {"pedang": {"position": [1.5, -2.5, -10.5], "rotation": [97.0, -1.5, -49.0]}},
            },
        },
    }


def skin_pack_json():
    return {
        "skins": [
            {"localization_name": "asta", "geometry": "geometry.humanoid.custom", "texture": "asta.png", "type": "free"},
            {"localization_name": "asta_iblis", "geometry": "geometry.humanoid.custom", "texture": "asta_iblis.png", "type": "free"},
        ],
        "serialize_name": "AstaBlackClover",
        "localization_name": "AstaBlackClover",
    }


def skin_iblis(skin, a1, a2):
    """Skin tambahan: Asta mode iblis (armor dilukis langsung ke skin)."""
    img = skin.copy()

    def salin(src, su, sv, du, dv, w, h, d, cermin=False):
        ps, pd = kotak_uv(su, sv, w, h, d), kotak_uv(du, dv, w, h, d)
        for nama in ps:
            x0, y0, fw, fh = ps[nama]
            f = src.crop((x0, y0, x0 + fw, y0 + fh))
            if cermin:
                f = f.transpose(Image.FLIP_LEFT_RIGHT)
            dx, dy, _, _ = pd[nama]
            for y in range(fh):
                for x in range(fw):
                    p = f.getpixel((x, y))
                    if p[3]:
                        img.putpixel((dx + x, dy + y), p)

    # bersihkan lapisan topi/jaket/manset asal
    for (u, v, w, h, d) in ((32, 0, 8, 8, 8), (16, 32, 8, 12, 4), (48, 48, 4, 12, 4), (0, 32, 4, 12, 4), (0, 48, 4, 12, 4)):
        for nama, (x0, y0, fw, fh) in kotak_uv(u, v, w, h, d).items():
            for y in range(fh):
                for x in range(fw):
                    img.putpixel((x0 + x, y0 + y), KOSONG)
    salin(a1, 0, 0, 0, 0, 8, 8, 8)
    salin(a1, 32, 0, 32, 0, 8, 8, 8)
    salin(a2, 16, 16, 16, 16, 8, 12, 4)
    salin(a1, 16, 16, 16, 16, 8, 12, 4)
    salin(a1, 40, 16, 40, 16, 4, 12, 4)
    salin(a1, 40, 16, 32, 48, 4, 12, 4, True)
    for (u, v) in ((0, 16), (16, 48)):
        salin(a2, 0, 16, u, v, 4, 12, 4, u == 16)
        salin(a1, 0, 16, u, v, 4, 12, 4, u == 16)
    # rambut hitam iblis
    for y in range(64):
        for x in range(64):
            p = img.getpixel((x, y))
            if p[3] and p[:3] in {PALET[c][:3] for c in "Hhg"}:
                img.putpixel((x, y), ubah(PALET["D"], 1 + random.uniform(-0.15, 0.4)))
    return img


# ===========================================================================
# Utama
# ===========================================================================
def main():
    skin = skin_asta()
    a1, a2 = armor_1(), armor_2()
    sayap = elytra()

    # ---------------- skin pack ----------------
    simpan(skin, SKIN, "asta.png")
    simpan(skin_iblis(skin, a1, a2), SKIN, "asta_iblis.png")
    tulis_json(skin_pack_json(), SKIN, "skins.json")
    tulis_json(
        manifest("Asta (Black Clover)", "Skin Asta dari Black Clover", UUID["skin_header"], UUID["skin_module"], "skin_pack"),
        SKIN, "manifest.json",
    )
    tulis_teks(
        "skinpack.AstaBlackClover=Asta (Black Clover)\n"
        "skin.AstaBlackClover.asta=Asta\n"
        "skin.AstaBlackClover.asta_iblis=Asta (Mode Iblis)\n",
        SKIN, "texts", "en_US.lang",
    )
    tulis_json(["en_US"], SKIN, "texts", "languages.json")

    # ---------------- resource pack ----------------
    simpan(a1, RP, "textures", "models", "armor", "netherite_1.png")
    simpan(a2, RP, "textures", "models", "armor", "netherite_2.png")
    simpan(sayap, RP, "textures", "models", "armor", "elytra.png")
    for nama, baris in IKON_VANILLA.items():
        simpan(ikon_grid(baris), RP, "textures", "items", f"{nama}.png")

    tekstur_item = {}
    sprites = []
    teks_en = ["## Asta - Black Clover"]
    teks_id = ["## Asta - Black Clover"]
    for id_, buat, ingot, en, nama_id, dmg, dur in PEDANG:
        spr, W, L, hc = buat()
        outline(spr)
        sprites.append((spr, W, L, hc))
        simpan(spr, RP, "textures", "asta", "pedang", f"{id_}.png")
        simpan(ikon_pedang(spr, L), RP, "textures", "items", "asta", f"{id_}.png")
        tekstur_item[f"asta_{id_}"] = {"textures": f"textures/items/asta/{id_}"}
        tulis_json(geometri_json(id_, W, L, hc), RP, "models", "entity", f"asta_{id_}.geo.json")
        tulis_json(attachable_json(id_), RP, "attachables", f"asta_{id_}.json")
        teks_en.append(f"item.asta:{id_}.name={en}")
        teks_id.append(f"item.asta:{id_}.name={nama_id}")

        tulis_json(item_json(id_, dmg, dur), BP, "items", f"{id_}.json")
        tulis_json(resep_json(id_, ingot), BP, "recipes", f"{id_}.json")

    tulis_json(animasi_json(), RP, "animations", "asta_pedang.animation.json")
    tulis_json({"resource_pack_name": "asta", "texture_name": "atlas.items", "texture_data": tekstur_item},
               RP, "textures", "item_texture.json")
    tulis_teks("\n".join(teks_en) + "\n", RP, "texts", "en_US.lang")
    tulis_teks("\n".join(teks_id) + "\n", RP, "texts", "id_ID.lang")
    tulis_json(["en_US", "id_ID"], RP, "texts", "languages.json")
    tulis_json(
        manifest("Asta §cRP", "Armor iblis, elytra sayap iblis, dan 4 pedang Asta (Black Clover).",
                 UUID["rp_header"], UUID["rp_module"], "resources"),
        RP, "manifest.json",
    )
    tulis_json(
        manifest("Asta §cBP", "4 pedang iblis Asta: pedang apa saja + ingot di meja kerajinan.",
                 UUID["bp_header"], UUID["bp_module"], "data", UUID["rp_header"]),
        BP, "manifest.json",
    )
    ikon = ikon_pack(skin, a1)
    simpan(ikon, RP, "pack_icon.png")
    simpan(ikon, BP, "pack_icon.png")
    simpan(ikon_pack(skin, latar="#2b2b33"), SKIN, "pack_icon.png")

    # ---------------- dokumentasi ----------------
    simpan(pratinjau(skin, a1, a2, sayap, sprites), DOCS, "pratinjau.png")
    simpan(skin.resize((256, 256), Image.NEAREST), DOCS, "skin_asta_x4.png")
    lembar = Image.new("RGBA", (len(sprites) * 40, 40), hex2rgb("#e9e4dc"))
    for i, (id_, *_r) in enumerate(PEDANG):
        lembar.alpha_composite(Image.open(os.path.join(RP, "textures", "items", "asta", f"{id_}.png")), (i * 40 + 4, 4))
    simpan(lembar.resize((lembar.width * 4, lembar.height * 4), Image.NEAREST), DOCS, "ikon_pedang.png")
    print("Selesai.")


if __name__ == "__main__":
    main()
