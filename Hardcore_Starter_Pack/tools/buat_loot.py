"""Generator loot table Hold to Enchant (Hardcore Starter Pack).

API script menolak enchant yang saling bentrok (mis. Sharpness + Smite, Infinity + Mending).
Untuk item yang punya enchant bentrok, script memakai loot table berfungsi `specific_enchants`
yang dibuat di sini: loot_tables/hsp/enchant/<item>[_fortune|_silk|_polos].json

Jalankan dari folder Hardcore_Starter_Pack:  python3 tools/buat_loot.py
"""

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "HardcoreStarterPack_BP", "loot_tables", "hsp", "enchant")

MAKS = {
    "sharpness": 5, "smite": 5, "bane_of_arthropods": 5, "knockback": 2, "fire_aspect": 2,
    "looting": 3, "unbreaking": 3, "mending": 1, "efficiency": 5, "fortune": 3, "silk_touch": 1,
    "density": 5, "breach": 4, "wind_burst": 3, "power": 5, "punch": 2, "flame": 1, "infinity": 1,
    "multishot": 1, "piercing": 4, "quick_charge": 3, "impaling": 5, "loyalty": 3, "riptide": 3,
    "channeling": 1, "protection": 4, "fire_protection": 4, "blast_protection": 4,
    "projectile_protection": 4, "respiration": 3, "aqua_affinity": 1, "thorns": 3, "swift_sneak": 3,
    "feather_falling": 4, "depth_strider": 3, "frost_walker": 2, "soul_speed": 3, "lunge": 3,
}

BAHAN = ["wooden", "stone", "copper", "iron", "golden", "diamond", "netherite"]
ARMOR = ["leather", "chainmail", "copper", "iron", "golden", "diamond", "netherite"]
PROT = ["protection", "fire_protection", "blast_protection", "projectile_protection"]
UMUM = ["unbreaking", "mending"]

# kategori: (daftar item, daftar enchant)
KATEGORI = {
    "pedang": ([f"{b}_sword" for b in BAHAN],
               ["sharpness", "smite", "bane_of_arthropods", "knockback", "fire_aspect", "looting"] + UMUM),
    "kapak": ([f"{b}_axe" for b in BAHAN],
              ["efficiency", "sharpness", "smite", "bane_of_arthropods"] + UMUM),
    "tombak": ([f"{b}_spear" for b in BAHAN],
               ["lunge", "sharpness", "smite", "bane_of_arthropods", "knockback", "fire_aspect", "looting"] + UMUM),
    "gada": (["mace"], ["density", "breach", "smite", "bane_of_arthropods", "wind_burst", "fire_aspect"] + UMUM),
    "busur": (["bow"], ["power", "punch", "flame", "infinity"] + UMUM),
    "busur_silang": (["crossbow"], ["multishot", "piercing", "quick_charge"] + UMUM),
    "trisula": (["trident"], ["impaling", "loyalty", "channeling", "riptide"] + UMUM),
    "helm": ([f"{b}_helmet" for b in ARMOR] + ["turtle_helmet"],
             PROT + ["respiration", "aqua_affinity", "thorns"] + UMUM),
    "zirah": ([f"{b}_chestplate" for b in ARMOR], PROT + ["thorns"] + UMUM),
    "celana": ([f"{b}_leggings" for b in ARMOR], PROT + ["swift_sneak", "thorns"] + UMUM),
    "sepatu": ([f"{b}_boots" for b in ARMOR],
               PROT + ["feather_falling", "depth_strider", "frost_walker", "soul_speed", "thorns"] + UMUM),
}

# Alat tambang punya varian sesuai pilihan Fortune / Silk Touch di /setting.
VARIAN_TAMBANG = {"fortune": ["fortune"], "silk": ["silk_touch"], "polos": []}


def tabel(item, enchant):
    return {
        "pools": [
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "item",
                        "name": f"minecraft:{item}",
                        "weight": 1,
                        "functions": [
                            {
                                "function": "specific_enchants",
                                "enchants": [{"id": e, "level": MAKS[e]} for e in enchant],
                            }
                        ],
                    }
                ],
            }
        ]
    }


def tulis(nama, data):
    with open(os.path.join(OUT, f"{nama}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".json"):
            os.remove(os.path.join(OUT, f))
    n = 0
    for kategori, (items, enchant) in KATEGORI.items():
        for item in items:
            if kategori == "kapak":
                for varian, tambahan in VARIAN_TAMBANG.items():
                    tulis(f"{item}_{varian}", tabel(item, enchant + tambahan))
                    n += 1
            else:
                tulis(item, tabel(item, enchant))
                n += 1
    print(f"{n} loot table dibuat di {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
