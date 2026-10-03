// Berlayar: Kemudi + Layar memindahkan seluruh rakit (beserta isi peti) 1 blok
// per langkah ke arah yang dipilih, memakai perintah /structure.
import { system, world } from "@minecraft/server";
import { aturPusatRakit, pusatRakit } from "./awal.js";
import { adalahAir, arahPandang, bacaJSON, blokAman, overworld, pesanBar, tulisJSON } from "./util.js";

const KUNCI = "rakit:pelayaran";
const TINGGI = 8; // blok di atas lantai rakit yang ikut berpindah
const UKURAN_MAKS = 32;
const SEL_MAKS = 600;
const FONDASI = new Set(["rakit:fondasi_rakit", "rakit:fondasi_kuat"]);
const BOLEH_DILEWATI = new Set([
  "minecraft:air",
  "minecraft:water",
  "minecraft:flowing_water",
  "minecraft:seagrass",
  "minecraft:kelp",
  "minecraft:bubble_column",
]);
// Selang langkah (tick) menurut jumlah layar.
const SELANG = { 1: 40, 2: 30, 3: 20 };

function bacaPelayaran() {
  return bacaJSON(world, KUNCI, null);
}

function simpanPelayaran(st) {
  tulisJSON(world, KUNCI, st);
}

function berhenti(alasan) {
  simpanPelayaran(null);
  if (alasan) world.sendMessage(`§e[Layar] §f${alasan}`);
}

/** Cari semua fondasi yang tersambung (4 arah) pada ketinggian y. */
function pindaiRakit(dim, mulai) {
  const awal = blokAman(dim, mulai);
  if (!awal || !FONDASI.has(awal.typeId)) return null;
  const y = mulai.y;
  const sel = new Set();
  const antrian = [[mulai.x, mulai.z]];
  sel.add(`${mulai.x},${mulai.z}`);
  let minX = mulai.x;
  let maxX = mulai.x;
  let minZ = mulai.z;
  let maxZ = mulai.z;
  while (antrian.length) {
    const [x, z] = antrian.pop();
    for (const [ox, oz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = x + ox;
      const nz = z + oz;
      const k = `${nx},${nz}`;
      if (sel.has(k)) continue;
      const b = blokAman(dim, { x: nx, y, z: nz });
      if (!b || !FONDASI.has(b.typeId)) continue;
      sel.add(k);
      if (sel.size > SEL_MAKS) return { terlaluBesar: true };
      minX = Math.min(minX, nx);
      maxX = Math.max(maxX, nx);
      minZ = Math.min(minZ, nz);
      maxZ = Math.max(maxZ, nz);
      antrian.push([nx, nz]);
    }
  }
  if (maxX - minX + 1 > UKURAN_MAKS || maxZ - minZ + 1 > UKURAN_MAKS) return { terlaluBesar: true };

  let layar = 0;
  for (const k of sel) {
    const [x, z] = k.split(",").map(Number);
    for (let dy = 1; dy <= TINGGI; dy++) {
      if (blokAman(dim, { x, y: y + dy, z })?.typeId === "rakit:layar") layar++;
    }
  }
  return { y, minX, maxX, minZ, maxZ, layar, jumlah: sel.size };
}

export function infoLayar(player, block) {
  const rakit = pindaiRakit(block.dimension, { x: block.location.x, y: block.location.y - 1, z: block.location.z });
  const n = rakit && !rakit.terlaluBesar ? rakit.layar : 0;
  pesanBar(player, `§fLayar terpasang. §7Layar di rakit ini: §e${n}§7. Gunakan §fKemudi§7 untuk berlayar.`);
}

export function interaksiKemudi(player, block) {
  const loc = block.location;
  const st = bacaPelayaran();
  if (st && st.x === loc.x && st.y === loc.y && st.z === loc.z) {
    berhenti(`${player.name} menurunkan layar. Rakit berhenti.`);
    return;
  }
  const rakit = pindaiRakit(block.dimension, { x: loc.x, y: loc.y - 1, z: loc.z });
  if (!rakit) {
    pesanBar(player, "§cKemudi harus dipasang tepat di atas Fondasi Rakit.");
    return;
  }
  if (rakit.terlaluBesar) {
    pesanBar(player, `§cRakit terlalu besar untuk berlayar (maks ${UKURAN_MAKS}x${UKURAN_MAKS}).`);
    return;
  }
  if (rakit.layar === 0) {
    pesanBar(player, "§cPasang minimal 1 Layar di atas rakit.");
    return;
  }
  const arah = arahPandang(player);
  simpanPelayaran({ x: loc.x, y: loc.y, z: loc.z, dx: arah.dx, dz: arah.dz, nama: arah.nama, tunggu: 0 });
  world.sendMessage(
    `§e[Layar] §f${player.name} mengembangkan layar! Rakit berlayar ke §b${arah.nama}§f ` +
      `(${Math.min(rakit.layar, 3)} layar). Klik kemudi lagi untuk berhenti.`
  );
}

function dalamKotak(p, x1, y1, z1, x2, y2, z2) {
  return p.x >= x1 && p.x < x2 + 1 && p.y >= y1 && p.y < y2 + 1 && p.z >= z1 && p.z < z2 + 1;
}

function langkah() {
  const st = bacaPelayaran();
  if (!st) return;
  const dim = overworld();
  const kemudi = blokAman(dim, st);
  if (kemudi?.typeId !== "rakit:kemudi") {
    berhenti("Kemudi tidak ditemukan. Pelayaran berhenti.");
    return;
  }
  const rakit = pindaiRakit(dim, { x: st.x, y: st.y - 1, z: st.z });
  if (!rakit || rakit.terlaluBesar || rakit.layar === 0) {
    berhenti("Rakit tidak bisa berlayar lagi (layar/fondasi hilang).");
    return;
  }

  st.tunggu += 10;
  if (st.tunggu < SELANG[Math.min(rakit.layar, 3)]) {
    simpanPelayaran(st);
    return;
  }
  st.tunggu = 0;

  const { dx, dz } = st;
  const x1 = rakit.minX;
  const x2 = rakit.maxX;
  const z1 = rakit.minZ;
  const z2 = rakit.maxZ;
  const y1 = rakit.y;
  const y2 = rakit.y + TINGGI;

  // Periksa irisan baru di depan rakit.
  const xs = dx > 0 ? [x2 + 1] : dx < 0 ? [x1 - 1] : range(x1, x2);
  const zs = dz > 0 ? [z2 + 1] : dz < 0 ? [z1 - 1] : range(z1, z2);
  for (const x of xs) {
    for (const z of zs) {
      for (let y = y1; y <= y2; y++) {
        const b = blokAman(dim, { x, y, z });
        if (!b) {
          berhenti("Wilayah di depan belum termuat. Pelayaran berhenti.");
          return;
        }
        if (!BOLEH_DILEWATI.has(b.typeId)) {
          berhenti("Rakit menabrak sesuatu! Pelayaran berhenti.");
          return;
        }
      }
      if (!adalahAir(blokAman(dim, { x, y: y1, z }))) {
        berhenti("Air di depan terlalu dangkal. Pelayaran berhenti.");
        return;
      }
    }
  }

  try {
    dim.runCommand(`structure save rakitin_layar ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} false memory true`);
    dim.runCommand(`fill ${x1} ${y1} ${z1} ${x2} ${y1} ${z2} water`);
    dim.runCommand(`fill ${x1} ${y1 + 1} ${z1} ${x2} ${y2} ${z2} air`);
    dim.runCommand(`structure load rakitin_layar ${x1 + dx} ${y1} ${z1 + dz}`);
  } catch (err) {
    berhenti(`Gagal memindahkan rakit: ${err}`);
    return;
  }

  // Pindahkan entitas di atas rakit (pemain, item, hewan).
  const lewati = new Set(["rakit:hiu", "rakit:puing", "minecraft:fishing_hook"]);
  const entitas = dim.getEntities({
    location: { x: x1, y: y1, z: z1 },
    volume: { x: x2 - x1 + 1, y: TINGGI + 2, z: z2 - z1 + 1 },
  });
  for (const e of entitas) {
    if (lewati.has(e.typeId)) continue;
    const l = e.location;
    e.teleport({ x: l.x + dx, y: l.y, z: l.z + dz }, { rotation: e.getRotation() });
  }

  // Titik spawn dan pusat rakit ikut bergeser.
  for (const p of world.getAllPlayers()) {
    const sp = p.getSpawnPoint();
    if (sp && sp.dimension.id === dim.id && dalamKotak(sp, x1, y1, z1, x2, y2 + 1, z2)) {
      p.setSpawnPoint({ dimension: dim, x: sp.x + dx, y: sp.y, z: sp.z + dz });
    }
  }
  const pusat = pusatRakit();
  if (pusat && dalamKotak(pusat, x1, y1, z1, x2, y2 + 1, z2)) {
    aturPusatRakit({ x: pusat.x + dx, y: pusat.y, z: pusat.z + dz });
  }

  st.x += dx;
  st.z += dz;
  simpanPelayaran(st);
}

function range(a, b) {
  const hasil = [];
  for (let i = a; i <= b; i++) hasil.push(i);
  return hasil;
}

export function mulaiLayar() {
  system.runInterval(() => {
    try {
      langkah();
    } catch (err) {
      berhenti(`Pelayaran berhenti karena galat: ${err}`);
    }
  }, 10);
}

export function sedangBerlayar() {
  const st = bacaPelayaran();
  return st ? { dx: st.dx, dz: st.dz } : null;
}
