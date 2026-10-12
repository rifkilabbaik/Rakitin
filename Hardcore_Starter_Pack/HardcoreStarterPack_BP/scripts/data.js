// Data vanilla yang dipakai banyak fitur: ore, hasil lebur, tanaman, pohon, alat.

const M = (id) => `minecraft:${id}`;

/**
 * Jenis ore. `tier` = tier beliung minimal agar ore menjatuhkan barang
 * (0 kayu/emas, 1 batu/tembaga, 2 besi, 3 berlian, 4 netherite).
 * `xp` = rentang XP vanilla saat ditambang tanpa Silk Touch.
 */
export const ORE = [
  { kunci: "berlian", nama: "Berlian", warna: "§b", tier: 2, xp: [3, 7], blok: ["diamond_ore", "deepslate_diamond_ore"] },
  { kunci: "zamrud", nama: "Zamrud", warna: "§a", tier: 2, xp: [3, 7], blok: ["emerald_ore", "deepslate_emerald_ore"] },
  { kunci: "debris", nama: "Puing Kuno", warna: "§n", tier: 3, xp: [0, 0], blok: ["ancient_debris"] },
  { kunci: "emas", nama: "Emas", warna: "§e", tier: 2, xp: [0, 0], blok: ["gold_ore", "deepslate_gold_ore"] },
  { kunci: "emas_nether", nama: "Emas Nether", warna: "§6", tier: 0, xp: [0, 1], blok: ["nether_gold_ore"] },
  { kunci: "besi", nama: "Besi", warna: "§i", tier: 1, xp: [0, 0], blok: ["iron_ore", "deepslate_iron_ore"] },
  { kunci: "tembaga", nama: "Tembaga", warna: "§v", tier: 1, xp: [0, 0], blok: ["copper_ore", "deepslate_copper_ore"] },
  { kunci: "redstone", nama: "Redstone", warna: "§c", tier: 2, xp: [1, 5], blok: ["redstone_ore", "deepslate_redstone_ore", "lit_redstone_ore", "lit_deepslate_redstone_ore"] },
  { kunci: "lapis", nama: "Lapis", warna: "§9", tier: 1, xp: [2, 5], blok: ["lapis_ore", "deepslate_lapis_ore"] },
  { kunci: "kuarsa", nama: "Kuarsa", warna: "§f", tier: 0, xp: [2, 5], blok: ["quartz_ore"] },
  { kunci: "batubara", nama: "Batu Bara", warna: "§8", tier: 0, xp: [0, 2], blok: ["coal_ore", "deepslate_coal_ore"] },
].map((o) => ({ ...o, blok: o.blok.map(M) }));

/** id blok ore -> data ore */
export const ORE_PER_BLOK = new Map();
for (const o of ORE) for (const b of o.blok) ORE_PER_BLOK.set(b, o);

/** Hasil leburan (Auto Smelt): item jatuhan -> item hasil tungku. */
export const LEBUR = new Map(
  [
    ["raw_iron", "iron_ingot"],
    ["raw_gold", "gold_ingot"],
    ["raw_copper", "copper_ingot"],
    ["iron_ore", "iron_ingot"],
    ["deepslate_iron_ore", "iron_ingot"],
    ["gold_ore", "gold_ingot"],
    ["deepslate_gold_ore", "gold_ingot"],
    ["nether_gold_ore", "gold_ingot"],
    ["copper_ore", "copper_ingot"],
    ["deepslate_copper_ore", "copper_ingot"],
    ["ancient_debris", "netherite_scrap"],
    ["coal_ore", "coal"],
    ["deepslate_coal_ore", "coal"],
    ["diamond_ore", "diamond"],
    ["deepslate_diamond_ore", "diamond"],
    ["emerald_ore", "emerald"],
    ["deepslate_emerald_ore", "emerald"],
    ["lapis_ore", "lapis_lazuli"],
    ["deepslate_lapis_ore", "lapis_lazuli"],
    ["redstone_ore", "redstone"],
    ["deepslate_redstone_ore", "redstone"],
    ["quartz_ore", "quartz"],
  ].map(([a, b]) => [M(a), M(b)])
);

/**
 * Tanaman yang bisa dipanen Crop Capitator.
 * `state`/`matang` = nama & nilai state umur saat siap panen; `bibit` = item untuk tanam ulang.
 */
export const TANAMAN = new Map(
  [
    ["wheat", "growth", 7, "wheat_seeds"],
    ["carrots", "growth", 7, "carrot"],
    ["potatoes", "growth", 7, "potato"],
    ["beetroot", "growth", 7, "beetroot_seeds"],
    ["nether_wart", "age", 3, "nether_wart"],
    ["cocoa", "age", 2, "cocoa_beans"],
  ].map(([id, state, matang, bibit]) => [M(id), { state, matang, bibit: M(bibit) }])
);

/** Blok buah tanpa tanam ulang (batangnya tetap tumbuh). */
export const BUAH = new Set([M("melon_block"), M("pumpkin")]);

const KAYU = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak", "poplar"];

/** Batang pohon -> kelompok (batang sejenis dianggap satu pohon). */
export const BATANG = new Map();
for (const k of KAYU) {
  BATANG.set(M(`${k}_log`), k);
  BATANG.set(M(`${k}_wood`), k);
}
BATANG.set(M("crimson_stem"), "crimson");
BATANG.set(M("warped_stem"), "warped");

/** Daun alami (punya state persistent_bit). */
export const DAUN = new Set(
  [
    "oak_leaves", "spruce_leaves", "birch_leaves", "jungle_leaves", "acacia_leaves", "dark_oak_leaves",
    "mangrove_leaves", "cherry_leaves", "pale_oak_leaves", "azalea_leaves", "azalea_leaves_flowered",
    "orange_poplar_leaves", "red_poplar_leaves", "yellow_poplar_leaves",
  ].map(M)
);

/** "Daun" jamur raksasa Nether (tidak punya persistent_bit). */
export const DAUN_NETHER = new Map([
  ["crimson", new Set([M("nether_wart_block"), M("shroomlight")])],
  ["warped", new Set([M("warped_wart_block"), M("shroomlight")])],
]);

/** Blok yang tidak boleh ikut dihancurkan oleh fitur area (3x3, vein, pohon). */
export const TERLARANG = new Set(
  [
    "air", "bedrock", "barrier", "command_block", "chain_command_block", "repeating_command_block",
    "structure_block", "structure_void", "jigsaw", "allow", "deny", "border_block", "end_portal",
    "end_portal_frame", "portal", "reinforced_deepslate", "trial_spawner", "vault", "mob_spawner",
    "water", "flowing_water", "lava", "flowing_lava", "fire", "soul_fire", "bubble_column", "light_block",
  ].map(M)
);

/** Blok yang efektif dengan sekop (dipakai 3x3 saat memegang sekop). */
export const BLOK_SEKOP = new Set(
  [
    "dirt", "coarse_dirt", "grass_block", "podzol", "mycelium", "farmland", "grass_path",
    "dirt_with_roots", "sand", "red_sand", "gravel", "clay", "mud", "muddy_mangrove_roots", "soul_sand",
    "soul_soil", "snow", "snow_layer", "suspicious_sand", "suspicious_gravel",
  ].map(M)
);

/** Tier alat dari bahannya. */
const TIER_BAHAN = { wooden: 0, golden: 0, stone: 1, copper: 1, iron: 2, diamond: 3, netherite: 4 };

/** Tier sebuah alat vanilla (alat custom dianggap setara besi). */
export function tierAlat(item) {
  const m = /^minecraft:([a-z]+)_(pickaxe|axe|shovel|hoe|sword|spear)$/.exec(item.typeId);
  return m && m[1] in TIER_BAHAN ? TIER_BAHAN[m[1]] : 2;
}

/** Tier beliung minimal agar sebuah blok menjatuhkan barang. */
const TIER_BLOK = new Map(
  [
    ["obsidian", 3], ["crying_obsidian", 3], ["respawn_anchor", 3], ["netherite_block", 3],
    ["diamond_block", 2], ["gold_block", 2], ["emerald_block", 2], ["raw_gold_block", 2],
    ["iron_block", 1], ["lapis_block", 1], ["raw_iron_block", 1], ["raw_copper_block", 1],
  ].map(([id, t]) => [M(id), t])
);

export function tierDibutuhkan(blok) {
  const ore = ORE_PER_BLOK.get(blok.typeId);
  if (ore) return ore.tier;
  const t = TIER_BLOK.get(blok.typeId);
  if (t !== undefined) return t;
  try {
    if (blok.hasTag("minecraft:diamond_tier_destructible")) return 3;
    if (blok.hasTag("minecraft:iron_tier_destructible")) return 2;
    if (blok.hasTag("minecraft:stone_tier_destructible")) return 1;
  } catch {
    // tag tidak tersedia
  }
  return 0;
}

/** Item yang menyalakan Ore Detector / Compass Finder saat berada di tangan kiri. */
export const OBOR = new Set(["hsp:torch_detector", M("torch"), M("soul_torch"), M("copper_torch")]);
export const KOMPAS = new Set(["hsp:compass_finder", M("compass")]);
