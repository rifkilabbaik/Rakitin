// Deteksi struktur untuk Compass Finder.
//
// Script API tidak punya fungsi "locate", jadi struktur dikenali dari blok-blok khasnya
// di chunk yang sudah termuat. Struktur yang pernah ditemukan disimpan di memori dunia
// sehingga kompas tetap bisa menunjukkan jalan pulang ke sana dari jauh.
import { BlockVolume, world } from "@minecraft/server";
import { blokAman, bacaJSON, jarak, tulisJSON } from "./util.js";

const M = (id) => `minecraft:${id}`;
const KAYU = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak", "poplar", "bamboo", "crimson", "warped"];
const WARNA = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"];

const G = {
  bel: [M("bell")],
  kerja: ["composter", "lectern", "smithing_table", "fletching_table", "cartography_table", "loom", "grindstone", "stonecutter_block", "blast_furnace", "smoker", "brewing_stand"].map(M),
  api: [M("campfire"), M("soul_campfire")],
  pagarNether: [M("nether_brick_fence")],
  bataNether: [M("nether_brick")],
  trial: [M("trial_spawner"), M("vault")],
  kerikilAneh: [M("suspicious_gravel")],
  pasirAneh: [M("suspicious_sand")],
  terakota: WARNA.map((w) => M(`${w}_terracotta`)),
  bingkaiEnd: [M("end_portal_frame")],
  silverfish: ["infested_stone_bricks", "infested_mossy_stone_bricks", "infested_cracked_stone_bricks", "infested_chiseled_stone_bricks"].map(M),
  deepslateKuat: [M("reinforced_deepslate")],
  logGelap: [M("dark_oak_log")],
  papanGelap: [M("dark_oak_planks")],
  papanBirch: [M("birch_planks")],
  spawner: [M("mob_spawner")],
  lumut: [M("mossy_cobblestone")],
  peti: [M("chest")],
  obsidianMenangis: [M("crying_obsidian")],
  obsidian: [M("obsidian")],
  netherrack: [M("netherrack")],
  tnt: [M("tnt")],
  terakotaJingga: [M("orange_terracotta")],
  terakotaBiru: [M("blue_terracotta")],
  rel: [M("rail")],
  sarang: [M("web")],
  pagarKayu: [M("oak_fence"), M("dark_oak_fence")],
  prismarine: [M("prismarine_bricks"), M("dark_prismarine"), M("sea_lantern")],
  ametis: [M("budding_amethyst"), M("amethyst_block")],
  jebakan: [M("tripwire_hook"), M("sticky_piston")],
  tulang: [M("bone_block")],
  papan: KAYU.map((k) => M(`${k}_planks`)),
  kuali: [M("cauldron")],
  papanSpruce: [M("spruce_planks")],
  karpetPutih: [M("white_carpet")],
  slabPasir: [M("sandstone_slab")],
  emasHitam: [M("gilded_blackstone")],
  bataHitam: [M("polished_blackstone_bricks")],
  purpur: [M("purpur_block"), M("purpur_pillar"), M("end_rod")],
  bedrock: [M("bedrock")],
};

/** Semua id blok penanda (satu panggilan getBlocks per kolom chunk). */
export const SEMUA_TANDA = [...new Set(Object.values(G).flat())];

const AIR = new Set([M("water"), M("flowing_water")]);
const ATAP_HARTA = new Set([M("sand"), M("sandstone"), M("gravel"), M("red_sand")]);

/**
 * Daftar struktur. `cek(c)` mengembalikan lokasi struktur atau null.
 * `c.n(grup)` jumlah blok grup di kolom chunk, `c.pos(grup)` lokasi blok pertama grup itu.
 */
export const STRUKTUR = [
  { kunci: "desa", nama: "Village", dim: "overworld", jarak: 96, cek: (c) => (c.n("bel") ? c.pos("bel") : c.n("kerja") >= 3 ? c.pos("kerja") : null) },
  { kunci: "benteng_nether", nama: "Nether Fortress", dim: "nether", jarak: 96, cek: (c) => (c.n("pagarNether") >= 2 || c.n("bataNether") >= 30 ? c.pos("pagarNether") ?? c.pos("bataNether") : null) },
  { kunci: "kemah", nama: "Camp (Abandoned Camp)", dim: "overworld", jarak: 32, cek: (c) => (c.n("api") && !c.n("bel") && c.n("kerja") < 2 ? c.pos("api") : null) },
  { kunci: "trial", nama: "Trial Chamber", dim: "overworld", jarak: 64, cek: (c) => c.pos("trial") },
  { kunci: "trail", nama: "Trail Ruins", dim: "overworld", jarak: 48, cek: (c) => (c.n("kerikilAneh") && c.n("terakota") >= 3 && !c.diBawahAir("kerikilAneh") ? c.pos("kerikilAneh") : null) },
  { kunci: "stronghold", nama: "Stronghold", dim: "overworld", jarak: 96, cek: (c) => c.pos("bingkaiEnd") ?? c.pos("silverfish") },
  { kunci: "ancient_city", nama: "Ancient City", dim: "overworld", jarak: 96, cek: (c) => c.pos("deepslateKuat") },
  { kunci: "outpost", nama: "Pillager Outpost", dim: "overworld", jarak: 64, cek: (c) => (c.n("logGelap") >= 6 && c.n("papanBirch") >= 8 && c.n("papanGelap") < 150 ? c.pos("logGelap") : null) },
  { kunci: "mansion", nama: "Woodland Mansion", dim: "overworld", jarak: 96, cek: (c) => (c.n("papanGelap") >= 150 && c.n("papanBirch") >= 20 ? c.pos("papanGelap") : null) },
  { kunci: "dungeon", nama: "Dungeon", dim: "overworld", jarak: 16, cek: (c) => (c.n("spawner") && c.n("lumut") >= 3 ? c.pos("spawner") : null) },
  { kunci: "harta", nama: "Buried Treasure", dim: "overworld", jarak: 16, cek: (c) => c.cari("peti", (b) => ATAP_HARTA.has(c.tipe(b.x, b.y + 1, b.z))) },
  { kunci: "portal_rusak", nama: "Ruined Portal", dim: null, jarak: 32, cek: (c) => (c.n("obsidianMenangis") ? c.pos("obsidianMenangis") : c.n("obsidian") >= 3 && (c.n("netherrack") >= 3 || c.dimensi === "nether") ? c.pos("obsidian") : null) },
  { kunci: "kuil_gurun", nama: "Desert Temple", dim: "overworld", jarak: 48, cek: (c) => (c.n("tnt") >= 4 && (c.n("terakotaJingga") >= 2 || c.n("terakotaBiru")) ? c.pos("terakotaBiru") ?? c.pos("tnt") : null) },
  { kunci: "gua", nama: "Cave", dim: "overworld", jarak: 48, cek: (c) => c.gua },
  { kunci: "mineshaft", nama: "Mineshaft", dim: "overworld", jarak: 64, cek: (c) => ((c.n("rel") >= 2 || c.n("sarang") >= 3) && c.n("pagarKayu") >= 2 ? c.pos("pagarKayu") : null) },
  { kunci: "monumen", nama: "Ocean Monument", dim: "overworld", jarak: 96, cek: (c) => (c.n("prismarine") >= 5 ? c.pos("prismarine") : null) },
  { kunci: "kolam_lava", nama: "Lava Pool", dim: "overworld", jarak: 24, cek: (c) => c.lava },
  { kunci: "geode", nama: "Amethyst Geode", dim: "overworld", jarak: 24, cek: (c) => (c.n("ametis") >= 2 ? c.pos("ametis") : null) },
  { kunci: "jurang", nama: "Ravine", dim: "overworld", jarak: 48, cek: (c) => c.jurang },
  { kunci: "kuil_hutan", nama: "Jungle Temple", dim: "overworld", jarak: 48, cek: (c) => (c.n("jebakan") && c.n("lumut") >= 8 && !c.n("spawner") ? c.pos("jebakan") : null) },
  { kunci: "fosil", nama: "Fossil", dim: null, jarak: 24, cek: (c) => (c.n("tulang") >= 4 ? c.pos("tulang") : null) },
  { kunci: "kapal_karam", nama: "Shipwreck", dim: "overworld", jarak: 32, cek: (c) => (c.n("papan") >= 10 ? c.cari("peti", (b) => AIR.has(c.tipe(b.x, b.y + 1, b.z))) : null) },
  { kunci: "pondok_penyihir", nama: "Witch Hut", dim: "overworld", jarak: 32, cek: (c) => (c.n("kuali") && c.n("papanSpruce") >= 10 ? c.pos("kuali") : null) },
  { kunci: "reruntuhan_laut", nama: "Ocean Ruin", dim: "overworld", jarak: 32, cek: (c) => (c.diBawahAir("pasirAneh") ? c.pos("pasirAneh") : c.diBawahAir("kerikilAneh") ? c.pos("kerikilAneh") : null) },
  { kunci: "igloo", nama: "Igloo", dim: "overworld", jarak: 24, cek: (c) => c.cari("karpetPutih", (b) => c.tipe(b.x + 1, b.y + 1, b.z) === M("snow") || c.tipe(b.x, b.y + 1, b.z + 1) === M("snow") || c.tipe(b.x - 1, b.y + 1, b.z) === M("snow") || c.tipe(b.x, b.y + 1, b.z - 1) === M("snow")) },
  { kunci: "sumur_gurun", nama: "Desert Well", dim: "overworld", jarak: 24, cek: (c) => (c.n("slabPasir") >= 4 && !c.n("tnt") ? c.cari("slabPasir", (b) => [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dz]) => AIR.has(c.tipe(b.x + dx, b.y, b.z + dz)) || AIR.has(c.tipe(b.x + dx, b.y - 1, b.z + dz)))) : null) },
  { kunci: "bastion", nama: "Bastion Remnant", dim: "nether", jarak: 96, cek: (c) => c.pos("emasHitam") ?? (c.n("bataHitam") >= 20 ? c.pos("bataHitam") : null) },
  { kunci: "end_city", nama: "End City", dim: "the_end", jarak: 96, cek: (c) => (c.n("purpur") >= 6 ? c.pos("purpur") : null) },
  { kunci: "end_gateway", nama: "End Gateway", dim: "the_end", jarak: 32, cek: (c) => (c.n("bedrock") >= 4 && Math.hypot(c.pos("bedrock").x, c.pos("bedrock").z) >= 60 ? c.pos("bedrock") : null) },
];

export const STRUKTUR_PER_KUNCI = new Map(STRUKTUR.map((s) => [s.kunci, s]));

// --- Memori struktur ----------------------------------------------------------
const KUNCI_MEMORI = "hsp:struktur";
const MAKS_MEMORI = 500;
/** @type {{k: string, d: string, x: number, y: number, z: number}[] | undefined} */
let memori;

export function memoriStruktur() {
  if (!memori) memori = bacaJSON(world, KUNCI_MEMORI, []);
  return memori;
}

export function hapusMemoriStruktur() {
  memori = [];
  tulisJSON(world, KUNCI_MEMORI, memori);
}

/** Catat struktur baru. Mengembalikan true jika belum pernah tercatat. */
function catat(kunci, dimensiId, lok) {
  const daftar = memoriStruktur();
  const s = STRUKTUR_PER_KUNCI.get(kunci);
  if (daftar.some((m) => m.k === kunci && m.d === dimensiId && jarak(m, lok) < (s?.jarak ?? 32))) return false;
  daftar.push({ k: kunci, d: dimensiId, x: Math.floor(lok.x), y: Math.floor(lok.y), z: Math.floor(lok.z) });
  if (daftar.length > MAKS_MEMORI) daftar.splice(0, daftar.length - MAKS_MEMORI);
  tulisJSON(world, KUNCI_MEMORI, daftar);
  return true;
}

// --- Pemindaian satu kolom chunk ---------------------------------------------------
function namaDimensi(id) {
  return id.replace(/^minecraft:/, "");
}

/**
 * Pindai satu kolom chunk dan catat struktur yang dikenali.
 * Melempar error jika chunk belum termuat (pemanggil akan mencoba lagi nanti).
 * @param {import("@minecraft/server").Dimension} dim
 * @returns {string[]} kunci struktur baru yang ditemukan
 */
export function pindaiKolom(dim, cx, cz) {
  const { min, max } = dim.heightRange;
  const x0 = cx * 16;
  const z0 = cz * 16;
  const dimNama = namaDimensi(dim.id);

  /** @type {Map<string, {n: number, pos: any[]}>} */
  const hitung = new Map();
  const hasil = dim.getBlocks(new BlockVolume({ x: x0, y: min, z: z0 }, { x: x0 + 15, y: max - 1, z: z0 + 15 }), { includeTypes: SEMUA_TANDA }, false);
  let n = 0;
  for (const lok of hasil.getBlockLocationIterator()) {
    if (++n > 6000) break;
    const tipe = dim.getBlock(lok)?.typeId;
    if (!tipe) continue;
    let h = hitung.get(tipe);
    if (!h) hitung.set(tipe, (h = { n: 0, pos: [] }));
    h.n++;
    if (h.pos.length < 8) h.pos.push({ x: lok.x, y: lok.y, z: lok.z, tipe });
  }

  const ctx = {
    dimensi: dimNama,
    n: (grup) => G[grup].reduce((s, id) => s + (hitung.get(id)?.n ?? 0), 0),
    pos: (grup) => {
      for (const id of G[grup]) {
        const p = hitung.get(id)?.pos[0];
        if (p) return p;
      }
      return null;
    },
    /** Cari blok grup yang memenuhi syarat tambahan (maks 8 contoh per id). */
    cari: (grup, syarat) => {
      for (const id of G[grup]) for (const p of hitung.get(id)?.pos ?? []) if (syarat(p)) return p;
      return null;
    },
    tipe: (x, y, z) => blokAman(dim, { x, y, z })?.typeId,
    diBawahAir: (grup) => ctx.cari(grup, (p) => AIR.has(ctx.tipe(p.x, p.y + 1, p.z))) !== null,
    gua: null,
    jurang: null,
    lava: null,
  };

  if (dimNama === "overworld") {
    Object.assign(ctx, pindaiRongga(dim, x0, z0, min));
    ctx.lava = cariLava(dim, x0, z0);
  }

  const baru = [];
  for (const s of STRUKTUR) {
    if (s.dim && s.dim !== dimNama) continue;
    let lok = null;
    try {
      lok = s.cek(ctx);
    } catch {
      lok = null;
    }
    if (lok && catat(s.kunci, dim.id, lok)) baru.push(s.kunci);
  }
  return baru;
}

/** Gua & jurang: hitung udara di bawah tanah (y < 40) pada 16 sub-kolom 1x1. */
function pindaiRongga(dim, x0, z0, min) {
  const atas = 40;
  if (atas <= min) return { gua: null, jurang: null };
  let total = 0;
  let tinggi = 0;
  let sempit = 0;
  /** @type {any} */
  let posGua = null;
  /** @type {any} */
  let posJurang = null;
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      const x = x0 + 2 + i * 4;
      const z = z0 + 2 + j * 4;
      const v = dim.getBlocks(new BlockVolume({ x, y: min, z }, { x, y: atas, z }), { includeTypes: [M("air")] }, false);
      const jml = v.getCapacity();
      total += jml;
      if (jml >= 30) {
        tinggi++;
        if (!posJurang) posJurang = { x, y: Math.floor((v.getMin().y + v.getMax().y) / 2), z };
      } else if (jml < 5) {
        sempit++;
      }
      if (jml >= 6 && !posGua) posGua = { x, y: v.getMin().y + 1, z };
    }
  }
  return {
    gua: total >= 60 ? posGua : null,
    jurang: tinggi >= 1 && tinggi <= 6 && sempit >= 8 ? posJurang : null,
  };
}

/** Kolam lava permukaan (y >= 40) di overworld. */
function cariLava(dim, x0, z0) {
  const v = dim.getBlocks(new BlockVolume({ x: x0, y: 40, z: z0 }, { x: x0 + 15, y: 120, z: z0 + 15 }), { includeTypes: [M("lava")] }, false);
  if (v.getCapacity() < 6) return null;
  for (const lok of v.getBlockLocationIterator()) return { x: lok.x, y: lok.y, z: lok.z };
  return null;
}
