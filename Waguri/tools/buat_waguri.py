"""Generator addon "Waguri YSM" untuk Minecraft Bedrock.

Konsep: meniru mod Java *Yes Steve Model* (YSM), yaitu mengganti tubuh pemain
dengan model 3D bergaya anime yang detail dan bisa dipilih tiap pemain.
Bedrock tidak bisa memakai mod, jadi addon ini:

  * menimpa entitas pemain (BP player.json) untuk menambah property
    `waguri:model` (model terpilih) dan `waguri:emote` (emote yang diputar);
  * menimpa client entity pemain (RP player.entity.json): bila model > 0,
    render controller skin vanilla dimatikan dan geometri model digambar.
    Tulang utama memakai nama & pivot yang sama dengan skin vanilla sehingga
    SEMUA animasi vanilla tetap jalan;
  * menambah animasi khas YSM: kedip, ekspresi, siku & lutut menekuk, rambut /
    ekor kuda / rok / pita bergoyang (fisika sederhana), napas, skala tinggi
    badan per karakter, dan emote.

Model dibangun oleh modul di tools/karakter/ memakai kerangka tools/inti.py.
Karakter dari *Kaoru Hana wa Rin to Saku* (Saka Mikami / Kodansha).

Jalankan dari folder Waguri:  python3 tools/buat_waguri.py
Butuh paket: pip install pillow numpy
"""

import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import inti  # noqa: E402
from inti import KOSONG, rgb  # noqa: E402
from karakter import semua_model  # noqa: E402

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


# ===========================================================================
# Emote & animasi
# ===========================================================================
EMOTE = [
    # (id property, kunci animasi, nama tombol, lama dalam tick)
    (1, "lambai", "Melambai", 70),
    (2, "ojigi", "Membungkuk (ojigi)", 60),
    (3, "kue", "Makan kue", 90),
    (4, "senang", "Lompat senang", 70),
    (5, "damai", "Pose damai (V)", 80),
    (6, "duduk", "Duduk", 400),
]

MODEL_AKTIF = "q.property('waguri:model') > 0"
SEDANG_EMOTE = "q.property('waguri:emote') > 0"
KECEPATAN = "math.clamp(q.modified_move_speed, 0, 1)"
WAKTU = "q.life_time"
# kompensasi tunduk/menengadah kepala supaya rambut tetap menjuntai
KOMPENSASI_KEPALA = "math.clamp(q.target_x_rotation, -40, 50) * 0.75"
TANGAN_KANAN_KOSONG = "(q.get_equipped_item_name(0, 1) == '')"
TANGAN_KIRI_KOSONG = "(q.get_equipped_item_name('off_hand') == '')"


def ekspresi_skala(models):
    """Molang: skala tinggi badan sesuai karakter (property waguri:model)."""
    e = "1.0"
    for i, m in reversed(list(enumerate(models, start=1))):
        e = f"(q.property('waguri:model') == {i} ? {m.skala} : {e})"
    return e


def animasi_json(models):
    v = KECEPATAN
    t = WAKTU
    ayun = "math.abs(variable.tcos0)"
    return {
        "format_version": "1.10.0",
        "animations": {
            "animation.waguri.skala": {
                "loop": True,
                "bones": {"root": {"scale": ekspresi_skala(models)}},
            },
            # wajah: kedip berkala & ekspresi senang saat emote tertentu
            "animation.waguri.wajah": {
                "loop": True,
                "bones": {
                    "kelopak": {"scale": f"(math.mod({t} + q.property('waguri:model') * 0.37, 3.7) < 0.12 && q.property('waguri:emote') != 1 && q.property('waguri:emote') != 4) ? 1 : 0"},
                    "ekspresi_senang": {"scale": "(q.property('waguri:emote') == 1 || q.property('waguri:emote') == 4) ? 1 : 0"},
                    "alis": {"position": [0, "q.property('waguri:emote') == 4 ? 0.35 : 0", 0]},
                },
            },
            # fisika sederhana: rambut, ekor kuda, rok, pita, tudung
            "animation.waguri.fisika": {
                "loop": True,
                "bones": {
                    "rambut_belakang": {"rotation": [
                        f"math.clamp({v} * 38, 0, 26) + math.sin({t} * 90) * 1.6 - {KOMPENSASI_KEPALA}",
                        0, f"math.sin({t} * 70) * 1.2"]},
                    "rambut_belakang2": {"rotation": [
                        f"math.clamp({v} * 22, 0, 16) + math.sin({t} * 90 - 50) * 2.4", 0,
                        f"math.sin({t} * 70 - 40) * 1.8"]},
                    "rambut_kanan": {"rotation": [
                        f"math.clamp({v} * 30, 0, 20) + math.sin({t} * 85) * 1.5 - {KOMPENSASI_KEPALA} * 0.6",
                        0, f"2 + math.sin({t} * 75) * 1.5"]},
                    "rambut_kiri": {"rotation": [
                        f"math.clamp({v} * 30, 0, 20) + math.sin({t} * 85 + 30) * 1.5 - {KOMPENSASI_KEPALA} * 0.6",
                        0, f"-2 - math.sin({t} * 75 + 30) * 1.5"]},
                    "ahoge": {"rotation": [f"math.sin({t} * 260) * (4 + {v} * 10)", 0, f"math.sin({t} * 150) * 5"]},
                    "ekor_kuda": {"rotation": [
                        f"math.clamp({v} * 45, 0, 38) + math.sin({t} * 100) * 3 - {KOMPENSASI_KEPALA}",
                        0, f"math.sin({t} * 60) * 5 + variable.tcos0 * 0.18"]},
                    "ekor_kuda2": {"rotation": [
                        f"math.clamp({v} * 25, 0, 20) + math.sin({t} * 100 - 60) * 4", 0,
                        f"math.sin({t} * 60 - 50) * 6"]},
                    "pita": {"rotation": [f"math.clamp({v} * 12, 0, 10) + math.sin({t} * 130) * 2", 0,
                                          f"math.sin({t} * 90) * 4"]},
                    "jubah": {"rotation": [f"math.clamp({v} * 35, 0, 30) + math.sin({t} * 95) * 2", 0, 0]},
                    "rok": {"rotation": [0, 0, f"math.sin({t} * 110) * 1.2 * {v}"]},
                    "rok_depan": {"rotation": [f"-{ayun} * 0.22 - {v} * 6", 0, 0]},
                    "rok_belakang": {"rotation": [f"{ayun} * 0.22 + {v} * 14 + math.sin({t} * 160) * {v} * 3", 0, 0]},
                    "rok_kanan": {"rotation": [0, 0, f"{ayun} * 0.12 + {v} * 4"]},
                    "rok_kiri": {"rotation": [0, 0, f"-{ayun} * 0.12 - {v} * 4"]},
                    # napas halus
                    "body": {"scale": [1, f"1 + math.sin({t} * 120) * 0.008", 1]},
                },
            },
            # siku & lutut menekuk mengikuti langkah (hanya bila tangan kosong)
            "animation.waguri.sendi": {
                "loop": True,
                "bones": {
                    "rightForearm": {"rotation": [f"{TANGAN_KANAN_KOSONG} ? (-6 - {ayun} * 0.45 - {v} * 18) : 0", 0, 0]},
                    "leftForearm": {"rotation": [f"{TANGAN_KIRI_KOSONG} ? (-6 - {ayun} * 0.45 - {v} * 18) : 0", 0, 0]},
                    "rightShin": {"rotation": [f"math.max(0, variable.tcos0) * 0.75 + {v} * 6 + (q.is_sneaking ? 18 : 0)", 0, 0]},
                    "leftShin": {"rotation": [f"math.max(0, -variable.tcos0) * 0.75 + {v} * 6 + (q.is_sneaking ? 18 : 0)", 0, 0]},
                },
            },
            "animation.waguri.emote.lambai": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "rightArm": {"rotation": [-165, 0, f"math.sin({t} * 540) * 20"]},
                    "rightForearm": {"rotation": [-15, 0, 0]},
                    "head": {"rotation": [0, 0, f"math.sin({t} * 270) * 4"]},
                },
            },
            "animation.waguri.emote.ojigi": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "waist": {"rotation": ["math.min(q.anim_time * 160, 40)", 0, 0]},
                    "rightArm": {"rotation": [-12, 0, -6]},
                    "leftArm": {"rotation": [-12, 0, 6]},
                    "rightForearm": {"rotation": [-25, 0, 0]},
                    "leftForearm": {"rotation": [-25, 0, 0]},
                },
            },
            "animation.waguri.emote.kue": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "rightArm": {"rotation": [f"-70 + math.sin({t} * 600) * 6", 25, 0]},
                    "rightForearm": {"rotation": ["-75", 0, 0]},
                    "leftArm": {"rotation": [-35, -15, 0]},
                    "leftForearm": {"rotation": [-45, 0, 0]},
                    "head": {"rotation": [8, 0, f"math.sin({t} * 200) * 5"]},
                },
            },
            "animation.waguri.emote.senang": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "root": {"position": [0, f"math.abs(math.sin({t} * 360)) * 2.5", 0]},
                    "rightArm": {"rotation": [0, 0, f"130 + math.sin({t} * 720) * 10"]},
                    "leftArm": {"rotation": [0, 0, f"-130 - math.sin({t} * 720) * 10"]},
                },
            },
            "animation.waguri.emote.damai": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "rightArm": {"rotation": [-60, 20, 15]},
                    "rightForearm": {"rotation": [-95, 0, 0]},
                    "head": {"rotation": [0, 0, f"8 + math.sin({t} * 120) * 2"]},
                    "waist": {"rotation": [0, 0, -4]},
                },
            },
            "animation.waguri.emote.duduk": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {
                    "root": {"position": [0, -10, 0]},
                    "rightLeg": {"rotation": [-80, 8, 0]},
                    "leftLeg": {"rotation": [-80, -8, 0]},
                    "rightShin": {"rotation": [10, 0, 0]},
                    "leftShin": {"rotation": [10, 0, 0]},
                    "rightArm": {"rotation": [-25, 0, -10]},
                    "leftArm": {"rotation": [-25, 0, 10]},
                    "rightForearm": {"rotation": [-30, 0, 0]},
                    "leftForearm": {"rotation": [-30, 0, 0]},
                    "rok_depan": {"rotation": [-75, 0, 0]},
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
        desc["textures"][f"waguri_{m.id}"] = f"textures/entity/waguri/{m.id}"
    nama_anim = ["skala", "wajah", "fisika", "sendi"] + [f"emote.{k}" for _i, k, _n, _l in EMOTE]
    desc["animations"].update({f"waguri.{n}": f"animation.waguri.{n}" for n in nama_anim})
    orang_ketiga = f"{MODEL_AKTIF} && !variable.is_first_person"
    desc["scripts"]["animate"] += [
        {"waguri.skala": orang_ketiga},
        {"waguri.wajah": MODEL_AKTIF},
        {"waguri.fisika": orang_ketiga},
        {"waguri.sendi": f"{orang_ketiga} && !{SEDANG_EMOTE}"},
    ] + [
        {f"waguri.emote.{k}": f"{orang_ketiga} && q.property('waguri:emote') == {i}"}
        for i, k, _n, _l in EMOTE
    ]
    vanilla_mati = "q.property('waguri:model') == 0"
    rc = []
    for item in desc["render_controllers"]:
        (nama, syarat), = item.items()
        if nama in ("controller.render.player.first_person", "controller.render.player.third_person"):
            syarat = f"({syarat}) && {vanilla_mati}"
        rc.append({nama: syarat})
    rc += [
        {"controller.render.waguri.first_person": f"variable.is_first_person && !query.is_spectator && {MODEL_AKTIF}"},
        {"controller.render.waguri.third_person": f"!variable.is_first_person && !variable.map_face_icon && !query.is_spectator && {MODEL_AKTIF}"},
    ]
    desc["render_controllers"] = rc
    return d


def render_controller_json(models):
    with open(os.path.join(VANILLA, "player.render_controllers.json"), encoding="utf-8") as f:
        v = json.load(f)["render_controllers"]
    fp = []
    # visibilitas tangan orang pertama sama dengan vanilla; lengan bawah (siku)
    # ikut syarat lengannya karena "*": false juga menyembunyikan tulang anak.
    for x in v["controller.render.player.first_person"]["part_visibility"]:
        (bone, syarat), = x.items()
        if bone.endswith("Sleeve"):
            continue
        fp.append({bone: syarat})
        if bone in ("rightArm", "leftArm"):
            fp.append({bone.replace("Arm", "Forearm"): syarat})
    larik = {"Array.model": [f"Geometry.waguri_{m.id}" for m in models]}
    larik_tex = {"Array.kulit": [f"Texture.waguri_{m.id}" for m in models]}
    idx = "math.clamp(q.property('waguri:model') - 1, 0, %d)" % (len(models) - 1)
    umum = {
        "arrays": {"geometries": larik, "textures": larik_tex},
        "geometry": f"Array.model[{idx}]",
        "materials": [{"*": "Material.default"}],
        "textures": [f"Array.kulit[{idx}]"],
    }
    return {
        "format_version": "1.8.0",
        "render_controllers": {
            "controller.render.waguri.first_person": {**umum, "part_visibility": fp},
            "controller.render.waguri.third_person": {**umum, "part_visibility": [{"*": True}]},
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
        "header": {"name": nama, "description": deskripsi, "uuid": header, "version": [1, 1, 0],
                   "min_engine_version": ENGINE},
        "modules": [{"type": tipe, "uuid": modul, "version": [1, 1, 0]}],
        "metadata": {"authors": ["Rakitin"]},
    }
    if dependensi:
        m["dependencies"] = [{"uuid": dependensi, "version": [1, 1, 0]}]
    return m


def data_script(models):
    """Daftar model & emote untuk script (dibuat otomatis agar selalu sinkron)."""
    daftar = [{"nama": "Skin sendiri (bawaan)", "ket": "Kembali ke skin Minecraft-mu."}]
    daftar += [{"nama": m.nama_id, "ket": m.deskripsi} for m in models]
    emote = [{"id": i, "nama": n, "lama": lama} for i, _k, n, lama in EMOTE]
    return ("// File ini dibuat otomatis oleh tools/buat_waguri.py. Jangan diedit manual.\n"
            f"export const MODEL = {json.dumps(daftar, ensure_ascii=False, indent=2)};\n\n"
            f"export const EMOTE = {json.dumps(emote, ensure_ascii=False, indent=2)};\n")


# ===========================================================================
# Pratinjau
# ===========================================================================
def pratinjau(models, tekstur, S=7):
    latar = "#f6eef0"
    kolom = []
    for m in models:
        depan = inti.render(m, tekstur[m.id], yaw=0, S=S, lebar=30, latar=latar)
        miring = inti.render(m, tekstur[m.id], yaw=145, S=S, lebar=30, latar=latar)
        kolom.append((m, depan, miring))
    w = kolom[0][1].width
    h = kolom[0][1].height
    img = Image.new("RGBA", (w * len(kolom), h * 2 + 40), rgb(latar))
    dr = ImageDraw.Draw(img)
    for i, (m, depan, miring) in enumerate(kolom):
        img.alpha_composite(depan, (i * w, 22))
        img.alpha_composite(miring, (i * w, h + 30))
        dr.text((i * w + 8, 6), m.nama, fill=(60, 30, 50, 255))
        dr.text((i * w + 8, h + 14), f"{len(m.daftar)} kubus", fill=(110, 80, 100, 255))
    return img


# ===========================================================================
# Utama
# ===========================================================================
def main():
    models = semua_model()
    tekstur, masalah = {}, []
    for m in models:  # satu tekstur HD per karakter
        geo, tex, info = inti.bangun(m)
        tekstur[m.id] = tex
        masalah += [f"{m.id}: {x}" for x in inti.periksa(m, geo, tex)]
        tulis_json(geo, RP, "models", "entity", f"waguri_{m.id}.geo.json")
        simpan(tex, RP, "textures", "entity", "waguri", f"{m.id}.png")
        print(f"  {m.id}: {info['kubus']} kubus, tekstur {tex.width}x{tex.height}")
    if masalah:
        print("\n".join("MASALAH " + x for x in masalah))
        raise SystemExit(1)

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
    tulis_json(manifest("Waguri YSM §dRP", "Model pemain 3D detail ala Yes Steve Model: Kaoruko Waguri & teman-teman.",
                        UUID["rp_header"], UUID["rp_module"], "resources"), RP, "manifest.json")

    # ---------------- BP ----------------
    tulis_json(player_bp(models), BP, "entities", "player.json")
    tulis_json(item_lemari(), BP, "items", "lemari.json")
    tulis_json(resep_lemari(), BP, "recipes", "lemari.json")
    tulis_teks(data_script(models), BP, "scripts", "data.js")
    mbp = manifest("Waguri YSM §dBP", "Pilih model anime lewat Lemari Model (klik kanan). Tanpa eksperimen.",
                   UUID["bp_header"], UUID["bp_module"], "data", UUID["rp_header"])
    mbp["modules"].append({"type": "script", "language": "javascript", "uuid": UUID["bp_script"],
                           "version": [1, 1, 0], "entry": "scripts/main.js"})
    mbp["dependencies"] = [{"module_name": "@minecraft/server", "version": "2.4.0"},
                           {"module_name": "@minecraft/server-ui", "version": "2.0.0"}] + mbp["dependencies"]
    tulis_json(mbp, BP, "manifest.json")

    # ---------------- ikon pack & pratinjau ----------------
    simpan(pratinjau(models, tekstur), DOCS, "pratinjau.png")
    for m in models:
        simpan(inti.lembar_render(m, tekstur[m.id], S=8), DOCS, "karakter", f"{m.id}.png")
    wajah = inti.render(models[0], tekstur[models[0].id], yaw=12, S=12, lebar=14, tinggi=14, atas=35,
                        latar="#f3c9d3", skala=False)
    simpan(wajah.resize((128, 128), Image.LANCZOS), RP, "pack_icon.png")
    simpan(wajah.resize((128, 128), Image.LANCZOS), BP, "pack_icon.png")
    # file lama dari versi sebelumnya
    for lama in ("tekstur_kaoruko_x2.png",):
        p = os.path.join(DOCS, lama)
        if os.path.exists(p):
            os.remove(p)
    print("Selesai:", ", ".join(m.nama for m in models))


if __name__ == "__main__":
    main()
