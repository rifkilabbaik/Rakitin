// Outline ore: partikel berwarna (stabil) atau kirim data ke pack X-Ray (Beta) jika aktif.
import { MolangVariableMap, system } from "@minecraft/server";
import {
  BATAS_DETAK_XRAY,
  EVENT_DETAK,
  EVENT_ORE,
  MAKS_ORE,
  MAKS_OUTLINE,
  MAKS_PESAN,
  ORE,
  PARTIKEL_XY,
  PARTIKEL_XZ,
  TICK_GAMBAR,
  TICK_KIRIM_XRAY,
  WARNA_RGBA,
} from "./config.js";

/** @typedef {import("./deteksi.js").Keadaan} Keadaan */
/** @typedef {import("./deteksi.js").Ore} Ore */
/** @typedef {import("./pengaturan.js").Atur} Atur */

// --- Pack X-Ray ------------------------------------------------------------
let detakXRay = -1e9;

/** True jika pack X-Ray mengirim detak dalam 100 tick terakhir. */
export function xrayAktif() {
  return system.currentTick - detakXRay <= BATAS_DETAK_XRAY;
}

/** @param {string} teks */
function kirim(teks) {
  try {
    system.sendScriptEvent(EVENT_ORE, teks);
    return true;
  } catch {
    return false;
  }
}

/**
 * Susun pesan JSON; buang ore terjauh sampai panjangnya <= MAKS_PESAN.
 * @param {import("@minecraft/server").Player} player
 * @param {Ore[]} daftar
 */
function susunPesan(player, daftar) {
  /** @type {number[][]} */
  const o = [];
  for (let k = 0; k < daftar.length && k < MAKS_ORE; k++) {
    const b = daftar[k];
    o.push([b.x, b.y, b.z, b.i]);
  }
  const p = player.id;
  const d = player.dimension.id;
  for (;;) {
    /** @type {Record<string, string>} */
    const w = {};
    for (const e of o) w[String(e[3])] = ORE[e[3]].warna;
    const teks = JSON.stringify({ p, d, w, o });
    if (teks.length <= MAKS_PESAN || o.length === 0) return teks;
    o.pop();
  }
}

/**
 * Kirim daftar ore (maks 64, terdekat dulu) ke pack X-Ray.
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 */
function kirimOre(player, st) {
  const dim = player.dimension.id;
  // Pindah dimensi: hapus dulu kotak di dimensi lama.
  if (st.terkirim && st.dimKirim !== dim) kirimKosong(player, st);
  if (kirim(susunPesan(player, st.ore))) {
    st.terkirim = true;
    st.dimKirim = dim;
    st.tandaKirim = st.tanda;
    st.tickKirim = system.currentTick;
  }
}

/**
 * Minta pack X-Ray menghapus semua kotak milik pemain ini.
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 */
function kirimKosong(player, st) {
  if (xrayAktif()) kirim(JSON.stringify({ p: player.id, o: [] }));
  st.terkirim = false;
  st.tandaKirim = "";
  st.tickKirim = -1e9;
}

// --- Partikel --------------------------------------------------------------
/** @type {MolangVariableMap[] | undefined} */
let molangOre;

/** @param {number} i indeks ORE */
function molang(i) {
  if (!molangOre) {
    molangOre = WARNA_RGBA.map((w) => {
      const m = new MolangVariableMap();
      m.setColorRGBA("variable.warna", w);
      return m;
    });
  }
  return molangOre[i];
}

/**
 * @param {import("@minecraft/server").Player} player
 * @param {string} id
 * @param {number} x
 * @param {number} y
 * @param {number} z
 * @param {MolangVariableMap} m
 */
function partikel(player, id, x, y, z, m) {
  try {
    player.spawnParticle(id, { x, y, z }, m);
  } catch {
    // di luar dunia / chunk belum dimuat
  }
}

/**
 * 4 kotak berongga (atas, bawah, utara, selatan) = 12 rusuk kubus.
 * @param {import("@minecraft/server").Player} player
 * @param {Ore} b
 */
function gambarOutline(player, b) {
  const m = molang(b.i);
  const cx = b.x + 0.5;
  const cz = b.z + 0.5;
  partikel(player, PARTIKEL_XZ, cx, b.y + 1.001, cz, m);
  partikel(player, PARTIKEL_XZ, cx, b.y - 0.001, cz, m);
  partikel(player, PARTIKEL_XY, cx, b.y + 0.5, b.z - 0.001, m);
  partikel(player, PARTIKEL_XY, cx, b.y + 0.5, b.z + 1.001, m);
}

// --- Dipanggil deteksi.js -------------------------------------------------
/**
 * Dipanggil tiap 10 tick selama detektor aktif (setelah pemindaian).
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 * @param {Atur} atur
 */
export function perbaruiGambar(player, st, atur) {
  const sekarang = system.currentTick;
  if (xrayAktif()) {
    st.baru = [];
    if (!atur.outline) {
      if (st.terkirim) kirimKosong(player, st);
      return;
    }
    if (st.tandaKirim !== st.tanda || sekarang - st.tickKirim >= TICK_KIRIM_XRAY) kirimOre(player, st);
    return;
  }

  // X-Ray tidak aktif: pakai partikel.
  st.terkirim = false;
  if (!atur.outline) {
    st.baru = [];
    return;
  }
  if (sekarang - st.tickGambar >= TICK_GAMBAR) {
    st.tickGambar = sekarang;
    const n = Math.min(st.ore.length, MAKS_OUTLINE);
    for (let k = 0; k < n; k++) gambarOutline(player, st.ore[k]);
  } else {
    // Ore yang baru ditemukan langsung digambar, tidak menunggu siklus berikutnya.
    for (const b of st.baru) gambarOutline(player, b);
  }
  st.baru = [];
}

/**
 * Data ore berubah di luar siklus (mis. ore dipecah): segarkan X-Ray segera.
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 * @param {Atur} atur
 */
export function segarkanXRay(player, st, atur) {
  if (xrayAktif() && atur.outline && st.tandaKirim !== st.tanda) kirimOre(player, st);
}

/**
 * Detektor dimatikan: hapus outline di pack X-Ray.
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 */
export function matikanGambar(player, st) {
  kirimKosong(player, st);
  st.baru = [];
  st.tickGambar = -1e9;
}

/** Dengarkan detak dari pack X-Ray. */
export function mulaiGambar() {
  system.afterEvents.scriptEventReceive.subscribe(
    (e) => {
      if (e.id === EVENT_DETAK) detakXRay = system.currentTick;
    },
    { namespaces: ["td"] }
  );
}
