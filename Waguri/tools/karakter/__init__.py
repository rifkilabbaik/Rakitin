"""Modul karakter. Urutan DAFTAR_MODUL menentukan nomor model (property waguri:model).

Setiap modul punya fungsi buat() -> list[inti.Model].
"""
import importlib

DAFTAR_MODUL = ["kaoruko", "subaru", "rintaro", "saku", "usami", "ayato"]


def semua_model():
    hasil = []
    for nama in DAFTAR_MODUL:
        hasil += importlib.import_module(f"karakter.{nama}").buat()
    return hasil
