"""Render pratinjau satu/semua karakter untuk ulasan.

Pemakaian (dari folder Waguri):
    python3 tools/pratinjau.py kaoruko          # satu karakter (id model / nama modul)
    python3 tools/pratinjau.py                  # semua
Hasil: docs/render/<id>.png (depan, 3/4, samping, belakang, 3/4 belakang, close-up wajah)
       + laporan teknis (jumlah kubus, ukuran tekstur, masalah).
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import inti  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def muat_modul(nama):
    return importlib.import_module(f"karakter.{nama}")


def render_modul(nama):
    mod = muat_modul(nama)
    hasil = []
    for m in mod.buat():
        geo, tex, info = inti.bangun(m)
        masalah = inti.periksa(m, geo, tex)
        out = os.path.join(ROOT, "docs", "render", f"{m.id}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        inti.lembar_render(m, tex, S=8).save(out)
        tex.save(os.path.join(ROOT, "docs", "render", f"{m.id}_tekstur.png"))
        print(f"{m.id}: {info['kubus']} kubus, tekstur {info['tekstur_unit']} unit -> {out}")
        for x in masalah:
            print("   MASALAH:", x)
        hasil.append((m, masalah))
    return hasil


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for n in sys.argv[1:]:
            render_modul(n)
    else:
        from karakter import DAFTAR_MODUL
        for n in DAFTAR_MODUL:
            render_modul(n)
