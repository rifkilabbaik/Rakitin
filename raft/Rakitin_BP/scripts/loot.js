// Tabel hasil pancingan, isi puing, dan peti pulau.
import { acak, peluang, pilihBerbobot } from "./util.js";

// Peluang kategori (dalam persen) untuk tiap tier kail. Jumlah tiap baris = 100.
export const PELUANG_KATEGORI = {
  1: { sampah: 30, ikan: 35, blok: 25, bahan: 8, langka: 2, harta: 0, portal: 0 },
  2: { sampah: 22, ikan: 33, blok: 27, bahan: 13, langka: 4, harta: 1, portal: 0 },
  3: { sampah: 15, ikan: 30, blok: 28, bahan: 18, langka: 7, harta: 2, portal: 0 },
  4: { sampah: 10, ikan: 27, blok: 28, bahan: 22, langka: 10, harta: 3, portal: 0 },
  5: { sampah: 5, ikan: 25, blok: 25, bahan: 23, langka: 11, harta: 5, portal: 6 },
};

/** Peluang dapat dua tangkapan sekaligus. */
export const PELUANG_GANDA = { 1: 0, 2: 0, 3: 0.05, 4: 0.1, 5: 0.2 };

export const INFO_KATEGORI = {
  sampah: { nama: "Sampah", warna: "§7" },
  ikan: { nama: "Ikan", warna: "§b" },
  blok: { nama: "Blok", warna: "§a" },
  bahan: { nama: "Bahan", warna: "§f" },
  langka: { nama: "Langka", warna: "§6" },
  harta: { nama: "Harta", warna: "§d" },
  portal: { nama: "Bahan Portal", warna: "§5" },
};

// [id item, bobot, jumlah min, jumlah maks]
const ISI = {
  sampah: [
    ["minecraft:string", 15, 1, 2],
    ["minecraft:stick", 15, 1, 3],
    ["rakit:plastik", 15, 1, 2],
    ["minecraft:kelp", 10, 1, 3],
    ["minecraft:bone", 10, 1, 2],
    ["minecraft:rotten_flesh", 10, 1, 2],
    ["minecraft:bowl", 8, 1, 1],
    ["minecraft:leather", 6, 1, 1],
    ["minecraft:ink_sac", 6, 1, 2],
    ["minecraft:tripwire_hook", 5, 1, 1],
  ],
  ikan: [
    ["minecraft:cod", 55, 1, 1],
    ["minecraft:salmon", 25, 1, 1],
    ["minecraft:tropical_fish", 12, 1, 1],
    ["minecraft:pufferfish", 8, 1, 1],
  ],
  blok: [
    ["minecraft:oak_planks", 22, 2, 4],
    ["minecraft:oak_log", 14, 1, 2],
    ["minecraft:cobblestone", 14, 2, 6],
    ["minecraft:dirt", 13, 1, 3],
    ["minecraft:sand", 12, 2, 4],
    ["minecraft:oak_sapling", 8, 1, 1],
    ["minecraft:wheat_seeds", 7, 1, 3],
    ["minecraft:gravel", 5, 1, 3],
    ["minecraft:clay_ball", 5, 2, 4],
  ],
  bahan: [
    ["minecraft:coal", 18, 1, 3],
    ["minecraft:raw_iron", 14, 1, 2],
    ["rakit:besi_tua", 14, 1, 2],
    ["minecraft:iron_nugget", 10, 2, 5],
    ["minecraft:raw_copper", 8, 1, 3],
    ["minecraft:redstone", 7, 2, 5],
    ["minecraft:gold_nugget", 7, 2, 4],
    ["minecraft:lapis_lazuli", 5, 2, 4],
    ["minecraft:flint", 4, 1, 2],
    ["minecraft:potato", 4, 1, 2],
    ["minecraft:carrot", 4, 1, 2],
    ["minecraft:beetroot_seeds", 3, 1, 2],
    ["minecraft:sugar_cane", 2, 1, 2],
  ],
  langka: [
    ["minecraft:gold_ingot", 18, 1, 2],
    ["minecraft:raw_gold", 10, 1, 2],
    ["minecraft:diamond", 10, 1, 1],
    ["minecraft:emerald", 10, 1, 2],
    ["minecraft:experience_bottle", 8, 1, 3],
    ["minecraft:nautilus_shell", 7, 1, 1],
    ["minecraft:arrow", 7, 4, 8],
    ["minecraft:obsidian", 5, 1, 2],
    ["minecraft:name_tag", 5, 1, 1],
    ["minecraft:bow", 5, 1, 1],
    ["minecraft:golden_carrot", 5, 1, 2],
    ["minecraft:saddle", 3, 1, 1],
    ["minecraft:birch_sapling", 2, 1, 1],
    ["minecraft:spruce_sapling", 2, 1, 1],
    ["minecraft:jungle_sapling", 2, 1, 1],
    ["minecraft:cherry_sapling", 1, 1, 1],
  ],
  harta: [
    ["minecraft:diamond", 25, 1, 2],
    ["minecraft:netherite_scrap", 15, 1, 1],
    ["minecraft:golden_apple", 14, 1, 1],
    ["minecraft:experience_bottle", 14, 3, 6],
    ["minecraft:emerald", 10, 2, 4],
    ["minecraft:totem_of_undying", 6, 1, 1],
    ["minecraft:heart_of_the_sea", 5, 1, 1],
    ["minecraft:trident", 4, 1, 1],
    ["minecraft:iron_block", 4, 1, 1],
    ["minecraft:enchanted_golden_apple", 3, 1, 1],
  ],
  portal: [
    ["rakit:pecahan_portal", 55, 1, 1],
    ["minecraft:ender_eye", 15, 1, 1],
    ["minecraft:ender_pearl", 15, 1, 2],
    ["minecraft:blaze_rod", 15, 1, 1],
  ],
};

function ambilDari(daftar) {
  const e = pilihBerbobot(daftar.map(([id, bobot, min, maks]) => ({ id, bobot, min, maks })));
  return { id: e.id, jumlah: acak(e.min, e.maks) };
}

/** Hasil satu tangkapan untuk tier tertentu. */
export function gulirTangkapan(tier) {
  const p = PELUANG_KATEGORI[tier] ?? PELUANG_KATEGORI[1];
  const kat = pilihBerbobot(
    Object.entries(p)
      .filter(([, bobot]) => bobot > 0)
      .map(([kategori, bobot]) => ({ kategori, bobot }))
  ).kategori;
  return { kategori: kat, ...ambilDari(ISI[kat]) };
}

/** Persentase peluang tangkapan bagus (langka + harta + portal). */
export function peluangBagus(tier) {
  const p = PELUANG_KATEGORI[tier] ?? PELUANG_KATEGORI[1];
  return p.langka + p.harta + p.portal;
}

// --- Puing hanyut ----------------------------------------------------------
export const JENIS_PUING = [
  { jenis: 0, nama: "Papan Hanyut", bobot: 40 },
  { jenis: 1, nama: "Sampah Plastik", bobot: 30 },
  { jenis: 2, nama: "Daun Palem", bobot: 20 },
  { jenis: 3, nama: "Barel Terapung", bobot: 10 },
];

const ISI_BAREL = [
  ["minecraft:oak_planks", 14, 2, 4],
  ["rakit:plastik", 14, 1, 3],
  ["rakit:daun_palem", 10, 1, 2],
  ["minecraft:string", 8, 1, 2],
  ["rakit:besi_tua", 8, 1, 2],
  ["minecraft:wheat_seeds", 6, 1, 3],
  ["minecraft:potato", 5, 1, 2],
  ["minecraft:carrot", 5, 1, 2],
  ["minecraft:beetroot_seeds", 4, 1, 2],
  ["minecraft:dirt", 6, 1, 2],
  ["minecraft:oak_sapling", 4, 1, 1],
  ["minecraft:bone_meal", 5, 1, 3],
  ["minecraft:iron_nugget", 5, 2, 4],
  ["minecraft:cooked_cod", 4, 1, 2],
  ["rakit:botol_kosong", 4, 1, 1],
  ["rakit:air_bersih", 3, 1, 1],
];

/** Daftar `{id, jumlah}` hasil mengambil puing. */
export function isiPuing(jenis) {
  switch (jenis) {
    case 0: {
      const hasil = [{ id: "minecraft:oak_planks", jumlah: acak(1, 3) }];
      if (peluang(0.2)) hasil.push({ id: "minecraft:stick", jumlah: 1 });
      return hasil;
    }
    case 1:
      return [{ id: "rakit:plastik", jumlah: acak(1, 2) }];
    case 2: {
      const hasil = [{ id: "rakit:daun_palem", jumlah: acak(1, 2) }];
      if (peluang(0.15)) hasil.push({ id: "minecraft:string", jumlah: 1 });
      return hasil;
    }
    default: {
      const hasil = [];
      const n = acak(3, 5);
      for (let i = 0; i < n; i++) hasil.push(ambilDari(ISI_BAREL));
      return hasil;
    }
  }
}

// --- Peti pulau ------------------------------------------------------------
const ISI_PULAU = [
  ["minecraft:oak_sapling", 8, 1, 2],
  ["minecraft:dirt", 8, 2, 4],
  ["minecraft:wheat_seeds", 6, 2, 4],
  ["minecraft:potato", 5, 1, 3],
  ["minecraft:carrot", 5, 1, 3],
  ["minecraft:melon_seeds", 3, 1, 2],
  ["minecraft:pumpkin_seeds", 3, 1, 2],
  ["minecraft:iron_ingot", 6, 1, 3],
  ["minecraft:gold_ingot", 4, 1, 2],
  ["minecraft:coal", 6, 2, 5],
  ["minecraft:bread", 6, 1, 3],
  ["rakit:air_bersih", 6, 1, 2],
  ["rakit:besi_tua", 5, 1, 3],
  ["minecraft:bone_meal", 4, 2, 4],
  ["minecraft:diamond", 2, 1, 1],
  ["minecraft:experience_bottle", 3, 1, 3],
];

export function isiPetiPulau() {
  const hasil = [];
  const n = acak(5, 8);
  for (let i = 0; i < n; i++) hasil.push(ambilDari(ISI_PULAU));
  if (peluang(0.1)) hasil.push({ id: "rakit:pecahan_portal", jumlah: 1 });
  return hasil;
}
