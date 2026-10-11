// Cahaya obor dinamis: blok cahaya tak terlihat (light_block_14) mengikuti pemain
// selama Obor Detektor ada di tangan kiri.
import { system, world } from "@minecraft/server";
import { BLOK_CAHAYA, KUNCI_CAHAYA, KUNCI_CAHAYA_SISA, TICK_BERSIH_CAHAYA, TICK_CAHAYA } from "./config.js";
import { bacaAtur } from "./pengaturan.js";
import { bacaJSON, blokAman, catatGalat, hidup, oborDiKiri, posBlok, tulisJSON } from "./util.js";

/** @typedef {{ d: string, x: number, y: number, z: number }} PosCahaya */

const MAKS_SISA = 64;

/** Cahaya yang sedang menyala: idPemain -> posisi. @type {Map<string, PosCahaya>} */
const aktif = new Map();
/** Cahaya yang belum bisa dihapus karena chunk-nya belum dimuat. @type {PosCahaya[]} */
let sisa = [];
let perluSimpan = false;

function simpan() {
  /** @type {Record<string, PosCahaya>} */
  const data = {};
  for (const [id, pos] of aktif) data[id] = pos;
  tulisJSON(world, KUNCI_CAHAYA, data);
  tulisJSON(world, KUNCI_CAHAYA_SISA, sisa);
  perluSimpan = false;
}

/**
 * @param {PosCahaya | undefined} a
 * @param {PosCahaya | undefined} b
 */
function samaPos(a, b) {
  return !!a && !!b && a.d === b.d && a.x === b.x && a.y === b.y && a.z === b.z;
}

/** @param {string} id */
function dimensi(id) {
  try {
    return world.getDimension(id);
  } catch {
    return undefined;
  }
}

/**
 * Hapus blok cahaya di posisi itu, HANYA jika masih light_block_14.
 * @param {PosCahaya} pos
 * @returns {boolean} false jika chunk belum dimuat (perlu dicoba lagi)
 */
function padamkanDi(pos) {
  const dim = dimensi(pos.d);
  if (!dim) return true; // dimensi tidak dikenal: lupakan saja
  const blok = blokAman(dim, pos);
  if (!blok) return false;
  try {
    if (blok.typeId === BLOK_CAHAYA) blok.setType("minecraft:air");
    return true;
  } catch {
    return false;
  }
}

/**
 * Padamkan cahaya; jika chunk belum dimuat, simpan ke daftar sisa untuk dicoba lagi.
 * @param {PosCahaya} pos
 */
function padamkan(pos) {
  if (padamkanDi(pos)) return;
  sisa.push(pos);
  if (sisa.length > MAKS_SISA) sisa.shift();
  perluSimpan = true;
}

/**
 * Matikan cahaya milik pemain (dipakai saat obor dilepas, keluar, mati, ganti dimensi).
 * @param {string} idPemain
 */
export function padamkanPemain(idPemain) {
  const pos = aktif.get(idPemain);
  if (!pos) return;
  aktif.delete(idPemain);
  perluSimpan = true;
  padamkan(pos);
}

/**
 * Posisi baru untuk cahaya: blok kepala jika udara, kalau tidak blok kaki.
 * Posisi cahaya milik sendiri yang masih menyala tetap dianggap boleh.
 * @param {import("@minecraft/server").Player} player
 * @param {PosCahaya | undefined} lama
 * @returns {PosCahaya | undefined}
 */
function cariTempat(player, lama) {
  const dim = player.dimension;
  for (const l of [player.getHeadLocation(), player.location]) {
    const p = posBlok(l);
    const pos = { d: dim.id, x: p.x, y: p.y, z: p.z };
    const blok = blokAman(dim, p);
    if (!blok) continue;
    if (blok.typeId === "minecraft:air") return pos;
    if (blok.typeId === BLOK_CAHAYA && samaPos(pos, lama)) return pos;
  }
  return undefined;
}

/** @param {import("@minecraft/server").Player} player */
function perbaruiPemain(player) {
  const lama = aktif.get(player.id);
  const nyala = hidup(player) && oborDiKiri(player) && bacaAtur(player).cahaya;
  const target = nyala ? cariTempat(player, lama) : undefined;
  if (samaPos(target, lama)) return;

  if (target) {
    const blok = blokAman(player.dimension, target);
    if (!blok) return;
    try {
      if (blok.typeId !== BLOK_CAHAYA) blok.setType(BLOK_CAHAYA);
    } catch {
      return; // gagal memasang: coba lagi siklus berikutnya
    }
    aktif.set(player.id, target);
  } else {
    aktif.delete(player.id);
  }
  perluSimpan = true;
  if (lama) padamkan(lama);
}

/** Coba lagi menghapus cahaya yatim (chunk yang tadinya belum dimuat). */
function bersihkanSisa() {
  if (sisa.length === 0) return;
  const masihAda = [];
  for (const pos of sisa) {
    // Posisi itu sekarang dipakai cahaya pemain (dipasang ulang): jangan dihapus,
    // cukup dikeluarkan dari daftar sisa.
    let dipakai = false;
    for (const a of aktif.values()) if (samaPos(a, pos)) dipakai = true;
    if (dipakai) continue;
    if (!padamkanDi(pos)) masihAda.push(pos);
  }
  if (masihAda.length !== sisa.length) {
    sisa = masihAda;
    perluSimpan = true;
  }
}

/**
 * @param {any} p
 * @returns {p is PosCahaya}
 */
function sahPos(p) {
  return (
    !!p &&
    typeof p.d === "string" &&
    Number.isFinite(p.x) &&
    Number.isFinite(p.y) &&
    Number.isFinite(p.z)
  );
}

export function mulaiCahaya() {
  // Cahaya yang tersimpan dari sesi sebelumnya sudah yatim: masukkan ke daftar sisa.
  const lama = bacaJSON(world, KUNCI_CAHAYA, {});
  const sisaLama = bacaJSON(world, KUNCI_CAHAYA_SISA, []);
  if (Array.isArray(sisaLama)) for (const p of sisaLama) if (sahPos(p)) sisa.push(p);
  if (lama && typeof lama === "object") for (const p of Object.values(lama)) if (sahPos(p)) sisa.push(p);
  if (sisa.length > MAKS_SISA) sisa = sisa.slice(-MAKS_SISA);
  bersihkanSisa();
  simpan();

  let hitung = 0;
  system.runInterval(() => {
    try {
      for (const player of world.getAllPlayers()) {
        try {
          perbaruiPemain(player);
        } catch (err) {
          catatGalat("cahaya", err);
        }
      }
      hitung += TICK_CAHAYA;
      if (hitung >= TICK_BERSIH_CAHAYA) {
        hitung = 0;
        bersihkanSisa();
      }
      if (perluSimpan) simpan();
    } catch (err) {
      catatGalat("cahaya", err);
    }
  }, TICK_CAHAYA);

  world.afterEvents.playerLeave.subscribe(({ playerId }) => {
    padamkanPemain(playerId);
    simpan();
  });
  world.afterEvents.entityDie.subscribe(
    ({ deadEntity }) => {
      padamkanPemain(deadEntity.id);
    },
    { entityTypes: ["minecraft:player"] }
  );
  world.afterEvents.playerDimensionChange.subscribe(({ player }) => {
    padamkanPemain(player.id);
  });
}
