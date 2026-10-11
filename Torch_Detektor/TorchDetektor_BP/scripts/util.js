// Fungsi bantu kecil yang dipakai banyak modul.
import { EquipmentSlot, system } from "@minecraft/server";
import { ID_OBOR, RADIUS_BAWAAN, RADIUS_BELIUNG, TAG_BELIUNG, TAHAN_PESAN } from "./config.js";

/**
 * Baca dynamic property berisi JSON dari world/entity.
 * @param {import("@minecraft/server").World | import("@minecraft/server").Entity} sumber
 * @param {string} kunci
 * @param {any} bawaan
 * @returns {any}
 */
export function bacaJSON(sumber, kunci, bawaan) {
  try {
    const s = sumber.getDynamicProperty(kunci);
    return typeof s === "string" ? JSON.parse(s) : bawaan;
  } catch {
    return bawaan;
  }
}

/**
 * @param {import("@minecraft/server").World | import("@minecraft/server").Entity} sumber
 * @param {string} kunci
 * @param {unknown} nilai
 */
export function tulisJSON(sumber, kunci, nilai) {
  try {
    sumber.setDynamicProperty(kunci, JSON.stringify(nilai));
  } catch {
    // entity sudah tidak valid: abaikan
  }
}

/**
 * Posisi blok (dibulatkan ke bawah).
 * @param {import("@minecraft/server").Vector3} lokasi
 * @returns {import("@minecraft/server").Vector3}
 */
export function posBlok(lokasi) {
  return { x: Math.floor(lokasi.x), y: Math.floor(lokasi.y), z: Math.floor(lokasi.z) };
}

/**
 * getBlock yang tidak melempar error untuk chunk yang belum dimuat.
 * @param {import("@minecraft/server").Dimension} dimensi
 * @param {import("@minecraft/server").Vector3} lokasi
 */
export function blokAman(dimensi, lokasi) {
  try {
    return dimensi.getBlock(lokasi);
  } catch {
    return undefined;
  }
}

/** @param {import("@minecraft/server").Player} player */
export function perlengkapan(player) {
  try {
    return player.getComponent("minecraft:equippable");
  } catch {
    return undefined;
  }
}

/**
 * True jika Obor Detektor ada di tangan kiri (offhand).
 * @param {import("@minecraft/server").Player} player
 */
export function oborDiKiri(player) {
  return perlengkapan(player)?.getEquipment(EquipmentSlot.Offhand)?.typeId === ID_OBOR;
}

/**
 * Radius maksimum dari beliung di tangan kanan, atau 0 jika bukan beliung.
 * @param {import("@minecraft/server").Player} player
 */
export function radiusBeliung(player) {
  const item = perlengkapan(player)?.getEquipment(EquipmentSlot.Mainhand);
  if (!item) return 0;
  const r = RADIUS_BELIUNG[item.typeId];
  if (r !== undefined) return r;
  return item.hasTag(TAG_BELIUNG) ? RADIUS_BAWAAN : 0;
}

/** @param {import("@minecraft/server").Player} player */
export function hidup(player) {
  try {
    const hp = player.getComponent("minecraft:health");
    return !hp || hp.currentValue > 0;
  } catch {
    return false;
  }
}

/**
 * Suara yang hanya terdengar oleh pemain itu.
 * @param {import("@minecraft/server").Player} player
 * @param {string} id
 */
export function suaraPemain(player, id, pitch = 1, volume = 1) {
  try {
    player.playSound(id, { pitch, volume });
  } catch {
    // suara tidak ada: abaikan
  }
}

// --- Pesan actionbar -------------------------------------------------------
// HUD radar memakai actionbar tiap 10 tick; pesan lain menahan HUD sebentar
// supaya tidak langsung tertimpa.
const pesanTerakhir = new Map();

/**
 * @param {import("@minecraft/server").Player} player
 * @param {string} teks
 */
export function pesanBar(player, teks) {
  try {
    player.onScreenDisplay.setActionBar(teks);
    pesanTerakhir.set(player.id, system.currentTick);
  } catch {
    // pemain sudah keluar
  }
}

/** @param {import("@minecraft/server").Player} player */
export function barSedangDipakai(player) {
  const t = pesanTerakhir.get(player.id);
  return t !== undefined && system.currentTick - t < TAHAN_PESAN;
}

/** @param {string} idPemain */
export function lupakanPesan(idPemain) {
  pesanTerakhir.delete(idPemain);
}

// --- Log galat -------------------------------------------------------------
const galatTercatat = new Set();

/**
 * Tulis galat ke log konten sekali saja per pesan (supaya log tidak banjir).
 * @param {string} tempat
 * @param {unknown} err
 */
export function catatGalat(tempat, err) {
  const pesan = `[Torch Detektor] ${tempat}: ${err instanceof Error ? err.message : String(err)}`;
  if (galatTercatat.has(pesan) || galatTercatat.size > 50) return;
  galatTercatat.add(pesan);
  // `console` tersedia di runtime Minecraft (masuk ke log konten), tapi tidak ada di tipe es2022.
  /** @type {any} */ (globalThis).console?.warn(pesan);
}
