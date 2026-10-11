// Fungsi bantu umum untuk script Asta.
import { EntityDamageCause, EquipmentSlot, system } from "@minecraft/server";

/** Efek "kutukan/sihir" yang dibatalkan oleh kekuatan anti-sihir. */
export const EFEK_BURUK = [
  "poison",
  "fatal_poison",
  "wither",
  "weakness",
  "slowness",
  "mining_fatigue",
  "nausea",
  "blindness",
  "darkness",
  "hunger",
  "levitation",
  "infested",
  "oozing",
  "weaving",
  "wind_charged",
];

/** Makhluk yang memakai sihir: kena damage tambahan dari Pedang Pembasmi Iblis. */
export const MAKHLUK_SIHIR = new Set([
  "minecraft:witch",
  "minecraft:evocation_illager",
  "minecraft:vex",
  "minecraft:blaze",
  "minecraft:ghast",
  "minecraft:enderman",
  "minecraft:endermite",
  "minecraft:shulker",
  "minecraft:guardian",
  "minecraft:elder_guardian",
  "minecraft:breeze",
  "minecraft:wither",
  "minecraft:ender_dragon",
  "minecraft:warden",
]);

/** Proyektil yang bisa ditebas/dihancurkan. */
export const PROYEKTIL = new Set([
  "minecraft:arrow",
  "minecraft:fireball",
  "minecraft:small_fireball",
  "minecraft:dragon_fireball",
  "minecraft:wither_skull",
  "minecraft:wither_skull_dangerous",
  "minecraft:shulker_bullet",
  "minecraft:llama_spit",
  "minecraft:snowball",
  "minecraft:egg",
  "minecraft:thrown_trident",
  "minecraft:splash_potion",
  "minecraft:lingering_potion",
  "minecraft:wind_charge_projectile",
  "minecraft:breeze_wind_charge_projectile",
  "minecraft:evocation_fang",
]);

const BUKAN_SASARAN = ["minecraft:item", "minecraft:xp_orb", "minecraft:arrow", "minecraft:painting", "minecraft:armor_stand"];

/** @param {import("@minecraft/server").Entity} entitas */
export function itemDiTangan(entitas) {
  try {
    return entitas.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Mainhand);
  } catch {
    return undefined;
  }
}

/** @param {import("@minecraft/server").Entity} entitas */
export function perlengkapan(entitas, slot) {
  try {
    return entitas.getComponent("minecraft:equippable")?.getEquipment(slot);
  } catch {
    return undefined;
  }
}

/** @param {import("@minecraft/server").Player} player */
export function pesanBar(player, teks) {
  try {
    player.onScreenDisplay.setActionBar(teks);
  } catch {
    // pemain keluar
  }
}

/** @param {import("@minecraft/server").Dimension} dimensi */
export function suara(dimensi, id, lokasi, volume = 1, pitch = 1) {
  try {
    dimensi.playSound(id, lokasi, { volume, pitch });
  } catch {
    // suara tidak ada di versi ini
  }
}

/** @param {import("@minecraft/server").Dimension} dimensi */
export function partikel(dimensi, id, lokasi) {
  try {
    dimensi.spawnParticle(id, lokasi);
  } catch {
    // chunk belum dimuat / partikel tidak ada
  }
}

/** @param {import("@minecraft/server").Entity} entitas */
export function tambahEfek(entitas, id, durasi, level = 0) {
  try {
    entitas.addEffect(id, durasi, { amplifier: level, showParticles: false });
  } catch {
    // efek tidak ada di versi ini
  }
}

/**
 * Hapus efek buruk saja (anti-sihir pada diri sendiri / teman).
 * @param {import("@minecraft/server").Entity} entitas
 */
export function bersihkanEfekBuruk(entitas) {
  let n = 0;
  for (const id of EFEK_BURUK) {
    try {
      if (entitas.getEffect(id)) {
        entitas.removeEffect(id);
        n++;
      }
    } catch {
      // abaikan
    }
  }
  return n;
}

/**
 * Hapus SEMUA efek (anti-sihir pada musuh: buff sihirnya ikut hilang).
 * @param {import("@minecraft/server").Entity} entitas
 */
export function bersihkanSemuaEfek(entitas) {
  try {
    for (const ef of entitas.getEffects()) entitas.removeEffect(ef.typeId);
  } catch {
    // abaikan
  }
}

/**
 * @param {import("@minecraft/server").Entity} sasaran
 * @param {import("@minecraft/server").Entity} penyerang
 */
export function lukai(sasaran, jumlah, penyerang) {
  try {
    if (sasaran.isValid) sasaran.applyDamage(jumlah, { cause: EntityDamageCause.entityAttack, damagingEntity: penyerang });
  } catch {
    // entitas kebal / sudah mati
  }
}

/** @param {import("@minecraft/server").Entity} entitas */
export function dorong(entitas, arah, kuat, naik) {
  try {
    entitas.applyKnockback({ x: arah.x * kuat, z: arah.z * kuat }, naik);
  } catch {
    // entitas tidak bisa didorong
  }
}

/** @param {import("@minecraft/server").Entity} entitas */
export function pulihkan(entitas, jumlah) {
  const hp = entitas.getComponent("minecraft:health");
  if (!hp) return;
  hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + jumlah));
}

/**
 * Makhluk hidup di sekitar lokasi selain `kecuali`.
 * @param {import("@minecraft/server").Dimension} dimensi
 */
export function makhlukSekitar(dimensi, lokasi, jarak, kecuali) {
  return dimensi
    .getEntities({ location: lokasi, maxDistance: jarak, excludeTypes: BUKAN_SASARAN })
    .filter((e) => e.id !== kecuali?.id && e.getComponent("minecraft:health"));
}

/**
 * Makhluk di sepanjang garis dari `awal` ke arah `arah` (vektor satuan)
 * sepanjang `panjang` blok dengan lebar `lebar`.
 * @param {import("@minecraft/server").Dimension} dimensi
 */
export function makhlukDiGaris(dimensi, awal, arah, panjang, lebar, kecuali) {
  const tengah = { x: awal.x + (arah.x * panjang) / 2, y: awal.y + (arah.y * panjang) / 2, z: awal.z + (arah.z * panjang) / 2 };
  return makhlukSekitar(dimensi, tengah, panjang / 2 + lebar + 1, kecuali).filter((e) => {
    const p = { x: e.location.x - awal.x, y: e.location.y + 0.9 - awal.y, z: e.location.z - awal.z };
    const t = p.x * arah.x + p.y * arah.y + p.z * arah.z;
    if (t < 0 || t > panjang) return false;
    const dx = p.x - arah.x * t;
    const dy = p.y - arah.y * t;
    const dz = p.z - arah.z * t;
    return dx * dx + dy * dy + dz * dz <= lebar * lebar;
  });
}

/**
 * Hancurkan proyektil di sekitar lokasi (anti-sihir menebas serangan).
 * @param {import("@minecraft/server").Dimension} dimensi
 */
export function hancurkanProyektil(dimensi, lokasi, jarak) {
  let n = 0;
  for (const e of dimensi.getEntities({ location: lokasi, maxDistance: jarak })) {
    if (!PROYEKTIL.has(e.typeId)) continue;
    partikel(dimensi, "minecraft:critical_hit_emitter", e.location);
    try {
      e.remove();
      n++;
    } catch {
      // abaikan
    }
  }
  return n;
}

/**
 * Arah pandang datar (tanpa komponen y), sudah dinormalkan.
 * @param {import("@minecraft/server").Player} player
 */
export function arahDatar(player) {
  const v = player.getViewDirection();
  const p = Math.hypot(v.x, v.z) || 1;
  return { x: v.x / p, y: 0, z: v.z / p };
}

/**
 * Partikel di sepanjang garis.
 * @param {import("@minecraft/server").Dimension} dimensi
 */
export function garisPartikel(dimensi, awal, arah, panjang, id, langkah = 0.6) {
  for (let s = 0; s <= panjang; s += langkah) {
    partikel(dimensi, id, { x: awal.x + arah.x * s, y: awal.y + arah.y * s, z: awal.z + arah.z * s });
  }
}

export function setelah(tick, fn) {
  system.runTimeout(fn, tick);
}
