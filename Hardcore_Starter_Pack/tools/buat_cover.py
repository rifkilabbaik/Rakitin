"""Generator cover & ikon pack Hardcore Starter Pack (pixel art prosedural, tanpa aset Mojang).

Menghasilkan:
  docs/cover.png                              1280x720 (cover addon / README)
  HardcoreStarterPack_BP/pack_icon.png        256x256
  HardcoreStarterPack_RP/pack_icon.png        256x256

Jalankan dari folder Hardcore_Starter_Pack:  python3 tools/buat_cover.py   (butuh: pip install pillow)
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
random.seed(1337)

FONT_TEBAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BIASA = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, ukuran):
    try:
        return ImageFont.truetype(path, ukuran)
    except OSError:
        return ImageFont.load_default()


def rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ubah(c, f):
    return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))), max(0, min(255, int(c[2] * f))), c[3])


# ---------------------------------------------------------------------------
# Tekstur blok 16x16 (dibuat sendiri)
# ---------------------------------------------------------------------------
def tekstur_batu(dasar="#7a7a7a"):
    img = Image.new("RGBA", (16, 16))
    b = rgb(dasar)
    for y in range(16):
        for x in range(16):
            f = 1 + random.uniform(-0.12, 0.12)
            if random.random() < 0.08:
                f -= 0.18
            img.putpixel((x, y), ubah(b, f))
    return img


def tekstur_ore(warna, dasar="#7a7a7a"):
    img = tekstur_batu(dasar)
    c = rgb(warna)
    for _ in range(5):
        cx, cy = random.randint(2, 13), random.randint(2, 13)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (-1, 1)):
            if random.random() < 0.85:
                x, y = cx + dx, cy + dy
                if 0 <= x < 16 and 0 <= y < 16:
                    img.putpixel((x, y), ubah(c, 1 + random.uniform(-0.15, 0.2)))
    return img


# ---------------------------------------------------------------------------
# Ikon 32x32 (dibuat sendiri)
# ---------------------------------------------------------------------------
def garis_tebal(img, titik, lebar, warna):
    d = ImageDraw.Draw(img)
    d.line(titik, fill=warna, width=lebar, joint="curve")
    r = lebar / 2 - 0.5
    for x, y in (titik[0], titik[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=warna)


def outline(img, warna=(20, 16, 12, 255)):
    alpha = img.split()[3]
    tebal = alpha.filter(ImageFilter.MaxFilter(3))
    dasar = Image.new("RGBA", img.size, warna)
    hasil = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hasil.paste(dasar, mask=tebal)
    hasil.alpha_composite(img)
    return hasil


def gagang(img, a=(7, 26), b=(20, 13)):
    garis_tebal(img, [a, b], 3, rgb("#7a4f26"))
    garis_tebal(img, [(a[0] + 1, a[1] - 1), (b[0] + 1, b[1] - 1)], 1, rgb("#a8743d"))


def ikon_beliung(warna="#4fe3e1"):
    img = Image.new("RGBA", (32, 32))
    gagang(img)
    pusat = (21, 11)
    titik = []
    for i in range(-10, 11):
        t = i / 10
        x = pusat[0] + t * 9 - (t * t) * 4
        y = pusat[1] + t * 9 + (t * t) * 4 - 4
        titik.append((x, y))
    garis_tebal(img, titik, 4, rgb(warna))
    garis_tebal(img, titik[3:-3], 1, ubah(rgb(warna), 1.35))
    return outline(img)


def ikon_kapak(warna="#d9a520"):
    img = Image.new("RGBA", (32, 32))
    gagang(img, (7, 26), (22, 11))
    ImageDraw.Draw(img).polygon([(17, 8), (23, 3), (28, 8), (27, 15), (22, 16)], fill=rgb(warna))
    ImageDraw.Draw(img).line([(21, 6), (26, 10)], fill=ubah(rgb(warna), 1.3), width=1)
    return outline(img)


def ikon_cangkul(warna="#b8bec4"):
    img = Image.new("RGBA", (32, 32))
    gagang(img, (7, 26), (22, 11))
    ImageDraw.Draw(img).polygon([(17, 7), (23, 5), (25, 8), (19, 10)], fill=rgb(warna))
    ImageDraw.Draw(img).polygon([(22, 6), (27, 3), (28, 6), (24, 9)], fill=ubah(rgb(warna), 0.85))
    return outline(img)


def ikon_obor():
    img = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(img)
    d.rectangle([14, 13, 17, 29], fill=rgb("#7a4f26"))
    d.rectangle([15, 13, 15, 29], fill=rgb("#a8743d"))
    d.ellipse([11, 3, 20, 14], fill=rgb("#f28c28"))
    d.ellipse([13, 6, 18, 13], fill=rgb("#ffd54a"))
    d.ellipse([14, 9, 17, 13], fill=rgb("#fff4b0"))
    return outline(img)


def ikon_kompas():
    img = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(img)
    d.ellipse([3, 3, 28, 28], fill=rgb("#8c8f94"))
    d.ellipse([6, 6, 25, 25], fill=rgb("#dfe6ea"))
    d.polygon([(16, 7), (19, 16), (16, 16)], fill=rgb("#d32f2f"))
    d.polygon([(16, 7), (13, 16), (16, 16)], fill=rgb("#ff5252"))
    d.polygon([(16, 25), (13, 16), (19, 16)], fill=rgb("#5c6670"))
    d.ellipse([14, 14, 17, 17], fill=rgb("#2b2b2b"))
    return outline(img)


def ikon_buku():
    img = Image.new("RGBA", (32, 32))
    d = ImageDraw.Draw(img)
    d.polygon([(6, 8), (22, 4), (26, 22), (10, 27)], fill=rgb("#5b2a86"))
    d.polygon([(8, 9), (22, 5), (25, 21), (11, 25)], fill=rgb("#7b3fb0"))
    d.line([(9, 26), (25, 22)], fill=rgb("#efe6c8"), width=2)
    for x, y in ((14, 10), (19, 14), (15, 19), (20, 9)):
        d.point((x, y), fill=rgb("#f3d9ff"))
    return outline(img)


def besar(img, skala):
    return img.resize((img.width * skala, img.height * skala), Image.NEAREST)


# ---------------------------------------------------------------------------
# Latar gua penuh ore
# ---------------------------------------------------------------------------
ORE = ["#4fe3e1", "#fcee4b", "#17dd62", "#d8af93", "#ff2a2a", "#2f5bff", "#e0734a"]


def latar_gua(w, h, ukuran_blok, peluang_ore=0.18):
    img = Image.new("RGBA", (w, h))
    for by in range(0, h, ukuran_blok):
        for bx in range(0, w, ukuran_blok):
            dasar = "#5c5c63" if (by // ukuran_blok) * 7 + bx // ukuran_blok > 60 and random.random() < 0.5 else "#7a7a7a"
            t = tekstur_ore(random.choice(ORE), dasar) if random.random() < peluang_ore else tekstur_batu(dasar)
            img.paste(t.resize((ukuran_blok, ukuran_blok), Image.NEAREST), (bx, by))
    # Gelapkan (gua) dan beri vinyet radial supaya teks menonjol.
    kecil = Image.new("L", (64, 36))
    for y in range(36):
        for x in range(64):
            r = math.hypot((x - 31.5) / 32, (y - 17.5) / 18)
            kecil.putpixel((x, y), int(255 * min(1, 0.35 + 0.65 * r ** 1.8)))
    topeng = kecil.resize((w, h), Image.BILINEAR)
    hitam = Image.new("RGBA", (w, h), (6, 6, 10, 255))
    img = Image.composite(hitam, img, topeng.point(lambda v: int(v * 0.85)))
    return img


def teks_berkontur(d, posisi, teks, f, isi, kontur=(25, 16, 8, 255), tebal=6, bayangan=True):
    x, y = posisi
    if bayangan:
        d.text((x + 8, y + 10), teks, font=f, fill=(0, 0, 0, 160), stroke_width=tebal, stroke_fill=(0, 0, 0, 160))
    d.text((x, y), teks, font=f, fill=isi, stroke_width=tebal, stroke_fill=kontur)


def tengah(d, teks, f, lebar, tebal=0):
    b = d.textbbox((0, 0), teks, font=f, stroke_width=tebal)
    return (lebar - (b[2] - b[0])) // 2 - b[0]


def gradien_teks(ukuran, teks, f, atas, bawah, tebal=7):
    """Teks dengan isi gradien emas dan kontur gelap."""
    w, h = ukuran
    topeng = Image.new("L", (w, h), 0)
    dm = ImageDraw.Draw(topeng)
    x = tengah(dm, teks, f, w, tebal)
    dm.text((x, 0), teks, font=f, fill=255)
    grad = Image.new("RGBA", (w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(atas[i] + (bawah[i] - atas[i]) * t) for i in range(3)) + (255,)
        ImageDraw.Draw(grad).line([(0, y), (w, y)], fill=c)
    lapis = Image.new("RGBA", (w, h))
    dl = ImageDraw.Draw(lapis)
    dl.text((x + 8, 10), teks, font=f, fill=(0, 0, 0, 170), stroke_width=tebal, stroke_fill=(0, 0, 0, 170))
    dl.text((x, 0), teks, font=f, fill=(0, 0, 0, 0), stroke_width=tebal, stroke_fill=(30, 18, 6, 255))
    lapis.paste(grad, mask=topeng)
    return lapis


def cover():
    W, H = 1280, 720
    img = latar_gua(W, H, 80)
    d = ImageDraw.Draw(img)

    # panel judul
    panel = Image.new("RGBA", (W, H))
    ImageDraw.Draw(panel).rounded_rectangle([110, 70, W - 110, 400], 28, fill=(10, 10, 16, 175))
    img.alpha_composite(panel)

    judul = gradien_teks((W, 170), "HARDCORE", font(FONT_TEBAL, 150), (255, 232, 120), (230, 120, 20))
    img.alpha_composite(judul, (0, 90))
    sub = gradien_teks((W, 110), "STARTER PACK", font(FONT_TEBAL, 92), (180, 250, 255), (40, 170, 220))
    img.alpha_composite(sub, (0, 262))

    # deretan ikon alat
    ikon = [ikon_beliung(), ikon_kapak(), ikon_cangkul(), ikon_obor(), ikon_kompas(), ikon_buku()]
    nama = ["Vein Miner", "Tree Capitator", "Crop Capitator", "Ore Detector", "Compass Finder", "Hold to Enchant"]
    ukuran = 128
    jarak_ikon = 176
    x0 = (W - (len(ikon) * jarak_ikon - (jarak_ikon - ukuran))) // 2
    f_label = font(FONT_TEBAL, 16)
    for i, (ik, n) in enumerate(zip(ikon, nama)):
        x = x0 + i * jarak_ikon
        y = 430
        kartu = Image.new("RGBA", (W, H))
        ImageDraw.Draw(kartu).rounded_rectangle([x - 14, y - 12, x + ukuran + 14, y + ukuran + 46], 18, fill=(12, 12, 18, 200), outline=(255, 210, 90, 255), width=3)
        img.alpha_composite(kartu)
        img.alpha_composite(besar(ik, 4), (x, y))
        lx = x + (ukuran - d.textbbox((0, 0), n, font=f_label)[2]) // 2
        d.text((lx, y + ukuran + 10), n, font=f_label, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))

    # pita bawah
    pita = "Auto Smelt  •  3x3x3 Mining  •  Offhand  •  /setting"
    f_pita = font(FONT_TEBAL, 26)
    d.text((tengah(d, pita, f_pita, W, 3), 655), pita, font=f_pita, fill=(255, 236, 160, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
    label = "Minecraft Bedrock 1.26"
    f_lbl = font(FONT_TEBAL, 22)
    d.text((W - 330, 26), label, font=f_lbl, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
    return img.convert("RGB")


def ikon_pack():
    S = 256
    img = latar_gua(S, S, 32, peluang_ore=0.3)
    cahaya = Image.new("RGBA", (S, S))
    ImageDraw.Draw(cahaya).ellipse([30, 30, 226, 226], fill=(255, 200, 80, 90))
    img.alpha_composite(cahaya.filter(ImageFilter.GaussianBlur(24)))
    kapak = besar(ikon_kapak(), 6).transpose(Image.FLIP_LEFT_RIGHT)
    beliung = besar(ikon_beliung(), 6)
    img.alpha_composite(kapak, (32, 32))
    img.alpha_composite(beliung, (32, 32))
    d = ImageDraw.Draw(img)
    f = font(FONT_TEBAL, 54)
    teks = "HSP"
    d.text((tengah(d, teks, f, S, 6), 176), teks, font=f, fill=(255, 226, 110, 255), stroke_width=6, stroke_fill=(30, 18, 6, 255))
    return img


def main():
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    cover().save(os.path.join(ROOT, "docs", "cover.png"), optimize=True)
    ik = ikon_pack()
    for pack in ("HardcoreStarterPack_BP", "HardcoreStarterPack_RP"):
        ik.save(os.path.join(ROOT, pack, "pack_icon.png"), optimize=True)
    print("Cover & ikon pack selesai dibuat.")


if __name__ == "__main__":
    main()
