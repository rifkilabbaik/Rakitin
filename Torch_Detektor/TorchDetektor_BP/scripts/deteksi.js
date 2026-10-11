// Loop detektor: cek aktif/nonaktif, pindai ore di sekitar, cache hasil, event blok pecah/dipasang.
import { BlockVolume, system, world } from "@minecraft/server";
import { INDEKS_BLOK, MAKS_ORE, MAKS_OUTLINE, TICK_CEK, TICK_PINDAI_ULANG } from "./config.js";
import { matikanGambar, perbaruiGambar, segarkanXRay } from "./gambar.js";
import { perbaruiHud } from "./hud.js";
import { bacaAtur, idBlokAktif, tandaAtur } from "./pengaturan.js";
import { blokAman, catatGalat, hidup, lupakanPesan, oborDiKiri, pesanBar, posBlok, radiusBeliung, suaraPemain } from "./util.js";

/** @typedef {{ x: number, y: number, z: number, i: number }} Ore */
/**
 * Keadaan detektor per pemain.
 * @typedef {{
 *   aktif: boolean,
 *   radius: number,
 *   kunciPos: string,
 *   tandaAtur: string,
 *   tickPindai: number,
 *   kotor: boolean,
 *   ore: Ore[],
 *   tanda: string,
 *   baru: Ore[],
 *   tickGambar: number,
 *   terkirim: boolean,
 *   dimKirim: string,
 *   tandaKirim: string,
 *   tickKirim: number,
 * }} Keadaan
 */

/** @type {Map<string, Keadaan>} */
const keadaan = new Map();

/** @returns {Keadaan} */
function keadaanBaru() {
  return {
    aktif: false,
    radius: 0,
    kunciPos: "",
    tandaAtur: "",
    tickPindai: -1e9,
    kotor: false,
    ore: [],
    tanda: "",
    baru: [],
    tickGambar: -1e9,
    terkirim: false,
    dimKirim: "",
    tandaKirim: "",
    tickKirim: -1e9,
  };
}

/** @param {import("@minecraft/server").Player} player */
function ambilKeadaan(player) {
  let st = keadaan.get(player.id);
  if (!st) {
    st = keadaanBaru();
    keadaan.set(player.id, st);
  }
  return st;
}

/** @param {Ore} b */
const kunciOre = (b) => `${b.x},${b.y},${b.z}`;

/**
 * Penanda isi daftar ore (untuk tahu apakah hasil pindai berubah).
 * @param {Ore[]} daftar
 */
function tandaOre(daftar) {
  return daftar.map((b) => `${b.x},${b.y},${b.z},${b.i}`).join(";");
}

/**
 * Cari ore dalam bola radius R di sekitar kepala pemain, urut dari terdekat (maks 64).
 * @param {import("@minecraft/server").Player} player
 * @param {number} radius
 * @param {string[]} idTipe
 * @returns {Ore[]}
 */
function pindai(player, radius, idTipe) {
  if (idTipe.length === 0) return [];
  const dim = player.dimension;
  const kepala = player.getHeadLocation();
  const p = posBlok(kepala);

  /** @type {{ x: number, y: number, z: number, j: number }[]} */
  const calon = [];
  try {
    const tinggi = dim.heightRange;
    const y0 = Math.max(p.y - radius, tinggi.min);
    const y1 = Math.min(p.y + radius, tinggi.max - 1);
    if (y0 > y1) return [];
    const volume = new BlockVolume({ x: p.x - radius, y: y0, z: p.z - radius }, { x: p.x + radius, y: y1, z: p.z + radius });
    const hasil = dim.getBlocks(volume, { includeTypes: idTipe }, true);
    const batas = (radius + 0.5) * (radius + 0.5);
    for (const l of hasil.getBlockLocationIterator()) {
      const dx = l.x + 0.5 - kepala.x;
      const dy = l.y + 0.5 - kepala.y;
      const dz = l.z + 0.5 - kepala.z;
      const j = dx * dx + dy * dy + dz * dz;
      if (j <= batas) calon.push({ x: l.x, y: l.y, z: l.z, j });
    }
  } catch {
    // di luar dunia / chunk belum dimuat
    return [];
  }

  calon.sort((a, b) => a.j - b.j);
  // Jenis ore hanya perlu dibaca untuk yang disimpan (maks 64).
  /** @type {Ore[]} */
  const ore = [];
  for (const c of calon) {
    if (ore.length >= MAKS_ORE) break;
    const blok = blokAman(dim, c);
    const i = blok ? INDEKS_BLOK.get(blok.typeId) : undefined;
    if (i !== undefined) ore.push({ x: c.x, y: c.y, z: c.z, i });
  }
  return ore;
}

/**
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 */
function matikan(player, st) {
  st.aktif = false;
  st.ore = [];
  st.tanda = "";
  st.kunciPos = "";
  st.kotor = false;
  matikanGambar(player, st);
}

/** @param {import("@minecraft/server").Player} player */
function cekPemain(player) {
  const st = ambilKeadaan(player);
  const radiusMaks = hidup(player) && oborDiKiri(player) ? radiusBeliung(player) : 0;

  if (radiusMaks <= 0) {
    if (st.aktif) {
      matikan(player, st);
      pesanBar(player, "§7Detektor OFF");
    }
    return;
  }

  const atur = bacaAtur(player);
  const radius = Math.min(radiusMaks, atur.batasRadius);
  const sekarang = system.currentTick;
  const baruAktif = !st.aktif;
  if (baruAktif) {
    st.aktif = true;
    suaraPemain(player, "random.orb", 1.6, 0.6);
    pesanBar(player, "§aDetektor ON");
  }

  // Pindai ulang hanya bila perlu.
  const p = posBlok(player.getHeadLocation());
  const kunciPos = `${player.dimension.id}|${p.x}|${p.y}|${p.z}`;
  const ta = `${tandaAtur(player)}|${radius}`;
  if (
    baruAktif ||
    st.kotor ||
    kunciPos !== st.kunciPos ||
    ta !== st.tandaAtur ||
    st.radius !== radius ||
    sekarang - st.tickPindai >= TICK_PINDAI_ULANG
  ) {
    const lamaDekat = new Set(st.ore.slice(0, MAKS_OUTLINE).map(kunciOre));
    st.ore = pindai(player, radius, idBlokAktif(atur));
    st.tanda = tandaOre(st.ore);
    st.radius = radius;
    st.kunciPos = kunciPos;
    st.tandaAtur = ta;
    st.tickPindai = sekarang;
    st.kotor = false;
    // Ore yang baru masuk daftar outline digambar langsung oleh gambar.js.
    st.baru = st.ore.slice(0, MAKS_OUTLINE).filter((b) => !lamaDekat.has(kunciOre(b)));
  }

  perbaruiGambar(player, st, atur);
  perbaruiHud(player, st, atur);
}

/**
 * Blok pecah/dipasang: tandai pemain di dekatnya supaya memindai ulang.
 * Jika yang pecah adalah ore, langsung hapus dari cache.
 * @param {import("@minecraft/server").Dimension} dimensi
 * @param {import("@minecraft/server").Vector3} lokasi
 * @param {boolean} orePecah
 */
function blokBerubah(dimensi, lokasi, orePecah) {
  for (const player of world.getAllPlayers()) {
    const st = keadaan.get(player.id);
    if (!st || !st.aktif) continue;
    try {
      if (player.dimension.id !== dimensi.id) continue;
      const kepala = player.getHeadLocation();
      const dx = lokasi.x + 0.5 - kepala.x;
      const dy = lokasi.y + 0.5 - kepala.y;
      const dz = lokasi.z + 0.5 - kepala.z;
      const batas = st.radius + 2;
      if (dx * dx + dy * dy + dz * dz > batas * batas) continue;
      st.kotor = true;
      if (!orePecah) continue;
      // Ore dipecah: hapus dari cache sekarang juga supaya outline-nya langsung hilang.
      const sisa = st.ore.filter((b) => b.x !== lokasi.x || b.y !== lokasi.y || b.z !== lokasi.z);
      if (sisa.length !== st.ore.length) {
        st.ore = sisa;
        st.tanda = tandaOre(sisa);
        segarkanXRay(player, st, bacaAtur(player));
      }
    } catch (err) {
      catatGalat("blok berubah", err);
    }
  }
}

export function mulaiDeteksi() {
  system.runInterval(() => {
    for (const player of world.getAllPlayers()) {
      try {
        cekPemain(player);
      } catch (err) {
        // mis. pemain sedang berpindah dimensi / keluar: coba lagi siklus berikutnya
        catatGalat("deteksi", err);
      }
    }
  }, TICK_CEK);

  world.afterEvents.playerBreakBlock.subscribe((e) => {
    blokBerubah(e.dimension, e.block.location, INDEKS_BLOK.has(e.brokenBlockPermutation.type.id));
  });
  world.afterEvents.playerPlaceBlock.subscribe((e) => {
    blokBerubah(e.dimension, e.block.location, false);
  });
  world.afterEvents.playerLeave.subscribe(({ playerId }) => {
    keadaan.delete(playerId);
    lupakanPesan(playerId);
  });
}
