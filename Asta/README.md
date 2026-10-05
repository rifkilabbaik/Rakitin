![Pratinjau](docs/pratinjau.png)

# Asta (Black Clover) untuk Minecraft Bedrock

Paket bertema **Asta** dari *Black Clover*:

| Isi | Keterangan |
|---|---|
| 🧍 **Skin Asta** | 64×64 (model klasik), rambut perak, ikat kepala, jubah Banteng Hitam, sabuk & sepatu cokelat. Bonus: skin **Asta Mode Iblis**. |
| 🛡️ **Armor Penyatuan Iblis** | 4 item armor **baru dengan bentuk 3D sendiri** (wujud Devil Union, tanpa sayap): helm berambut runcing dengan **tanduk melingkar** & mata merah, zirah dengan lambang dada & **pelindung bahu berduri**, sarung tangan **bercakar**, celana dengan **ekor iblis** & duri lutut, sepatu bercakar. Armor Netherite vanilla tidak diubah. |
| 🪽 **Elytra Sayap Iblis** | Sayap hitam compang-camping dengan tulang merah. **Menggantikan tampilan Elytra.** |
| ⚔️ **4 Pedang Iblis** | Item baru dengan model 3D di tangan (dipegang **di gagang**), **ukuran & kekuatan mengikuti lore**. |

| | |
|---|---|
| **Versi game** | Minecraft Bedrock **1.26.30 ke atas** |
| **Eksperimen** | Tidak perlu (Script API stabil `@minecraft/server` 2.4.0) |

---

## Pedang & Resep

Resep **tanpa bentuk (shapeless)** di **Meja Kerajinan**: taruh **pedang apa saja** (kayu, batu, besi, emas,
berlian, netherite, atau pedang iblis lain) + **1 ingot**:

| Bahan | Hasil | Damage | Durabilitas | Panjang (lore) |
|---|---|---|---|---|
| Pedang apa saja + **Iron Ingot** | **Demon-Destroyer Sword** (Pedang Penghancur Iblis) | 8 | 1200 | ±1,6 blok, ramping |
| Pedang apa saja + **Gold Ingot** | **Demon-Dweller Sword** (Pedang Penghuni Iblis) | 9 | 1500 | ±1,75 blok, lebar |
| Pedang apa saja + **Diamond** | **Demon-Slayer Sword** (Pedang Pembasmi Iblis) | 10 | 2031 | **2 blok** (setinggi Asta), sangat lebar |
| Pedang apa saja + **Netherite Ingot** | **Demon-Slasher Katana** (Katana Penebas Iblis) | 11 | 2500 | ±1,75 blok, melengkung |

> Berlian memakai item `minecraft:diamond` (Bedrock tidak punya "diamond ingot").
> Semua pedang iblis bisa di-enchant seperti pedang biasa dan diperbaiki di Anvil dengan Netherite Ingot.

### Kekuatan pedang (sesuai lore)

Semua pedang iblis bersifat **anti-sihir**: setiap pukulan **menghapus semua efek** (buff sihir) pada musuh.

| Pedang | Pasif (saat dipegang) | Klik kanan | Jeda |
|---|---|---|---|
| **Demon-Slayer** — pedang anti-sihir pertama Asta | Kebal kutukan: efek buruk (racun, wither, lemah, lambat, buta, levitasi, dll.) langsung hilang. **+6 damage** ke makhluk sihir (witch, evoker, vex, blaze, ghast, enderman, shulker, guardian, breeze, wither, naga Ender, warden). | **Tebasan Anti-Sihir**: gelombang tebasan 7 blok ke depan, 10 damage (16 ke makhluk sihir) + terpental, dan menebas semua proyektil (panah, bola api, tengkorak wither, dll.) di sekitar. | 6 dtk |
| **Demon-Destroyer** — menghancurkan sihir yang sudah terpasang | Proyektil yang mendekat (≤3 blok) otomatis dihancurkan. | **Pemecah Kutukan** (radius 8 blok): menghapus efek buruk semua pemain + Regenerasi II 5 dtk, **zombie villager dipulihkan menjadi villager**, buff musuh dihapus, proyektil dihancurkan. | 10 dtk |
| **Demon-Dweller** — menyerap sihir lalu melepaskannya | Serangan sihir/proyektil/api/ledakan/petir yang mengenaimu: **50% damage dipulihkan** dan disimpan sebagai **muatan sihir** (maks 40). Tiap pukulan juga menyerap +2. | **Lepaskan Sihir**: sinar sejauh 20 blok, damage **4 + muatan** ke semua yang dilewati, lalu muatan kembali 0. | 2 dtk |
| **Demon-Slasher Katana** — tebasan kilat Black Asta | Speed II + kebal kutukan. | **Tebasan Hitam Kilat**: melesat ±8 blok ke depan, 12 damage ke semua yang dilewati, lalu tebasan pendaratan 4 damage. Kebal damage selama melesat. | 5 dtk |

---

## Armor Penyatuan Iblis

Resep **tanpa bentuk** di Meja Kerajinan: **bagian armor Netherite + Crying Obsidian + Redstone Block**.

| Bahan | Hasil | Proteksi | Durabilitas |
|---|---|---|---|
| Netherite Helmet + Crying Obsidian + Redstone Block | **Helm Penyatuan Iblis** (tanduk, rambut runcing, mata merah) | 4 | 520 |
| Netherite Chestplate + … | **Zirah Penyatuan Iblis** (lambang dada, bahu berduri, cakar) | 9 | 760 |
| Netherite Leggings + … | **Celana Penyatuan Iblis** (ekor iblis, duri lutut) | 7 | 710 |
| Netherite Boots + … | **Sepatu Penyatuan Iblis** (cakar kaki) | 4 | 610 |

**Bonus set** (seperti Asta menyatu dengan iblis Liebe):
- **2 bagian atau lebih**: kebal kutukan (efek buruk langsung hilang).
- **4 bagian (Penyatuan Iblis penuh)**: Strength II, Speed I, Jump Boost II, Resistance I, Night Vision, dan aura merah.

![Ikon pedang](docs/ikon_pedang.png)

---

## Cara Pasang

Unduh dari folder [`dist/`](dist):

| File | Fungsi |
|---|---|
| [`Asta.mcaddon`](dist/Asta.mcaddon) | Pedang iblis + armor Penyatuan Iblis + elytra (BP + RP). **Pakai ini.** |
| [`Asta_RP.mcpack`](dist/Asta_RP.mcpack) | Hanya resource pack (tanpa BP, cuma tampilan elytra yang berubah) |
| [`Asta_Skin.mcpack`](dist/Asta_Skin.mcpack) | Skin pack Asta (Asta + Asta Mode Iblis) |
| [`asta.png`](dist/asta.png), [`asta_iblis.png`](dist/asta_iblis.png) | File skin untuk diimpor langsung |

1. Buka `Asta.mcaddon` dengan Minecraft, tunggu *Import berhasil*.
2. Di pengaturan dunia → **Behavior Packs** → aktifkan **Asta BP** (Asta RP ikut aktif otomatis).
3. **Skin**: buka **Ruang Ganti → Edit Karakter → Skin Klasik → Impor → Pilih skin baru** → pilih `asta.png`,
   lalu pilih model **klasik (lengan lebar)**. Atau buka `Asta_Skin.mcpack` (skin pack).

Addon ini bisa dipasang bersama addon **Rakitin** (folder [`../raft`](../raft)).

---

## Catatan

- Armor Penyatuan Iblis adalah item baru dengan model 3D sendiri (`Asta_RP/attachables/asta_iblis_*.json`).
  Elytra tetap **pengganti tekstur** elytra vanilla.
- Model pedang di tangan memakai animasi pegang **trident vanilla**. Pusat gagang diletakkan tepat di titik
  yang jatuh ke tangan pada animasi itu (`GRIP_Y = 13.3` di `tools/buat_asta.py`). Jika di perangkatmu masih
  meleset, ubah `GRIP_Y` (lebih kecil = pedang bergeser ke atas tangan) lalu jalankan ulang generator.
- Karakter & nama milik © Yūki Tabata / Shueisha. Semua tekstur di sini adalah pixel art buatan sendiri
  (prosedural), tidak memakai aset resmi.

## Untuk Pengembang

```
Asta_Skin/   skin pack (manifest, skins.json, asta.png, asta_iblis.png)
Asta_RP/     textures/asta/armor/iblis.png (tekstur armor 3D), elytra, ikon, sprite pedang,
             attachables/, models/entity/ (geometri armor & pedang), animations/, texts/
Asta_BP/     items/ (4 pedang + 4 armor), recipes/ (8 resep shapeless),
             scripts/ (main.js, pedang.js = kekuatan pedang, armor.js = bonus set, util.js)
tools/
  buat_asta.py   generator gambar & JSON (script di Asta_BP/scripts ditulis manual)
  build.sh       membuat dist/
docs/        pratinjau
dist/        paket siap pasang
```

```bash
cd Asta
pip install pillow
python3 tools/buat_asta.py
./tools/build.sh
```
