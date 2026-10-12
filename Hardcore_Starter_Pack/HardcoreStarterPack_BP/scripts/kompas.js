// Compass Finder: kompas di tangan kiri -> navigasi ke struktur terdekat.
import { EquipmentSlot, system, world } from "@minecraft/server";
import { KOMPAS } from "./data.js";
import { atur } from "./pengaturan.js";
import { STRUKTUR_PER_KUNCI, memoriStruktur, pindaiKolom } from "./struktur.js";
import { arahKe, barSibuk, itemTangan, jarak, koordinat, partikelPenunjuk, pesanBar } from "./util.js";

/** Kolom chunk yang sudah dipindai: "dim:cx:cz" -> tick. Dipindai ulang setelah 5 menit. */
const dipindai = new Map();
const PINDAI_ULANG = 6000;

function kompasAktif(player) {
  const a = atur(player);
  return a.kompas && KOMPAS.has(itemTangan(player, EquipmentSlot.Offhand)?.typeId ?? "");
}

/** Pilih satu kolom chunk terdekat yang belum dipindai di sekitar pemain. */
function kolomBerikutnya(player, radius) {
  const cx = Math.floor(player.location.x / 16);
  const cz = Math.floor(player.location.z / 16);
  const sekarang = system.currentTick;
  let terbaik = null;
  let jTerbaik = Infinity;
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dz = -radius; dz <= radius; dz++) {
      const kunci = `${player.dimension.id}:${cx + dx}:${cz + dz}`;
      const t = dipindai.get(kunci);
      if (t !== undefined && sekarang - t < PINDAI_ULANG) continue;
      const j = dx * dx + dz * dz;
      if (j < jTerbaik) {
        jTerbaik = j;
        terbaik = { cx: cx + dx, cz: cz + dz, kunci };
      }
    }
  }
  return terbaik;
}

function pindaiUntuk(player) {
  const a = atur(player);
  const kolom = kolomBerikutnya(player, a.radiusKompas);
  if (!kolom) return;
  try {
    const baru = pindaiKolom(player.dimension, kolom.cx, kolom.cz);
    dipindai.set(kolom.kunci, system.currentTick);
    for (const k of baru) {
      if (a.strukturMati.includes(k)) continue;
      pesanBar(player, `§e[Kompas] §fDitemukan: §a${STRUKTUR_PER_KUNCI.get(k)?.nama ?? k}`);
    }
  } catch {
    // chunk belum termuat: tandai sebentar supaya dicoba lagi nanti
    dipindai.set(kolom.kunci, system.currentTick - PINDAI_ULANG + 100);
  }
}

/** 3 struktur terdekat di dimensi pemain (yang jenisnya aktif). */
function tigaTerdekat(player) {
  const a = atur(player);
  const daftar = [];
  for (const m of memoriStruktur()) {
    if (m.d !== player.dimension.id || a.strukturMati.includes(m.k)) continue;
    daftar.push({ m, j: jarak(m, player.location) });
  }
  daftar.sort((x, y) => x.j - y.j);
  return { tiga: daftar.slice(0, 3), jumlah: daftar.length };
}

function tampilkanNavigasi(player) {
  const { tiga, jumlah } = tigaTerdekat(player);
  if (!tiga.length) {
    const r = atur(player).radiusKompas;
    player.onScreenDisplay.setActionBar(`§e[Kompas] §7Mencari struktur... jelajahi area baru (jangkauan ${r} chunk)`);
    return;
  }
  const baris = tiga.map(({ m, j }) => {
    const tengah = { x: m.x + 0.5, y: m.y + 0.5, z: m.z + 0.5 };
    const nama = STRUKTUR_PER_KUNCI.get(m.k)?.nama ?? m.k;
    return `§a${nama} §f${koordinat(m)} §7(${Math.round(j)}m ${arahKe(player, tengah)})`;
  });
  player.onScreenDisplay.setActionBar(`§e[Kompas] §7${jumlah} struktur dikenal\n${baris.join("\n")}`);
  const m = tiga[0].m;
  partikelPenunjuk(player, { x: m.x + 0.5, y: m.y + 0.5, z: m.z + 0.5 }, "minecraft:villager_happy");
}

export function mulaiKompas() {
  // Pindai satu kolom chunk per pemain setiap 10 tick (ringan).
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      if (kompasAktif(p)) pindaiUntuk(p);
    }
  }, 10);
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      if (kompasAktif(p) && !barSibuk(p)) tampilkanNavigasi(p);
    }
  }, 10);
}
