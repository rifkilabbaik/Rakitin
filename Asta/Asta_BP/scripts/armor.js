// Set armor "Penyatuan Iblis" (Devil Union): kekuatan Asta saat menyatu dengan Liebe.
import { EquipmentSlot } from "@minecraft/server";
import { bersihkanEfekBuruk, partikel, pesanBar, perlengkapan, tambahEfek } from "./util.js";

const SET = [
  [EquipmentSlot.Head, "asta:iblis_helm"],
  [EquipmentSlot.Chest, "asta:iblis_zirah"],
  [EquipmentSlot.Legs, "asta:iblis_celana"],
  [EquipmentSlot.Feet, "asta:iblis_sepatu"],
];

const aktif = new Set();

/** @param {import("@minecraft/server").Player} player */
function jumlahBagian(player) {
  let n = 0;
  for (const [slot, id] of SET) if (perlengkapan(player, slot)?.typeId === id) n++;
  return n;
}

/**
 * Dipanggil tiap 10 tick dari main.js.
 * @param {import("@minecraft/server").Player} player
 */
export function pasifArmor(player) {
  const n = jumlahBagian(player);
  if (n >= 2) {
    // tubuh iblis: kutukan & racun dinetralkan
    bersihkanEfekBuruk(player);
  }
  if (n < 4) {
    if (aktif.delete(player.id)) pesanBar(player, "§7Penyatuan Iblis berakhir.");
    return;
  }
  // set lengkap: kekuatan fisik iblis
  tambahEfek(player, "strength", 40, 1);
  tambahEfek(player, "speed", 40, 0);
  tambahEfek(player, "jump_boost", 40, 1);
  tambahEfek(player, "resistance", 40, 0);
  tambahEfek(player, "night_vision", 260, 0);
  if (!aktif.has(player.id)) {
    aktif.add(player.id);
    pesanBar(player, "§4§lPENYATUAN IBLIS! §r§cKekuatan Liebe mengalir...");
    partikel(player.dimension, "minecraft:huge_explosion_emitter", player.location);
  }
  if (Math.random() < 0.3) {
    const l = player.location;
    partikel(player.dimension, "minecraft:redstone_wire_dust_particle", {
      x: l.x + (Math.random() - 0.5),
      y: l.y + Math.random() * 1.8,
      z: l.z + (Math.random() - 0.5),
    });
  }
}
