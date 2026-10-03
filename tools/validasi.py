"""Validasi file JSON addon terhadap skema resmi Mojang (repo bedrock-samples).

Pemakaian:
    git clone --depth 1 https://github.com/Mojang/bedrock-samples.git /tmp/bedrock-samples
    python3 tools/validasi.py /tmp/bedrock-samples/metadata/json_schemas

Butuh paket: pip install jsonschema
"""

import glob
import json
import os
import sys
from urllib.parse import unquote

from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def muat_registry(dir_skema):
    def ambil(uri):
        path = os.path.join(dir_skema, unquote(uri).lstrip("/"))
        with open(path, encoding="utf-8") as f:
            return Resource.from_contents(json.load(f))

    return Registry(retrieve=ambil)


def validator(dir_skema, rel):
    with open(os.path.join(dir_skema, rel), encoding="utf-8") as f:
        skema = json.load(f)
    return Draft7Validator(skema, registry=muat_registry(dir_skema))


def ambigu(e):
    """True jika galat hanya karena oneOf ambigu di skema (filter cocok >1 cabang).

    Skema resmi memakai oneOf untuk filter entity; filter yang valid sering
    cocok dengan dua cabang sekaligus sehingga ditolak padahal benar.
    """
    for c in e.context or []:
        if "is valid under each of" in c.message or ambigu(c):
            return True
    return False


def cek(v, files, kunci):
    gagal = 0
    for path in sorted(files):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        isi = data[kunci]
        galat = [e for e in v.iter_errors(isi) if not ambigu(e)]
        galat.sort(key=lambda e: list(e.path))
        nama = os.path.relpath(path, ROOT)
        if galat:
            gagal += 1
            print(f"GAGAL {nama}")
            for e in galat[:10]:
                lokasi = "/".join(str(p) for p in e.absolute_path)
                print(f"   - {lokasi}: {e.message[:300]}")
        else:
            print(f"ok    {nama}")
    return gagal


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    dir_skema = os.path.abspath(sys.argv[1])
    bp = os.path.join(ROOT, "Rakitin_BP")
    gagal = 0
    gagal += cek(
        validator(dir_skema, "server/block/1.26.20/Blocks.json"),
        glob.glob(os.path.join(bp, "blocks", "*.json")),
        "minecraft:block",
    )
    gagal += cek(
        validator(dir_skema, "server/item/1.26.30/ItemDocument.json"),
        glob.glob(os.path.join(bp, "items", "*.json")),
        "minecraft:item",
    )
    gagal += cek(
        validator(dir_skema, "server/entity/1.26.50/ActorDocument.json"),
        glob.glob(os.path.join(bp, "entities", "*.json")),
        "minecraft:entity",
    )
    print()
    print("SEMUA VALID" if gagal == 0 else f"{gagal} file tidak valid")
    sys.exit(1 if gagal else 0)


if __name__ == "__main__":
    main()
