// Fitur saat jongkok: Tree Capitator, Vein Miner, Auto Smelt, Crop Capitator, 3x3x3 Mining.
//
// Saat pemain jongkok dan memecah blok dengan alat yang cocok, pemecahan vanilla
// dibatalkan lalu script memecah blok asal + blok tambahan sendiri:
// - drop dibuat lewat loot table vanilla memakai alat pemain (Fortune/Silk Touch ikut berlaku),
// - daya tahan alat berkurang 1 per blok (Unbreaking tetap dihitung),
// - hanya blok vanilla yang disentuh, supaya tidak bentrok dengan blok addon lain,
// - blok dihancurkan bertahap (gelombang dari blok asal) dengan partikel & suara hancur vanilla.
import { GameMode, ItemStack, system, world } from "@minecraft/server";
import {
  BATANG, BLOK_SEKOP, BUAH, DAUN, DAUN_NETHER, LEBUR, ORE_PER_BLOK, TANAMAN, TERLARANG, tierAlat, tierDibutuhkan,
} from "./data.js";
import { atur } from "./pengaturan.js";
import { Kumpulan, acak, blokAman, suara } from "./util.js";

const TETANGGA = [];
for (let dx = -1; dx <= 1; dx++)
  for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) if (dx || dy || dz) TETANGGA.push([dx, dy, dz]);

const MAKS_DAUN = 1024;
const JARAK_DAUN = 6;
const MAKS_PANEN = 256;
/** Lama animasi gelombang hancur (tick) untuk Vein Miner / Capitator. */
const LAMA_ANIMASI = 20;

/** Pemain yang sedang diproses (mencegah dua proses bersamaan). */
const sibuk = new Set();

/** @returns {any} */
function state(blok, nama) {
  try {
    /** @type {any} */
    const perm = blok.permutation;
    return perm.getState(nama);
  } catch {
    return undefined;
  }
}

function jenisAlat(item) {
  if (item.hasTag("minecraft:is_pickaxe")) return "beliung";
  if (item.hasTag("minecraft:is_axe")) return "kapak";
  if (item.hasTag("minecraft:is_shovel")) return "sekop";
  if (item.hasTag("minecraft:is_hoe")) return "cangkul";
  return null;
}

const vanilla = (id) => id.startsWith("minecraft:");

function adaTag(blok, tag) {
  try {
    return blok.hasTag(tag);
  } catch {
    return false;
  }
}

/** Blok yang boleh ikut dihancurkan fitur area. */
function bolehDihancurkan(blok) {
  if (!blok || blok.isAir || blok.isLiquid) return false;
  const id = blok.typeId;
  if (!vanilla(id) || TERLARANG.has(id) || id.startsWith("minecraft:light_block")) return false;
  try {
    if (blok.getComponent("minecraft:inventory")) return false; // jangan tumpahkan isi peti/barel
  } catch {
    // tidak punya inventori
  }
  return true;
}

const POLA_KAYU = /(_planks|_log|_wood|_stem|_hyphae|bookshelf|_fence|_fence_gate|_door|_trapdoor|_stairs|_slab)$/;

/** Apakah alat ini cocok (dan cukup kuat) untuk blok tersebut di mode 3x3. */
function alatCocok(jenis, blok, alat) {
  const id = blok.typeId;
  if (jenis === "beliung") return tierAlat(alat) >= tierDibutuhkan(blok);
  if (jenis === "sekop") return BLOK_SEKOP.has(id) || id.endsWith("_concrete_powder") || adaTag(blok, "minecraft:is_shovel_item_destructible");
  if (jenis === "kapak") return BATANG.has(id) || adaTag(blok, "minecraft:is_axe_item_destructible") || (adaTag(blok, "wood") && POLA_KAYU.test(id));
  return false;
}

function siapPanen(blok) {
  const t = TANAMAN.get(blok.typeId);
  return !!t && state(blok, t.state) === t.matang;
}

/** Tentukan fitur mana yang berlaku (atau null = biarkan vanilla). */
function pilihMode(blok, alat, a) {
  const jenis = jenisAlat(alat);
  if (!jenis || !vanilla(blok.typeId)) return null;
  const id = blok.typeId;
  const ore = ORE_PER_BLOK.get(id);
  if (jenis === "beliung" && ore) {
    if (tierAlat(alat) < ore.tier) return null; // beliung terlalu lemah: biarkan vanilla
    if (a.vein) return "vein";
    if (a.tambang3) return "3x3";
    return a.lebur ? "tunggal" : null;
  }
  if (jenis === "kapak" && BATANG.has(id) && a.pohon) return "pohon";
  if (jenis === "cangkul" && a.panen && (siapPanen(blok) || BUAH.has(id))) return "panen";
  if (jenis !== "cangkul" && a.tambang3 && bolehDihancurkan(blok) && alatCocok(jenis, blok, alat)) return "3x3";
  return null;
}

// --- Mencari blok sasaran -------------------------------------------------------
const kunci = (l) => `${l.x},${l.y},${l.z}`;

/** BFS dari blok asal ke tetangga yang memenuhi `cocok`. */
function telusuri(dim, asal, cocok, maks, tetangga = TETANGGA) {
  const hasil = [asal];
  const dilihat = new Set([kunci(asal)]);
  for (let i = 0; i < hasil.length && hasil.length < maks; i++) {
    const p = hasil[i];
    for (const [dx, dy, dz] of tetangga) {
      const l = { x: p.x + dx, y: p.y + dy, z: p.z + dz };
      const k = kunci(l);
      if (dilihat.has(k)) continue;
      dilihat.add(k);
      const b = blokAman(dim, l);
      if (b && cocok(b)) {
        hasil.push(l);
        if (hasil.length >= maks) break;
      }
    }
  }
  return hasil;
}

function sasaranVein(dim, asal, blok, a) {
  const ore = ORE_PER_BLOK.get(blok.typeId);
  return telusuri(dim, asal, (b) => ORE_PER_BLOK.get(b.typeId) === ore, a.batasVein);
}

function sasaranPohon(dim, asal, blok, a) {
  const grup = BATANG.get(blok.typeId);
  const batang = telusuri(dim, asal, (b) => BATANG.get(b.typeId) === grup, a.batasPohon);
  const daunNether = DAUN_NETHER.get(grup ?? "");
  const daunAlami = (b) =>
    daunNether ? daunNether.has(b.typeId) : DAUN.has(b.typeId) && state(b, "persistent_bit") === false;

  // Daun alami yang tersambung ke batang (maks JARAK_DAUN langkah dari batang).
  const daun = [];
  const dilihat = new Set(batang.map(kunci));
  let lapis = batang;
  for (let langkah = 0; langkah < JARAK_DAUN && lapis.length && daun.length < MAKS_DAUN; langkah++) {
    const berikut = [];
    for (const p of lapis) {
      for (const [dx, dy, dz] of TETANGGA) {
        const l = { x: p.x + dx, y: p.y + dy, z: p.z + dz };
        const k = kunci(l);
        if (dilihat.has(k)) continue;
        dilihat.add(k);
        const b = blokAman(dim, l);
        if (b && daunAlami(b)) {
          berikut.push(l);
          daun.push(l);
          if (daun.length >= MAKS_DAUN) break;
        }
      }
      if (daun.length >= MAKS_DAUN) break;
    }
    lapis = berikut;
  }
  // Tanpa daun alami = kemungkinan bangunan pemain: hanya pecahkan blok asal.
  if (!daun.length) return [asal];
  return [...batang, ...daun];
}

const TETANGGA_PANEN = [];
for (let dx = -1; dx <= 1; dx++)
  for (let dz = -1; dz <= 1; dz++) for (const dy of [0, -1, 1]) if (dx || dz) TETANGGA_PANEN.push([dx, dy, dz]);

function sasaranPanen(dim, asal, blok) {
  const id = blok.typeId;
  const cocok = BUAH.has(id) ? (b) => b.typeId === id : (b) => b.typeId === id && siapPanen(b);
  return telusuri(dim, asal, cocok, MAKS_PANEN, TETANGGA_PANEN);
}

function sasaran3x3(dim, asal, jenis, alat) {
  const hasil = [asal];
  for (let dx = -1; dx <= 1; dx++)
    for (let dy = -1; dy <= 1; dy++)
      for (let dz = -1; dz <= 1; dz++) {
        if (!dx && !dy && !dz) continue;
        const l = { x: asal.x + dx, y: asal.y + dy, z: asal.z + dz };
        const b = blokAman(dim, l);
        if (bolehDihancurkan(b) && alatCocok(jenis, b, alat)) hasil.push(l);
      }
  return hasil;
}

// --- Memecah blok ---------------------------------------------------------------
function tanamUlang(blok, permAsal, drop) {
  const t = TANAMAN.get(permAsal.type.id);
  if (!t) return false;
  const bibit = drop.find((it) => it.typeId === t.bibit && it.amount > 0);
  if (!bibit) return false;
  if (bibit.amount > 1) bibit.amount -= 1;
  else drop.splice(drop.indexOf(bibit), 1);
  /** @type {any} */
  const perm = permAsal;
  blok.setPermutation(perm.withState(t.state, 0));
  return true;
}

// --- Animasi hancur -------------------------------------------------------------
// "setblock ... destroy" menampilkan partikel & suara hancur vanilla, tetapi juga menjatuhkan
// drop vanilla (tanpa Fortune/Silk Touch). Drop vanilla itu langsung dihapus di sini;
// drop yang benar dibuat sendiri lewat loot table dengan alat pemain.
/** @type {{d: string, x: number, y: number, z: number, sampai: number}[]} */
const ditekan = [];
/** Entitas item milik addon ini yang tidak boleh dihapus. */
const milikKita = new Set();

function hancurkanDenganEfek(dim, lok, blok) {
  ditekan.push({ d: dim.id, x: lok.x + 0.5, y: lok.y + 0.5, z: lok.z + 0.5, sampai: system.currentTick + 3 });
  try {
    dim.runCommand(`setblock ${lok.x} ${lok.y} ${lok.z} air destroy`);
  } catch {
    blok.setType("minecraft:air");
  }
}

function tekanDropVanilla(entity, tickMuncul) {
  if (milikKita.delete(entity.id)) return;
  while (ditekan.length && ditekan[0].sampai < system.currentTick - 3) ditekan.shift();
  if (!ditekan.length) return;
  let l;
  try {
    l = entity.location;
  } catch {
    return;
  }
  const d = entity.dimension.id;
  for (const t of ditekan) {
    if (t.sampai < tickMuncul) continue;
    if (t.d === d && Math.abs(t.x - l.x) <= 1 && Math.abs(t.y - l.y) <= 1 && Math.abs(t.z - l.z) <= 1) {
      entity.remove();
      return;
    }
  }
}

/**
 * Pecahkan satu blok: buat drop dengan alat pemain, lebur jika perlu, lalu jadikan udara.
 * @returns {number} XP yang didapat
 */
function pecahkan(dim, lok, alat, opsi, kumpulan) {
  const blok = blokAman(dim, lok);
  if (!blok || blok.isAir) return 0;
  const id = blok.typeId;
  /** @type {ItemStack[]} */
  let drop = [];
  try {
    drop = world.getLootTableManager().generateLootFromBlock(blok, alat) ?? [];
  } catch {
    drop = [];
  }
  const permAsal = blok.permutation;
  hancurkanDenganEfek(dim, lok, blok);
  if (opsi.tanamUlang) tanamUlang(blok, permAsal, drop);

  for (const it of drop) {
    const hasil = opsi.lebur ? LEBUR.get(it.typeId) : undefined;
    kumpulan.tambah(hasil ? new ItemStack(hasil, it.amount) : it);
  }
  const ore = ORE_PER_BLOK.get(id);
  return ore && !opsi.silk ? acak(ore.xp[0], ore.xp[1]) : 0;
}

function jalankan(player, dim, asal, idAwal, mode, slot) {
  const inv = player.getComponent("minecraft:inventory")?.container;
  const alat = inv?.getItem(slot);
  const blok = blokAman(dim, asal);
  if (!inv || !alat || !blok || blok.typeId !== idAwal) {
    sibuk.delete(player.id);
    return;
  }
  const a = atur(player);
  let daftar;
  if (mode === "vein") daftar = sasaranVein(dim, asal, blok, a);
  else if (mode === "pohon") daftar = sasaranPohon(dim, asal, blok, a);
  else if (mode === "panen") daftar = sasaranPanen(dim, asal, blok);
  else if (mode === "3x3") daftar = sasaran3x3(dim, asal, jenisAlat(alat), alat);
  else daftar = [asal];

  const ench = alat.getComponent("minecraft:enchantable");
  const opsi = {
    lebur: a.lebur && (mode === "vein" || mode === "3x3" || mode === "tunggal"),
    silk: !!ench?.hasEnchantment("silk_touch"),
    tanamUlang: mode === "panen",
  };
  const unbreaking = ench?.getEnchantment("unbreaking")?.level ?? 0;
  const dur = alat.getComponent("minecraft:durability");
  const maks = dur?.maxDurability ?? 0;
  let damage = dur?.damage ?? 0;
  let patah = false;
  const kumpulan = new Kumpulan();
  let xp = 0;

  // 3x3x3 pecah sekaligus; fitur lain bergelombang dari blok asal selama ±1 detik.
  const sekaligus = mode === "3x3" || mode === "tunggal";
  const perTick = sekaligus ? daftar.length : Math.max(1, Math.ceil(daftar.length / LAMA_ANIMASI));
  // Rantai pendek dibuat sedikit lebih lambat supaya gelombangnya terlihat.
  const jeda = !sekaligus && daftar.length <= 10 ? 2 : 1;
  let indeks = 0;
  const putaran = system.runInterval(() => {
    let berhenti = false;
    try {
      for (let i = 0; i < perTick && indeks < daftar.length; i++) {
        if (!player.isValid) {
          berhenti = true;
          break;
        }
        xp += pecahkan(dim, daftar[indeks++], alat, opsi, kumpulan);
        // Daya tahan: 1 per blok, dengan peluang Unbreaking 1/(level+1).
        if (dur && Math.random() < 1 / (unbreaking + 1)) {
          damage++;
          if (damage > maks) {
            patah = true;
            berhenti = true;
            break;
          }
        }
      }
    } catch {
      berhenti = true;
    }
    if (berhenti || indeks >= daftar.length) {
      system.clearRun(putaran);
      selesai();
    }
  }, jeda);

  function selesai() {
    sibuk.delete(player.id);
    for (const e of kumpulan.jatuhkan(dim, { x: asal.x + 0.5, y: asal.y + 0.5, z: asal.z + 0.5 })) milikKita.add(e.id);
    if (!player.isValid) return;
    if (xp > 0) player.addExperience(xp);

    const sekarang = inv.getItem(slot);
    if (dur && sekarang && sekarang.typeId === alat.typeId) {
      if (patah) {
        inv.setItem(slot, undefined);
        suara(dim, "random.break", player.location);
      } else {
        const d = sekarang.getComponent("minecraft:durability");
        if (d) d.damage = Math.min(maks, damage);
        inv.setItem(slot, sekarang);
      }
    }
  }
}

export function mulaiTambang() {
  world.beforeEvents.playerBreakBlock.subscribe((e) => {
    const { player, block, itemStack } = e;
    if (!itemStack || !player.isSneaking || sibuk.has(player.id)) return;
    const gm = player.getGameMode();
    if (gm === GameMode.Creative || gm === GameMode.Spectator) return;
    const mode = pilihMode(block, itemStack, atur(player));
    if (!mode) return;

    e.cancel = true;
    sibuk.add(player.id);
    const asal = { x: block.location.x, y: block.location.y, z: block.location.z };
    const dim = block.dimension;
    const idAwal = block.typeId;
    const slot = player.selectedSlotIndex;
    system.run(() => {
      try {
        jalankan(player, dim, asal, idAwal, mode, slot);
      } catch {
        sibuk.delete(player.id);
      }
    });
  });

  world.afterEvents.playerLeave.subscribe(({ playerId }) => sibuk.delete(playerId));

  world.afterEvents.entitySpawn.subscribe(({ entity }) => {
    if (entity.typeId !== "minecraft:item" && entity.typeId !== "minecraft:xp_orb") return;
    if (!ditekan.length && !milikKita.size) return;
    // Diputuskan tick berikutnya, setelah drop milik addon sempat ditandai.
    const tick = system.currentTick;
    system.run(() => {
      if (entity.isValid) tekanDropVanilla(entity, tick);
    });
  });
}
