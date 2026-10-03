// Pulau kecil langka yang muncul di laut saat pemain menjelajah.
import { ItemStack, system, world } from "@minecraft/server";
import { sedangBerlayar } from "./layar.js";
import { isiPetiPulau } from "./loot.js";
import { kunjungiPulau } from "./statistik.js";
import { acak, adalahAir, bacaJSON, blokAman, jarak2D, lautY, overworld, peluang, tulisJSON } from "./util.js";

const KUNCI = "rakit:pulau";
const JARAK_ANTAR_PULAU = 160;

function daftarPulau() {
  return bacaJSON(world, KUNCI, []);
}

function namaArah(dx, dz) {
  if (Math.abs(dx) > Math.abs(dz)) return dx > 0 ? "Timur" : "Barat";
  return dz > 0 ? "Selatan" : "Utara";
}

/** Semua kolom di sekitar calon pulau harus laut yang cukup dalam dan sudah termuat. */
function lautCukup(dim, cx, cz, r) {
  const y = lautY();
  for (let dx = -r; dx <= r; dx += 2) {
    for (let dz = -r; dz <= r; dz += 2) {
      const atas = blokAman(dim, { x: cx + dx, y: y + 1, z: cz + dz });
      if (!atas?.isAir) return false;
      for (const d of [0, 3]) {
        if (!adalahAir(blokAman(dim, { x: cx + dx, y: y - d, z: cz + dz }))) return false;
      }
    }
  }
  return true;
}

function bangunPulau(dim, cx, cz) {
  const y = lautY();
  const r = acak(4, 6);
  const set = (x, yy, z, id) => dim.setBlockType({ x, y: yy, z }, id);

  for (let dx = -r - 1; dx <= r + 1; dx++) {
    for (let dz = -r - 1; dz <= r + 1; dz++) {
      const d = Math.sqrt(dx * dx + dz * dz);
      const x = cx + dx;
      const z = cz + dz;
      if (d <= r - 2) {
        for (let yy = y - 4; yy <= y - 1; yy++) set(x, yy, z, "minecraft:sand");
        set(x, y, z, "minecraft:dirt");
        set(x, y + 1, z, "minecraft:grass_block");
        if (d > 1.5 && peluang(0.25)) set(x, y + 2, z, "minecraft:short_grass");
      } else if (d <= r - 0.5) {
        for (let yy = y - 4; yy <= y; yy++) set(x, yy, z, "minecraft:sand");
      } else if (d <= r + 1) {
        for (let yy = y - 4; yy <= y - 1; yy++) set(x, yy, z, "minecraft:sand");
      }
    }
  }

  // Pohon di tengah pulau.
  const tinggi = acak(4, 5);
  for (let i = 0; i < tinggi; i++) set(cx, y + 2 + i, cz, "minecraft:oak_log");
  const puncak = y + 1 + tinggi;
  for (let dy = -1; dy <= 1; dy++) {
    const rr = dy === 1 ? 1 : 2;
    for (let dx = -rr; dx <= rr; dx++) {
      for (let dz = -rr; dz <= rr; dz++) {
        if (Math.abs(dx) === 2 && Math.abs(dz) === 2) continue;
        const p = { x: cx + dx, y: puncak + dy, z: cz + dz };
        if (blokAman(dim, p)?.isAir) dim.setBlockType(p, "minecraft:oak_leaves");
      }
    }
  }

  // Peti harta.
  const lokPeti = { x: cx + 2, y: y + 2, z: cz };
  set(lokPeti.x, lokPeti.y, lokPeti.z, "minecraft:chest");
  system.runTimeout(() => {
    const c = blokAman(dim, lokPeti)?.getComponent("minecraft:inventory")?.container;
    if (!c) return;
    isiPetiPulau().forEach((h, i) => {
      const stack = new ItemStack(h.id, 1);
      stack.amount = Math.min(h.jumlah, stack.maxAmount);
      c.setItem(i * 3 % c.size, stack);
    });
  }, 2);
}

function cobaBuatPulau(player) {
  const dim = overworld();
  const semua = daftarPulau();
  if (semua.some((p) => jarak2D(p, player.location) < JARAK_ANTAR_PULAU)) return;

  let sudut;
  const layar = sedangBerlayar();
  if (layar) sudut = Math.atan2(layar.dz, layar.dx) + ((Math.random() - 0.5) * Math.PI) / 3;
  else sudut = Math.random() * Math.PI * 2;
  const r = acak(40, 52);
  const cx = Math.floor(player.location.x + Math.cos(sudut) * r);
  const cz = Math.floor(player.location.z + Math.sin(sudut) * r);
  if (!lautCukup(dim, cx, cz, 8)) return;

  bangunPulau(dim, cx, cz);
  semua.push({ x: cx, z: cz });
  tulisJSON(world, KUNCI, semua.slice(-60));
  player.sendMessage(
    `§a[Pulau] §fKamu melihat pulau kecil di kejauhan, arah §b${namaArah(cx - player.location.x, cz - player.location.z)}§f!`
  );
}

export function mulaiPulau() {
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      if (p.dimension.id === "minecraft:overworld" && peluang(0.12)) cobaBuatPulau(p);
    }
  }, 400);

  // Catat kunjungan pulau untuk pencapaian.
  system.runInterval(() => {
    const semua = daftarPulau();
    if (!semua.length) return;
    for (const p of world.getAllPlayers()) {
      if (p.dimension.id !== "minecraft:overworld") continue;
      for (const pl of semua) {
        if (jarak2D(pl, p.location) <= 8 && kunjungiPulau(p, `${pl.x},${pl.z}`)) {
          p.sendMessage("§a[Pulau] §fKamu menginjakkan kaki di pulau! Cari peti hartanya.");
        }
      }
    }
  }, 40);
}
