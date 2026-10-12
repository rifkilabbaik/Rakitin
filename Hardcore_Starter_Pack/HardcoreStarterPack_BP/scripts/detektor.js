// Ore Detector: obor di tangan kiri -> navigasi ke ore terdekat.
import { BlockVolume, EquipmentSlot, system, world } from "@minecraft/server";
import { OBOR, ORE, ORE_PER_BLOK } from "./data.js";
import { atur, versiAtur } from "./pengaturan.js";
import { arahKe, barSibuk, itemTangan, jarak, koordinat, partikelPenunjuk } from "./util.js";

/** Cache per pemain: posisi pindai terakhir + daftar ore. */
const cache = new Map();

function detektorAktif(player) {
  return atur(player).detektor && OBOR.has(itemTangan(player, EquipmentSlot.Offhand)?.typeId ?? "");
}

function idOreAktif(player) {
  const mati = atur(player).oreMati;
  return ORE.filter((o) => !mati.includes(o.kunci)).flatMap((o) => o.blok);
}

/** Pindai ore dalam kubus radius r di sekitar kepala pemain. */
function pindai(player) {
  const a = atur(player);
  const dim = player.dimension;
  const kepala = player.getHeadLocation();
  const p = { x: Math.floor(kepala.x), y: Math.floor(kepala.y), z: Math.floor(kepala.z) };
  const r = a.radiusDetektor;
  const { min, max } = dim.heightRange;
  const daftar = [];
  const id = idOreAktif(player);
  if (id.length) {
    const dari = { x: p.x - r, y: Math.max(min, p.y - r), z: p.z - r };
    const ke = { x: p.x + r, y: Math.min(max - 1, p.y + r), z: p.z + r };
    if (dari.y <= ke.y) {
      const hasil = dim.getBlocks(new BlockVolume(dari, ke), { includeTypes: id }, true);
      for (const lok of hasil.getBlockLocationIterator()) {
        const tengah = { x: lok.x + 0.5, y: lok.y + 0.5, z: lok.z + 0.5 };
        const j = jarak(tengah, kepala);
        if (j > r + 0.5) continue;
        daftar.push({ lok: tengah, j });
        if (daftar.length >= 3000) break;
      }
    }
  }
  daftar.sort((x, y) => x.j - y.j);
  // Jenis ore hanya dicek untuk 64 terdekat (hemat getBlock).
  const dekat = daftar.slice(0, 64);
  for (const d of dekat) {
    d.ore = ORE_PER_BLOK.get(dim.getBlock({ x: Math.floor(d.lok.x), y: Math.floor(d.lok.y), z: Math.floor(d.lok.z) })?.typeId ?? "");
  }
  cache.set(player.id, {
    pos: p,
    dim: dim.id,
    tick: system.currentTick,
    versi: versiAtur(player),
    total: daftar.length,
    daftar: dekat.filter((d) => d.ore),
  });
}

function perluPindai(player) {
  const c = cache.get(player.id);
  if (!c) return true;
  const k = player.getHeadLocation();
  return (
    c.dim !== player.dimension.id ||
    c.versi !== versiAtur(player) ||
    system.currentTick - c.tick >= 40 ||
    Math.floor(k.x) !== c.pos.x || Math.floor(k.y) !== c.pos.y || Math.floor(k.z) !== c.pos.z
  );
}

/** 3 deposit ore terdekat (blok sejenis yang berdempetan dihitung satu deposit). */
function tigaTerdekat(daftar, kepala) {
  const urut = daftar.map((d) => ({ ...d, j: jarak(d.lok, kepala) })).sort((a, b) => a.j - b.j);
  const pilih = [];
  for (const d of urut) {
    if (pilih.some((p) => p.ore === d.ore && jarak(p.lok, d.lok) <= 2.5)) continue;
    pilih.push(d);
    if (pilih.length >= 3) break;
  }
  return pilih;
}

function tampilkan(player) {
  const c = cache.get(player.id);
  const r = atur(player).radiusDetektor;
  const kepala = player.getHeadLocation();
  const tiga = c ? tigaTerdekat(c.daftar, kepala) : [];
  if (!tiga.length) {
    player.onScreenDisplay.setActionBar(`§6[Detektor] §7Tidak ada ore dalam ${r} blok`);
    return;
  }
  const baris = tiga.map(
    (d) => `${d.ore.warna}${d.ore.nama} §f${koordinat(d.lok)} §7(${Math.round(d.j)}m ${arahKe(player, d.lok)})`
  );
  player.onScreenDisplay.setActionBar(`§6[Detektor] §7${c.total} ore dalam ${r} blok\n${baris.join("\n")}`);
  partikelPenunjuk(player, tiga[0].lok, "minecraft:blue_flame_particle");
}

export function mulaiDetektor() {
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      if (!detektorAktif(p)) {
        cache.delete(p.id);
        continue;
      }
      try {
        if (perluPindai(p)) pindai(p);
      } catch {
        // area di luar dunia / chunk belum siap: coba lagi di putaran berikutnya
      }
      if (!barSibuk(p)) tampilkan(p);
    }
  }, 10);

  // Ore yang ditambang langsung hilang dari daftar.
  world.afterEvents.playerBreakBlock.subscribe(({ player }) => cache.delete(player.id));
}
