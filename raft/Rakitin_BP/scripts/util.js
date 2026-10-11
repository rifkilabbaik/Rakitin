// Fungsi bantu yang dipakai banyak modul.
import { GameMode, ItemStack, system, world } from "@minecraft/server";

export function overworld() {
  return world.getDimension("overworld");
}

/** Bilangan bulat acak min..max (inklusif). */
export function acak(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

export function peluang(p) {
  return Math.random() < p;
}

/** Pilih satu entri dari daftar berbobot `[{ bobot, ... }]`. */
export function pilihBerbobot(daftar) {
  let total = 0;
  for (const d of daftar) total += d.bobot;
  let r = Math.random() * total;
  for (const d of daftar) {
    r -= d.bobot;
    if (r < 0) return d;
  }
  return daftar[daftar.length - 1];
}

export function jarak(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const dz = a.z - b.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

export function jarak2D(a, b) {
  const dx = a.x - b.x;
  const dz = a.z - b.z;
  return Math.sqrt(dx * dx + dz * dz);
}

/** Baca dynamic property berisi JSON dari world/entity. */
export function bacaJSON(sumber, kunci, bawaan) {
  try {
    const s = sumber.getDynamicProperty(kunci);
    return typeof s === "string" ? JSON.parse(s) : bawaan;
  } catch {
    return bawaan;
  }
}

export function tulisJSON(sumber, kunci, nilai) {
  sumber.setDynamicProperty(kunci, JSON.stringify(nilai));
}

/** @param {import("@minecraft/server").Player} player */
export function inventori(player) {
  return player.getComponent("minecraft:inventory")?.container;
}

/** Masukkan item ke inventori; jika penuh, jatuhkan di dekat pemain. */
export function beriItem(player, item) {
  const c = inventori(player);
  const sisa = c ? c.addItem(item) : item;
  if (sisa) player.dimension.spawnItem(sisa, player.location);
}

export function beriItemId(player, id, jumlah = 1) {
  let sisa = jumlah;
  while (sisa > 0) {
    const stack = new ItemStack(id, 1);
    const n = Math.min(sisa, stack.maxAmount);
    stack.amount = n;
    beriItem(player, stack);
    sisa -= n;
  }
}

/** @param {import("@minecraft/server").Player} player */
export function itemDiTangan(player) {
  return inventori(player)?.getItem(player.selectedSlotIndex);
}

export function modeKreatif(player) {
  return player.getGameMode() === GameMode.Creative;
}

/** True untuk mode Survival/Adventure (yang kena haus, diserang hiu, dll). */
export function bisaBertahan(player) {
  const m = player.getGameMode();
  return m === GameMode.Survival || m === GameMode.Adventure;
}

/** Kurangi item di tangan sebanyak n (tidak berlaku di Kreatif). */
export function pakaiItemDiTangan(player, n = 1) {
  if (modeKreatif(player)) return;
  const c = inventori(player);
  if (!c) return;
  const slot = player.selectedSlotIndex;
  const it = c.getItem(slot);
  if (!it) return;
  if (it.amount > n) {
    it.amount -= n;
    c.setItem(slot, it);
  } else {
    c.setItem(slot, undefined);
  }
}

// --- Pesan actionbar -------------------------------------------------------
// HUD haus memakai actionbar tiap detik; pesan lain menahan HUD sebentar
// supaya tidak langsung tertimpa.
const pesanTerakhir = new Map();

/** @param {string | import("@minecraft/server").RawMessage} teks */
export function pesanBar(player, teks) {
  player.onScreenDisplay.setActionBar(teks);
  pesanTerakhir.set(player.id, system.currentTick);
}

export function barSedangDipakai(player) {
  const t = pesanTerakhir.get(player.id);
  return t !== undefined && system.currentTick - t < 50;
}

export function pesanSemua(teks) {
  world.sendMessage(teks);
}

export function suara(dimensi, id, lokasi, volume = 1, pitch = 1) {
  try {
    dimensi.playSound(id, lokasi, { volume, pitch });
  } catch {
    // suara tidak ada di versi ini: abaikan
  }
}

export function partikel(dimensi, id, lokasi) {
  try {
    dimensi.spawnParticle(id, lokasi);
  } catch {
    // partikel tidak ada / chunk belum dimuat
  }
}

// --- Blok & dunia ----------------------------------------------------------
/** getBlock yang tidak melempar error untuk chunk yang belum dimuat. */
export function blokAman(dimensi, lokasi) {
  try {
    return dimensi.getBlock(lokasi);
  } catch {
    return undefined;
  }
}

export function adalahAir(blok) {
  return !!blok && (blok.typeId === "minecraft:water" || blok.typeId === "minecraft:flowing_water");
}

/** Ketinggian permukaan laut (blok air paling atas). */
export function lautY() {
  const y = world.getDynamicProperty("rakit:lautY");
  return typeof y === "number" ? y : 62;
}

/** Arah mata angin dari pandangan pemain. */
export function arahPandang(player) {
  const yaw = ((player.getRotation().y % 360) + 360) % 360;
  if (yaw >= 315 || yaw < 45) return { dx: 0, dz: 1, nama: "Selatan" };
  if (yaw < 135) return { dx: -1, dz: 0, nama: "Barat" };
  if (yaw < 225) return { dx: 0, dz: -1, nama: "Utara" };
  return { dx: 1, dz: 0, nama: "Timur" };
}

/** Pemain terdekat dari sebuah lokasi (opsional: hanya yang memenuhi syarat). */
export function pemainTerdekat(dimensi, lokasi, maks, syarat) {
  let terbaik;
  let jTerbaik = maks;
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id !== dimensi.id) continue;
    if (syarat && !syarat(p)) continue;
    const j = jarak(p.location, lokasi);
    if (j <= jTerbaik) {
      jTerbaik = j;
      terbaik = p;
    }
  }
  return terbaik;
}

/** Ubah state blok custom (nama state tidak dikenal oleh tipe vanilla). */
export function aturState(blok, nama, nilai) {
  /** @type {any} */
  const perm = blok.permutation;
  blok.setPermutation(perm.withState(nama, nilai));
}

/** @returns {any} */
export function bacaState(blok, nama) {
  /** @type {any} */
  const perm = blok.permutation;
  return perm.getState(nama);
}
