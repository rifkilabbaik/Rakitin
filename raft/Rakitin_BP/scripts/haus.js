// Mekanisme haus: bar 0..20 yang turun seiring waktu, HUD di actionbar.
import { EntityDamageCause, system, world } from "@minecraft/server";
import { barSedangDipakai, bisaBertahan, pesanBar } from "./util.js";

const KUNCI = "rakit:haus";
const MAKS = 20;
// Dari penuh sampai habis ±12 menit saat diam/berjalan.
const LAJU_DASAR = MAKS / 720;

const cache = new Map();
const detikKering = new Map();

export function ambilHaus(player) {
  if (!cache.has(player.id)) {
    const v = player.getDynamicProperty(KUNCI);
    cache.set(player.id, typeof v === "number" ? v : MAKS);
  }
  return cache.get(player.id);
}

export function aturHaus(player, nilai) {
  const v = Math.max(0, Math.min(MAKS, nilai));
  cache.set(player.id, v);
  player.setDynamicProperty(KUNCI, v);
}

/** Dipanggil saat pemain selesai minum. */
export function minum(player, jumlah, asin) {
  aturHaus(player, ambilHaus(player) + jumlah);
  if (asin) {
    player.addEffect("nausea", 160, { amplifier: 0 });
    player.addEffect("hunger", 200, { amplifier: 0 });
    pesanBar(player, `§3Asin sekali... §b+${jumlah} haus`);
  } else {
    pesanBar(player, `§bSegar! +${jumlah} haus`);
  }
}

// Minuman/makanan vanilla yang ikut mengurangi haus.
const MINUMAN_VANILLA = {
  "minecraft:potion": 2,
  "minecraft:milk_bucket": 4,
  "minecraft:honey_bottle": 3,
  "minecraft:melon_slice": 1,
  "minecraft:mushroom_stew": 3,
  "minecraft:beetroot_soup": 3,
  "minecraft:rabbit_stew": 3,
  "minecraft:suspicious_stew": 3,
};

function teksHaus(h) {
  const n = Math.round(h / 2);
  const warna = h <= 6 ? "§c" : "§b";
  return `§9Haus ${warna}${"■".repeat(n)}§8${"■".repeat(10 - n)} §f${Math.ceil(h)}`;
}

function detak(player) {
  if (!bisaBertahan(player)) return;
  let laju = LAJU_DASAR;
  if (player.isSprinting) laju *= 2;
  if (player.isSwimming) laju *= 1.5;
  if (player.dimension.id === "minecraft:nether") laju *= 2;
  const h = ambilHaus(player) - laju;
  aturHaus(player, h);

  if (h <= 0) {
    const n = (detikKering.get(player.id) ?? 0) + 1;
    detikKering.set(player.id, n);
    if (n % 4 === 0) {
      player.applyDamage(1, { cause: EntityDamageCause.dehydration });
      pesanBar(player, "§c§lKamu kehausan! Cepat minum air!");
    }
  } else {
    detikKering.delete(player.id);
    if (h <= 6) player.addEffect("slowness", 40, { amplifier: 0, showParticles: false });
  }

  if (!barSedangDipakai(player)) player.onScreenDisplay.setActionBar(teksHaus(Math.max(0, h)));
}

export function mulaiHaus() {
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      try {
        detak(p);
      } catch {
        // pemain baru keluar di tengah detak
      }
    }
  }, 20);

  world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => {
    if (!initialSpawn) aturHaus(player, MAKS);
  });

  world.afterEvents.playerLeave.subscribe(({ playerId }) => {
    cache.delete(playerId);
    detikKering.delete(playerId);
  });

  world.afterEvents.itemCompleteUse.subscribe(({ itemStack, source }) => {
    const n = MINUMAN_VANILLA[itemStack.typeId];
    if (n) minum(source, n, false);
  });
}
