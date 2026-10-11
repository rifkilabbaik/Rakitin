// Tabel ore, radius per beliung, dan konstanta Torch Detektor.

export const ID_OBOR = "td:obor_detektor";
export const TAG_BELIUNG = "minecraft:is_pickaxe";

/**
 * Daftar ore yang bisa dideteksi. Urutan = prioritas tampilan HUD.
 * `warna` = RRGGBB (tanpa #) untuk outline; `kode` = kode warna teks § yang paling mirip.
 * @type {{ kunci: string, nama: string, warna: string, kode: string, blok: string[] }[]}
 */
export const ORE = [
  { kunci: "berlian", nama: "Berlian", warna: "4EE2EC", kode: "§b", blok: ["minecraft:diamond_ore", "minecraft:deepslate_diamond_ore"] },
  { kunci: "zamrud", nama: "Zamrud", warna: "17DD62", kode: "§a", blok: ["minecraft:emerald_ore", "minecraft:deepslate_emerald_ore"] },
  { kunci: "emas", nama: "Emas", warna: "FCEE4B", kode: "§e", blok: ["minecraft:gold_ore", "minecraft:deepslate_gold_ore", "minecraft:nether_gold_ore"] },
  { kunci: "besi", nama: "Besi", warna: "D8AF93", kode: "§i", blok: ["minecraft:iron_ore", "minecraft:deepslate_iron_ore"] },
  { kunci: "tembaga", nama: "Tembaga", warna: "E0734A", kode: "§v", blok: ["minecraft:copper_ore", "minecraft:deepslate_copper_ore"] },
  {
    kunci: "redstone",
    nama: "Redstone",
    warna: "FF2A2A",
    kode: "§c",
    blok: ["minecraft:redstone_ore", "minecraft:deepslate_redstone_ore", "minecraft:lit_redstone_ore", "minecraft:lit_deepslate_redstone_ore"],
  },
  { kunci: "lapis", nama: "Lapis", warna: "2F5BFF", kode: "§9", blok: ["minecraft:lapis_ore", "minecraft:deepslate_lapis_ore"] },
  { kunci: "batubara", nama: "Batu Bara", warna: "5A5A5A", kode: "§8", blok: ["minecraft:coal_ore", "minecraft:deepslate_coal_ore"] },
  { kunci: "kuarsa", nama: "Kuarsa", warna: "F2EDE6", kode: "§f", blok: ["minecraft:quartz_ore"] },
  { kunci: "debris", nama: "Puing Kuno", warna: "A0674F", kode: "§n", blok: ["minecraft:ancient_debris"] },
];

/** id blok -> indeks di ORE */
export const INDEKS_BLOK = new Map();
ORE.forEach((o, i) => {
  for (const id of o.blok) INDEKS_BLOK.set(id, i);
});

/** Warna RGBA 0..1 per ore (urutan sama dengan ORE). */
export const WARNA_RGBA = ORE.map((o) => ({
  red: parseInt(o.warna.slice(0, 2), 16) / 255,
  green: parseInt(o.warna.slice(2, 4), 16) / 255,
  blue: parseInt(o.warna.slice(4, 6), 16) / 255,
  alpha: 1,
}));

/**
 * Radius maksimum (blok) menurut jenis beliung di tangan kanan.
 * @type {Record<string, number>}
 */
export const RADIUS_BELIUNG = {
  "minecraft:wooden_pickaxe": 4,
  "minecraft:golden_pickaxe": 4,
  "minecraft:stone_pickaxe": 5,
  "minecraft:copper_pickaxe": 5,
  "minecraft:iron_pickaxe": 6,
  "minecraft:diamond_pickaxe": 7,
  "minecraft:netherite_pickaxe": 8,
};
/** Untuk item lain yang bertag is_pickaxe (mis. beliung dari addon lain). */
export const RADIUS_BAWAAN = 5;
export const RADIUS_MIN = 3;
export const RADIUS_MAKS = 8;

// --- Waktu (tick) ----------------------------------------------------------
export const TICK_CEK = 10; // cek aktif/nonaktif + HUD
export const TICK_PINDAI_ULANG = 40; // pindai ulang paling lambat tiap 40 tick
export const TICK_GAMBAR = 20; // gambar ulang semua outline partikel
export const TICK_KIRIM_XRAY = 40; // kirim data ke pack X-Ray minimal tiap 40 tick
export const BATAS_DETAK_XRAY = 100; // X-Ray dianggap aktif bila detak terakhir <= 100 tick lalu
export const TICK_CAHAYA = 5;
export const TICK_BERSIH_CAHAYA = 40; // coba hapus cahaya yatim tiap 40 tick
export const TAHAN_PESAN = 30; // HUD menunggu selama ini setelah pesan actionbar lain

// --- Batas lag -------------------------------------------------------------
export const MAKS_ORE = 64; // jumlah ore yang disimpan per pemain
export const MAKS_OUTLINE = 24; // jumlah ore terdekat yang diberi outline partikel
export const MAKS_PESAN = 2000; // panjang maksimum pesan scriptevent ke X-Ray
export const MAKS_HUD = 3; // jenis ore yang tampil di HUD

// --- Id lain ---------------------------------------------------------------
export const PARTIKEL_XZ = "td:garis_xz";
export const PARTIKEL_XY = "td:garis_xy";
export const EVENT_ORE = "td:ore";
export const EVENT_DETAK = "td:xray_hidup";
export const BLOK_CAHAYA = "minecraft:light_block_14";
export const KUNCI_ATUR = "td:atur";
export const KUNCI_CAHAYA = "td:cahaya";
export const KUNCI_CAHAYA_SISA = "td:cahaya_sisa";
