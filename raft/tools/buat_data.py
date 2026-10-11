"""Generator file JSON addon Rakitin (item, blok, resep, atlas tekstur, teks).

Jalankan dari root repo:  python3 tools/buat_data.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from data_rakitin import (  # noqa: E402
    BLOK_NAMA, ITEMS, NS, RESEP, RESEP_TUNGKU,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BP = os.path.join(ROOT, "Rakitin_BP")
RP = os.path.join(ROOT, "Rakitin_RP")

FORMAT_ITEM = "1.26.30"
FORMAT_BLOK = "1.26.20"
FORMAT_RESEP = "1.20.10"


def tulis(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------
def buat_item():
    for it in ITEMS:
        komp = {
            "minecraft:icon": f"{NS}_{it['id']}",
            "minecraft:display_name": {"value": f"item.{NS}:{it['id']}.name"},
            "minecraft:max_stack_size": it.get("stack", 64),
        }
        komp.update(it.get("komponen", {}))
        tulis(
            os.path.join(BP, "items", f"{it['id']}.json"),
            {
                "format_version": FORMAT_ITEM,
                "minecraft:item": {
                    "description": {
                        "identifier": f"{NS}:{it['id']}",
                        "menu_category": {"category": it["kategori"]},
                    },
                    "components": komp,
                },
            },
        )

    # Item untuk blok fondasi: menggantikan item bawaan blok supaya bisa
    # dipasang langsung di permukaan air lewat script.
    for blok in ("fondasi_rakit", "fondasi_kuat"):
        tulis(
            os.path.join(BP, "items", f"{blok}.json"),
            {
                "format_version": FORMAT_ITEM,
                "minecraft:item": {
                    "description": {
                        "identifier": f"{NS}:{blok}",
                        "menu_category": {"category": "construction"},
                    },
                    "components": {
                        "minecraft:block_placer": {
                            "block": f"{NS}:{blok}",
                            "replace_block_item": True,
                        },
                        "minecraft:display_name": {"value": f"tile.{NS}:{blok}.name"},
                        "rakit:fondasi_air": {},
                    },
                },
            },
        )


# ---------------------------------------------------------------------------
# Blok
# ---------------------------------------------------------------------------
def mat(tex, render="opaque", **extra):
    m = {"texture": f"{NS}_{tex}", "render_method": render}
    m.update(extra)
    return m


def rentang(lo, hi):
    """State blok berupa bilangan bulat lo..hi."""
    return {"values": {"min": lo, "max": hi}}


def blok_dasar(nama, komponen, states=None, permutasi=None, traits=None, kategori="construction"):
    desc = {
        "identifier": f"{NS}:{nama}",
        "menu_category": {"category": kategori},
    }
    if states:
        desc["states"] = states
    if traits:
        desc["traits"] = traits
    komp = {"minecraft:display_name": f"tile.{NS}:{nama}.name"}
    komp.update(komponen)
    isi = {"description": desc, "components": komp}
    if permutasi:
        isi["permutations"] = permutasi
    tulis(
        os.path.join(BP, "blocks", f"{nama}.json"),
        {"format_version": FORMAT_BLOK, "minecraft:block": isi},
    )


ROTASI = [
    ("north", 0),
    ("west", 90),
    ("south", 180),
    ("east", 270),
]


def permutasi_rotasi():
    return [
        {
            "condition": f"q.block_state('minecraft:cardinal_direction') == '{arah}'",
            "components": {"minecraft:transformation": {"rotation": [0, rot, 0]}},
        }
        for arah, rot in ROTASI
    ]


TRAIT_ARAH = {
    "minecraft:placement_direction": {
        "enabled_states": ["minecraft:cardinal_direction"],
        "y_rotation_offset": 180,
    }
}


def buat_blok():
    full = "minecraft:geometry.full_block"

    blok_dasar("fondasi_rakit", {
        "minecraft:geometry": full,
        "minecraft:material_instances": {"*": mat("fondasi_rakit")},
        "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.0},
        "minecraft:destructible_by_explosion": {"explosion_resistance": 3},
        "minecraft:flammable": {"catch_chance_modifier": 5, "destroy_chance_modifier": 20},
        "minecraft:map_color": "#a0794a",
    })

    blok_dasar("fondasi_kuat", {
        "minecraft:geometry": full,
        "minecraft:material_instances": {"*": mat("fondasi_kuat")},
        "minecraft:destructible_by_mining": {"seconds_to_destroy": 2.5},
        "minecraft:destructible_by_explosion": {"explosion_resistance": 12},
        "minecraft:map_color": "#7d6a55",
    })

    # Penyaring air: isi 0 = kosong, 1..3 = menyaring, 4 = air bersih siap.
    def mat_penyaring(atas):
        return {
            "*": mat("penyaring_samping"),
            "up": mat(atas),
            "down": mat("fondasi_rakit"),
        }

    blok_dasar(
        "penyaring_air",
        {
            "minecraft:geometry": full,
            "minecraft:material_instances": mat_penyaring("penyaring_atas_kosong"),
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.2},
            "minecraft:tick": {"interval_range": [200, 200], "looping": True},
            "rakit:penyaring": {},
        },
        states={"rakit:isi": rentang(0, 4)},
        permutasi=[
            {
                "condition": "q.block_state('rakit:isi') >= 1 && q.block_state('rakit:isi') <= 3",
                "components": {
                    "minecraft:geometry": full,
                    "minecraft:material_instances": mat_penyaring("penyaring_atas_proses"),
                },
            },
            {
                "condition": "q.block_state('rakit:isi') == 4",
                "components": {
                    "minecraft:geometry": full,
                    "minecraft:material_instances": mat_penyaring("penyaring_atas_siap"),
                    "minecraft:light_emission": 3,
                },
            },
        ],
    )

    # Penampung hujan: isi 0..4 (jumlah botol air bersih yang tersimpan).
    def mat_penampung(atas):
        return {
            "*": mat("penampung_samping"),
            "up": mat(atas),
            "down": mat("fondasi_rakit"),
        }

    blok_dasar(
        "penampung_hujan",
        {
            "minecraft:geometry": full,
            "minecraft:material_instances": mat_penampung("penampung_atas_kosong"),
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.2},
            "minecraft:tick": {"interval_range": [100, 100], "looping": True},
            "rakit:penampung": {},
        },
        states={"rakit:isi": rentang(0, 4)},
        permutasi=[
            {
                "condition": "q.block_state('rakit:isi') >= 1 && q.block_state('rakit:isi') <= 2",
                "components": {
                    "minecraft:geometry": full,
                    "minecraft:material_instances": mat_penampung("penampung_atas_sedikit"),
                },
            },
            {
                "condition": "q.block_state('rakit:isi') >= 3",
                "components": {
                    "minecraft:geometry": full,
                    "minecraft:material_instances": mat_penampung("penampung_atas_penuh"),
                },
            },
        ],
    )

    # Pot tanam: tahap 0 = kosong, 1 = bibit, 2 = tumbuh, 3 = siap panen.
    # jenis 0 = gandum, 1 = kentang, 2 = wortel, 3 = bit.
    geo_pot = {
        "identifier": "geometry.rakit.pot_tanam",
        "bone_visibility": {"tanaman": "q.block_state('rakit:tahap') > 0"},
    }

    def mat_pot(tanaman):
        return {
            "*": mat("pot_samping", "alpha_test"),
            "tanah": mat("pot_tanah", "alpha_test"),
            "tanaman": mat(tanaman, "alpha_test", face_dimming=False, ambient_occlusion=0),
        }

    perm_pot = [
        ("q.block_state('rakit:tahap') == 1", "tanaman_bibit"),
        ("q.block_state('rakit:tahap') == 2", "tanaman_tumbuh"),
        ("q.block_state('rakit:tahap') == 3 && q.block_state('rakit:jenis') == 0", "tanaman_gandum"),
        ("q.block_state('rakit:tahap') == 3 && q.block_state('rakit:jenis') == 1", "tanaman_kentang"),
        ("q.block_state('rakit:tahap') == 3 && q.block_state('rakit:jenis') == 2", "tanaman_wortel"),
        ("q.block_state('rakit:tahap') == 3 && q.block_state('rakit:jenis') == 3", "tanaman_bit"),
    ]
    blok_dasar(
        "pot_tanam",
        {
            "minecraft:geometry": geo_pot,
            "minecraft:material_instances": mat_pot("tanaman_bibit"),
            "minecraft:collision_box": {"origin": [-7, 0, -7], "size": [14, 8, 14]},
            "minecraft:selection_box": {"origin": [-7, 0, -7], "size": [14, 14, 14]},
            "minecraft:light_dampening": 0,
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.6},
            "minecraft:tick": {"interval_range": [500, 900], "looping": True},
            "rakit:pot": {},
        },
        states={"rakit:tahap": rentang(0, 3), "rakit:jenis": rentang(0, 3)},
        permutasi=[
            {
                "condition": kondisi,
                "components": {
                    "minecraft:geometry": geo_pot,
                    "minecraft:material_instances": mat_pot(tex),
                },
            }
            for kondisi, tex in perm_pot
        ],
    )

    blok_dasar(
        "layar",
        {
            "minecraft:geometry": "geometry.rakit.layar",
            "minecraft:material_instances": {
                "*": mat("layar_kain", "alpha_test"),
                "tiang": mat("layar_tiang", "alpha_test"),
            },
            "minecraft:collision_box": {"origin": [-1, 0, -1], "size": [2, 16, 2]},
            "minecraft:selection_box": {"origin": [-7, 0, -1], "size": [14, 16, 2]},
            "minecraft:light_dampening": 0,
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.8},
            "minecraft:flammable": {"catch_chance_modifier": 5, "destroy_chance_modifier": 20},
            "rakit:layar": {},
        },
        permutasi=permutasi_rotasi(),
        traits=TRAIT_ARAH,
    )

    blok_dasar(
        "kemudi",
        {
            "minecraft:geometry": "geometry.rakit.kemudi",
            "minecraft:material_instances": {"*": mat("kemudi", "alpha_test")},
            "minecraft:collision_box": {"origin": [-5, 0, -2], "size": [10, 16, 4]},
            "minecraft:selection_box": {"origin": [-5, 0, -2], "size": [10, 16, 4]},
            "minecraft:light_dampening": 0,
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.0},
            "rakit:kemudi": {},
        },
        permutasi=permutasi_rotasi(),
        traits=TRAIT_ARAH,
    )


# ---------------------------------------------------------------------------
# Geometri blok (resource pack)
# ---------------------------------------------------------------------------
def kubus(origin, size, material=None, uv0=(0, 0), **extra):
    """Kubus dengan UV per-sisi sederhana (setiap sisi memakai pojok tekstur)."""
    w, h, d = size
    u, v = uv0

    def sisi(a, b):
        f = {"uv": [u, v], "uv_size": [max(a, 1), max(b, 1)]}
        if material:
            f["material_instance"] = material
        return f

    c = {
        "origin": origin,
        "size": size,
        "uv": {
            "north": sisi(w, h), "south": sisi(w, h),
            "east": sisi(d, h), "west": sisi(d, h),
            "up": sisi(w, d), "down": sisi(w, d),
        },
    }
    c.update(extra)
    return c


def geometri(ident, bones):
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": ident,
                    "texture_width": 16,
                    "texture_height": 16,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2.5,
                    "visible_bounds_offset": [0, 0.75, 0],
                },
                "bones": bones,
            }
        ],
    }


def buat_geometri_blok():
    # Pot: badan pot + tanah di atas + dua bidang silang untuk tanaman.
    badan = kubus([-7, 0, -7], [14, 8, 14], uv0=(1, 1))
    badan["uv"]["up"] = {"uv": [1, 1], "uv_size": [14, 14], "material_instance": "tanah"}
    bidang = []
    for rot in (45, -45):
        bidang.append({
            "origin": [-7, 8, 0],
            "size": [14, 8, 0],
            "pivot": [0, 8, 0],
            "rotation": [0, rot, 0],
            "uv": {
                "north": {"uv": [1, 8], "uv_size": [14, 8], "material_instance": "tanaman"},
                "south": {"uv": [1, 8], "uv_size": [14, 8], "material_instance": "tanaman"},
            },
        })
    tulis(
        os.path.join(RP, "models", "blocks", "pot_tanam.geo.json"),
        geometri("geometry.rakit.pot_tanam", [
            {"name": "pot", "pivot": [0, 0, 0], "cubes": [badan]},
            {"name": "tanaman", "pivot": [0, 8, 0], "cubes": bidang},
        ]),
    )

    # Layar: tiang + palang bawah + kain layar.
    kain = {
        "origin": [-7, 3, -0.5],
        "size": [14, 12, 1],
        "uv": {
            "north": {"uv": [1, 2], "uv_size": [14, 12]},
            "south": {"uv": [1, 2], "uv_size": [14, 12]},
            "east": {"uv": [0, 2], "uv_size": [1, 12]},
            "west": {"uv": [15, 2], "uv_size": [1, 12]},
            "up": {"uv": [1, 1], "uv_size": [14, 1]},
            "down": {"uv": [1, 14], "uv_size": [14, 1]},
        },
    }
    tulis(
        os.path.join(RP, "models", "blocks", "layar.geo.json"),
        geometri("geometry.rakit.layar", [
            {
                "name": "tiang", "pivot": [0, 0, 0],
                "cubes": [
                    kubus([-1, 0, -1], [2, 16, 2], "tiang"),
                    kubus([-7, 2, -1], [14, 1, 2], "tiang"),
                ],
            },
            {"name": "kain", "pivot": [0, 0, 0], "cubes": [kain]},
        ]),
    )

    # Kemudi: tiang penyangga + roda kemudi berbentuk cincin dengan jari-jari.
    tulis(
        os.path.join(RP, "models", "blocks", "kemudi.geo.json"),
        geometri("geometry.rakit.kemudi", [
            {
                "name": "tiang", "pivot": [0, 0, 0],
                "cubes": [kubus([-1.5, 0, 0], [3, 7, 2], uv0=(0, 0))],
            },
            {
                "name": "roda", "pivot": [0, 10, 0],
                "cubes": [
                    kubus([-4, 14, -1], [8, 1, 1], uv0=(2, 2)),
                    kubus([-4, 5, -1], [8, 1, 1], uv0=(2, 4)),
                    kubus([-5, 6, -1], [1, 8, 1], uv0=(4, 6)),
                    kubus([4, 6, -1], [1, 8, 1], uv0=(6, 6)),
                    kubus([-4, 9.5, -1], [8, 1, 1], uv0=(2, 8)),
                    kubus([-0.5, 6, -1], [1, 8, 1], uv0=(8, 6)),
                    kubus([-1, 9, -1.5], [2, 2, 2], uv0=(10, 10)),
                    kubus([-0.5, 15, -1], [1, 1, 1], uv0=(12, 12)),
                    kubus([-0.5, 4, -1], [1, 1, 1], uv0=(12, 13)),
                    kubus([-6, 9.5, -1], [1, 1, 1], uv0=(13, 12)),
                    kubus([5, 9.5, -1], [1, 1, 1], uv0=(14, 12)),
                ],
            },
        ]),
    )


# ---------------------------------------------------------------------------
# Resep
# ---------------------------------------------------------------------------
def masukan(item_id):
    if item_id.startswith("tag:"):
        return {"tag": item_id[4:]}
    return {"item": item_id}


def buat_resep():
    for r in RESEP:
        ident = f"{NS}:{r['id']}"
        hasil = {"item": r["hasil"], "count": r["jumlah"]}
        unlock = {"context": "AlwaysUnlocked"}
        if r["tipe"] == "shaped":
            isi = {
                "format_version": FORMAT_RESEP,
                "minecraft:recipe_shaped": {
                    "description": {"identifier": ident},
                    "tags": ["crafting_table"],
                    "pattern": r["pola"],
                    "key": {k: masukan(v) for k, v in r["kunci"].items()},
                    "unlock": unlock,
                    "result": hasil,
                },
            }
        else:
            isi = {
                "format_version": FORMAT_RESEP,
                "minecraft:recipe_shapeless": {
                    "description": {"identifier": ident},
                    "tags": ["crafting_table"],
                    "ingredients": [masukan(b) for b in r["bahan"]],
                    "unlock": unlock,
                    "result": hasil,
                },
            }
        tulis(os.path.join(BP, "recipes", f"{r['id']}.json"), isi)

    for r in RESEP_TUNGKU:
        tulis(
            os.path.join(BP, "recipes", f"{r['id']}.json"),
            {
                "format_version": FORMAT_RESEP,
                "minecraft:recipe_furnace": {
                    "description": {"identifier": f"{NS}:{r['id']}"},
                    "unlock": [{"item": r["masuk"]}],
                    "tags": r["tag"],
                    "input": r["masuk"],
                    "output": r["hasil"],
                },
            },
        )


# ---------------------------------------------------------------------------
# Resource pack: atlas tekstur, suara blok, teks
# ---------------------------------------------------------------------------
TEKSTUR_BLOK = [
    "fondasi_rakit", "fondasi_kuat",
    "penyaring_samping", "penyaring_atas_kosong", "penyaring_atas_proses", "penyaring_atas_siap",
    "penampung_samping", "penampung_atas_kosong", "penampung_atas_sedikit", "penampung_atas_penuh",
    "pot_samping", "pot_tanah",
    "tanaman_bibit", "tanaman_tumbuh", "tanaman_gandum", "tanaman_kentang", "tanaman_wortel", "tanaman_bit",
    "layar_kain", "layar_tiang", "kemudi",
]


def buat_rp():
    tulis(
        os.path.join(RP, "textures", "item_texture.json"),
        {
            "resource_pack_name": "rakitin",
            "texture_name": "atlas.items",
            "texture_data": {
                f"{NS}_{it['id']}": {"textures": f"textures/items/{it['id']}"} for it in ITEMS
            },
        },
    )
    tulis(
        os.path.join(RP, "textures", "terrain_texture.json"),
        {
            "resource_pack_name": "rakitin",
            "texture_name": "atlas.terrain",
            "padding": 8,
            "num_mip_levels": 4,
            "texture_data": {
                f"{NS}_{t}": {"textures": f"textures/blocks/{t}"} for t in TEKSTUR_BLOK
            },
        },
    )
    suara = {
        "fondasi_rakit": "wood", "fondasi_kuat": "metal", "penyaring_air": "wood",
        "penampung_hujan": "wood", "pot_tanam": "wood", "layar": "cloth", "kemudi": "wood",
    }
    blocks = {"format_version": [1, 1, 0]}
    for b, s in suara.items():
        blocks[f"{NS}:{b}"] = {"sound": s}
    tulis(os.path.join(RP, "blocks.json"), blocks)

    baris = ["## Rakitin - teks bahasa Indonesia", ""]
    baris.append("pack.name=Rakitin")
    baris.append("pack.description=Bertahan hidup di lautan dengan rakit.")
    baris.append("")
    for it in ITEMS:
        baris.append(f"item.{NS}:{it['id']}.name={it['nama']}")
    for b, n in BLOK_NAMA.items():
        baris.append(f"tile.{NS}:{b}.name={n}")
    baris += [
        f"entity.{NS}:hiu.name=Hiu",
        f"item.spawn_egg.entity.{NS}:hiu.name=Telur Muncul Hiu",
        f"entity.{NS}:puing.name=Puing Hanyut",
        f"item.spawn_egg.entity.{NS}:puing.name=Telur Muncul Puing",
        "",
    ]
    teks = "\n".join(baris)
    for lang in ("id_ID", "en_US"):
        with open(os.path.join(RP, "texts", f"{lang}.lang"), "w", encoding="utf-8") as f:
            f.write(teks)
    tulis(os.path.join(RP, "texts", "languages.json"), ["id_ID", "en_US"])


def main():
    buat_item()
    buat_blok()
    buat_geometri_blok()
    buat_resep()
    buat_rp()
    print("Data addon selesai dibuat.")


if __name__ == "__main__":
    main()
