// Awal permainan: buat rakit 5x5 + peti perlengkapan, lalu pindahkan pemain ke atasnya.
import { ItemStack, system, world } from "@minecraft/server";
import { aturHaus } from "./haus.js";
import { buatKail } from "./kail.js";
import { aturMulai } from "./statistik.js";
import { adalahAir, bacaJSON, beriItem, blokAman, overworld, tulisJSON } from "./util.js";

const KUNCI_PUSAT = "rakit:pusat";
const KUNCI_MULAI = "rakit:sudahMulai";

/** Titik tengah rakit (lokasi berdiri), atau null jika belum dibuat. */
export function pusatRakit() {
  return bacaJSON(world, KUNCI_PUSAT, null);
}

export function aturPusatRakit(pusat) {
  tulisJSON(world, KUNCI_PUSAT, pusat);
  world.setDefaultSpawnLocation(pusat);
}

function isiPeti() {
  return [
    buatKail(1),
    new ItemStack("rakit:botol_kosong", 4),
    new ItemStack("rakit:air_bersih", 3),
    new ItemStack("rakit:tombak", 1),
    new ItemStack("minecraft:bread", 5),
    new ItemStack("minecraft:campfire", 1),
    new ItemStack("rakit:fondasi_rakit", 8),
    new ItemStack("rakit:plastik", 4),
    new ItemStack("rakit:buku_catatan", 1),
  ];
}

function isiPetiAwal(lokasi, percobaan = 0) {
  const peti = blokAman(overworld(), lokasi);
  const c = peti?.getComponent("minecraft:inventory")?.container;
  if (!c) {
    if (percobaan < 10) system.runTimeout(() => isiPetiAwal(lokasi, percobaan + 1), 5);
    return;
  }
  isiPeti().forEach((item, i) => c.setItem(i, item));
}

/** Membuat rakit awal di posisi pemain. Mengembalikan pusat, atau null jika chunk belum siap. */
function buatRakitAwal(player) {
  const dim = overworld();
  const x0 = Math.floor(player.location.x);
  const z0 = Math.floor(player.location.z);
  const { min, max } = dim.heightRange;

  let permukaan;
  for (let y = max - 1; y >= min; y--) {
    const b = blokAman(dim, { x: x0, y, z: z0 });
    if (!b) return null;
    if (!b.isAir) {
      permukaan = b;
      break;
    }
  }
  if (!permukaan) return null;

  let yRakit;
  if (adalahAir(permukaan)) {
    yRakit = permukaan.location.y;
    world.setDynamicProperty("rakit:lautY", yRakit);
  } else {
    // Bukan di laut: rakit dibuat di atas tanah, permukaan laut pakai standar (62).
    yRakit = permukaan.location.y + 1;
  }

  for (let dx = -2; dx <= 2; dx++) {
    for (let dz = -2; dz <= 2; dz++) {
      dim.setBlockType({ x: x0 + dx, y: yRakit, z: z0 + dz }, "rakit:fondasi_rakit");
      for (let dy = 1; dy <= 3; dy++) {
        const atas = { x: x0 + dx, y: yRakit + dy, z: z0 + dz };
        if (!blokAman(dim, atas)?.isAir) dim.setBlockType(atas, "minecraft:air");
      }
    }
  }
  const lokasiPeti = { x: x0 - 2, y: yRakit + 1, z: z0 - 2 };
  dim.setBlockType(lokasiPeti, "minecraft:chest");
  system.runTimeout(() => isiPetiAwal(lokasiPeti), 2);

  const pusat = { x: x0, y: yRakit + 1, z: z0 };
  aturPusatRakit(pusat);
  world.setDynamicProperty("rakit:mulaiDunia", world.getAbsoluteTime());
  return pusat;
}

function kitPemainBaru(player) {
  beriItem(player, buatKail(1));
  beriItem(player, new ItemStack("rakit:botol_kosong", 2));
  beriItem(player, new ItemStack("rakit:air_bersih", 2));
  beriItem(player, new ItemStack("rakit:buku_catatan", 1));
}

function siapkanPemain(player, percobaan = 0) {
  if (!player.isValid || player.getDynamicProperty(KUNCI_MULAI)) return;
  let pusat = pusatRakit();
  let pembuat = false;
  if (!pusat) {
    pusat = buatRakitAwal(player);
    if (!pusat) {
      if (percobaan < 20) system.runTimeout(() => siapkanPemain(player, percobaan + 1), 20);
      return;
    }
    pembuat = true;
  }

  const dim = overworld();
  player.teleport({ x: pusat.x + 0.5, y: pusat.y, z: pusat.z + 0.5 }, { dimension: dim });
  player.setSpawnPoint({ dimension: dim, x: pusat.x, y: pusat.y, z: pusat.z });
  if (!pembuat) kitPemainBaru(player);
  player.setDynamicProperty(KUNCI_MULAI, true);
  aturHaus(player, 20);
  aturMulai(player);

  player.onScreenDisplay.setTitle("§b§lRakitin", {
    subtitle: "§fBertahan hidup di tengah lautan!",
    fadeInDuration: 10,
    stayDuration: 70,
    fadeOutDuration: 20,
  });
  player.sendMessage(
    "§b[Rakitin] §fSelamat datang! Buka §epeti§f di rakit untuk perlengkapan awal. " +
      "Jaga §bhaus§f, pancing barang, dan waspadai §chiu§f. Baca §eBuku Catatan Rakit§f untuk panduan."
  );
}

export function mulaiAwal() {
  world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => {
    if (!initialSpawn) return;
    system.runTimeout(() => siapkanPemain(player), 40);
  });
  // Pemain yang sudah ada saat script dimuat (misalnya setelah /reload).
  system.runTimeout(() => {
    for (const p of world.getAllPlayers()) siapkanPemain(p);
  }, 60);
}
