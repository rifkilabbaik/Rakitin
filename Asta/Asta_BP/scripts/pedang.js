// Kekuatan 4 pedang iblis Asta berdasarkan lore Black Clover.
//
//  Demon-Slayer Sword    (Pedang Pembasmi Iblis)  : anti-sihir murni, menebas & membatalkan sihir
//  Demon-Destroyer Sword (Pedang Penghancur Iblis): menghancurkan sihir yang sudah terpasang (kutukan)
//  Demon-Dweller Sword   (Pedang Penghuni Iblis)  : menyerap sihir lalu melepaskannya kembali
//  Demon-Slasher Katana  (Katana Penebas Iblis)   : tebasan anti-sihir secepat kilat
import { system, world } from "@minecraft/server";
import {
  MAKHLUK_SIHIR,
  arahDatar,
  bersihkanEfekBuruk,
  bersihkanSemuaEfek,
  dorong,
  garisPartikel,
  hancurkanProyektil,
  itemDiTangan,
  lukai,
  makhlukDiGaris,
  makhlukSekitar,
  partikel,
  pesanBar,
  pulihkan,
  setelah,
  suara,
  tambahEfek,
} from "./util.js";

// Jeda (detik) harus sama dengan COOLDOWN di tools/buat_asta.py
const JEDA = { demon_slayer: 6, demon_destroyer: 10, demon_dweller: 2, demon_slasher: 5 };
const MUATAN_MAKS = 40;
const PROP_MUATAN = "asta:muatan";

const jedaTerakhir = new Map(); // `${player.id}:${jenis}` -> tick

/** @param {import("@minecraft/server").Player} player */
function siap(player, jenis) {
  const kunci = `${player.id}:${jenis}`;
  const t = jedaTerakhir.get(kunci);
  const sisa = t === undefined ? 0 : JEDA[jenis] * 20 - (system.currentTick - t);
  if (sisa > 0) {
    pesanBar(player, `§7Kekuatan pedang belum siap (§f${Math.ceil(sisa / 20)} dtk§7)`);
    return false;
  }
  jedaTerakhir.set(kunci, system.currentTick);
  try {
    player.startItemCooldown(`asta_${jenis}`, JEDA[jenis] * 20);
  } catch {
    // tampilan jeda opsional
  }
  return true;
}

/** @param {import("@minecraft/server").Player} player */
function muatan(player) {
  const n = player.getDynamicProperty(PROP_MUATAN);
  return typeof n === "number" ? n : 0;
}

/** @param {import("@minecraft/server").Player} player */
function aturMuatan(player, n) {
  const v = Math.max(0, Math.min(MUATAN_MAKS, Math.round(n)));
  player.setDynamicProperty(PROP_MUATAN, v);
  return v;
}

/** @param {import("@minecraft/server").Player} player */
function posisiDada(player) {
  const h = player.getHeadLocation();
  return { x: h.x, y: h.y - 0.4, z: h.z };
}

// ---------------------------------------------------------------------------
// Klik kanan
// ---------------------------------------------------------------------------

/**
 * Demon-Slayer: "Tebasan Anti-Sihir" — gelombang tebasan hitam ke depan.
 * @param {import("@minecraft/server").Player} player
 */
function tebasanAntiSihir(player) {
  const dim = player.dimension;
  const awal = posisiDada(player);
  const arah = arahDatar(player);
  garisPartikel(dim, awal, arah, 7, "minecraft:critical_hit_emitter", 0.8);
  garisPartikel(dim, awal, arah, 7, "minecraft:dragon_breath_trail", 0.5);
  suara(dim, "item.trident.riptide_2", player.location, 1, 0.7);
  let kena = 0;
  for (const e of makhlukDiGaris(dim, awal, arah, 7, 2.2, player)) {
    bersihkanSemuaEfek(e);
    lukai(e, MAKHLUK_SIHIR.has(e.typeId) ? 16 : 10, player);
    dorong(e, arah, 2.2, 0.45);
    kena++;
  }
  const pr = hancurkanProyektil(dim, player.location, 7);
  pesanBar(player, `§4Tebasan Anti-Sihir! §7${kena} musuh kena${pr ? `, ${pr} serangan ditebas` : ""}`);
}

/**
 * Demon-Destroyer: "Pemecah Kutukan" — memulihkan semua yang terkena sihir.
 * @param {import("@minecraft/server").Player} player
 */
function pemecahKutukan(player) {
  const dim = player.dimension;
  const loc = player.location;
  suara(dim, "mob.zombie.remedy", loc, 1, 1.2);
  partikel(dim, "minecraft:totem_particle", { x: loc.x, y: loc.y + 1, z: loc.z });
  let teman = 0;
  for (const p of dim.getPlayers({ location: loc, maxDistance: 8 })) {
    bersihkanEfekBuruk(p);
    tambahEfek(p, "regeneration", 100, 1);
    partikel(dim, "minecraft:villager_happy", { x: p.location.x, y: p.location.y + 1.8, z: p.location.z });
    teman++;
  }
  // kutukan zombie dihancurkan: zombie villager kembali menjadi villager
  let pulih = 0;
  for (const z of dim.getEntities({ location: loc, maxDistance: 8, type: "minecraft:zombie_villager_v2" })) {
    const l = z.location;
    try {
      z.remove();
      dim.spawnEntity("minecraft:villager_v2", l);
      partikel(dim, "minecraft:villager_happy", { x: l.x, y: l.y + 1, z: l.z });
      pulih++;
    } catch {
      // abaikan
    }
  }
  // sihir musuh di sekitar ikut dihancurkan
  for (const e of makhlukSekitar(dim, loc, 8, player)) {
    if (e.typeId !== "minecraft:player") bersihkanSemuaEfek(e);
  }
  const pr = hancurkanProyektil(dim, loc, 8);
  pesanBar(
    player,
    `§cPemecah Kutukan! §7${teman} pemain dipulihkan` +
      (pulih ? `, ${pulih} villager diselamatkan` : "") +
      (pr ? `, ${pr} serangan dihancurkan` : ""),
  );
}

/**
 * Demon-Dweller: "Lepaskan Sihir" — tembakkan sihir yang sudah diserap.
 * @param {import("@minecraft/server").Player} player
 */
function lepaskanSihir(player) {
  const n = muatan(player);
  if (n <= 0) {
    pesanBar(player, "§7Belum ada sihir yang diserap. §fTangkis serangan sihir/proyektil§7 atau pukul musuh.");
    jedaTerakhir.delete(`${player.id}:demon_dweller`);
    return;
  }
  const dim = player.dimension;
  const awal = player.getHeadLocation();
  const arah = player.getViewDirection();
  const dmg = 4 + n;
  garisPartikel(dim, awal, arah, 20, "minecraft:redstone_wire_dust_particle", 0.4);
  garisPartikel(dim, awal, arah, 20, "minecraft:sonic_explosion", 4);
  suara(dim, "mob.warden.sonic_boom", player.location, 1, 1.3);
  let kena = 0;
  for (const e of makhlukDiGaris(dim, awal, arah, 20, 1.6, player)) {
    lukai(e, dmg, player);
    dorong(e, arah, 1.5, 0.3);
    kena++;
  }
  aturMuatan(player, 0);
  pesanBar(player, `§6Sihir dilepaskan! §7(${dmg} damage, ${kena} musuh kena)`);
}

/**
 * Demon-Slasher: "Tebasan Hitam Kilat" — melesat menembus musuh.
 * @param {import("@minecraft/server").Player} player
 */
function tebasanKilat(player) {
  const dim = player.dimension;
  const awal = posisiDada(player);
  const arah = arahDatar(player);
  tambahEfek(player, "resistance", 20, 3);
  dorong(player, arah, 3.4, 0.2);
  suara(dim, "item.trident.riptide_3", player.location, 1, 1.4);
  garisPartikel(dim, awal, arah, 9, "minecraft:critical_hit_emitter", 0.7);
  let kena = 0;
  for (const e of makhlukDiGaris(dim, awal, arah, 9, 2.5, player)) {
    bersihkanSemuaEfek(e);
    lukai(e, 12, player);
    kena++;
  }
  // tebasan kedua saat mendarat
  setelah(8, () => {
    if (!player.isValid) return;
    for (const e of makhlukSekitar(player.dimension, player.location, 3, player)) lukai(e, 4, player);
    partikel(player.dimension, "minecraft:huge_explosion_emitter", player.location);
  });
  pesanBar(player, `§4Tebasan Hitam Kilat! §7${kena} musuh terbelah`);
}

const KEKUATAN = {
  demon_slayer: tebasanAntiSihir,
  demon_destroyer: pemecahKutukan,
  demon_dweller: lepaskanSihir,
  demon_slasher: tebasanKilat,
};

// ---------------------------------------------------------------------------
// Komponen custom item "asta:pedang"
// ---------------------------------------------------------------------------
export const komponenPedang = {
  onUse(e, p) {
    const player = e.source;
    const jenis = /** @type {any} */ (p.params).jenis;
    const f = KEKUATAN[jenis];
    if (!f || !siap(player, jenis)) return;
    f(player);
  },
  onHitEntity(e, p) {
    const penyerang = e.attackingEntity;
    const sasaran = e.hitEntity;
    const jenis = /** @type {any} */ (p.params).jenis;
    system.run(() => {
      if (!sasaran?.isValid || !penyerang?.isValid) return;
      // semua pedang iblis bersifat anti-sihir: efek sihir musuh dibatalkan
      bersihkanSemuaEfek(sasaran);
      if (jenis === "demon_slayer" && MAKHLUK_SIHIR.has(sasaran.typeId)) {
        lukai(sasaran, 6, penyerang);
        partikel(sasaran.dimension, "minecraft:critical_hit_emitter", sasaran.location);
      }
      if (jenis === "demon_dweller" && penyerang.typeId === "minecraft:player") {
        const n = aturMuatan(penyerang, muatan(penyerang) + 2);
        pesanBar(penyerang, `§6Sihir terserap: §f${n}/${MUATAN_MAKS}`);
      }
    });
  },
};

// ---------------------------------------------------------------------------
// Pasif
// ---------------------------------------------------------------------------
const SEBAB_SIHIR = new Set([
  "magic",
  "projectile",
  "fire",
  "fireTick",
  "lava",
  "entityExplosion",
  "blockExplosion",
  "lightning",
  "wither",
  "sonicBoom",
  "freezing",
]);

function mulaiPenyerapan() {
  // Demon-Dweller menyerap serangan sihir: separuh damage dipulihkan & disimpan
  world.afterEvents.entityHurt.subscribe((ev) => {
    if (ev.hurtEntity.typeId !== "minecraft:player") return;
    const p = /** @type {import("@minecraft/server").Player} */ (ev.hurtEntity);
    if (itemDiTangan(p)?.typeId !== "asta:demon_dweller") return;
    if (!SEBAB_SIHIR.has(ev.damageSource.cause)) return;
    const serap = ev.damage * 0.5;
    if (serap <= 0) return;
    try {
      pulihkan(p, serap);
    } catch {
      // abaikan
    }
    const n = aturMuatan(p, muatan(p) + serap * 2);
    partikel(p.dimension, "minecraft:dragon_breath_trail", p.getHeadLocation());
    suara(p.dimension, "beacon.power", p.location, 0.5, 1.8);
    pesanBar(p, `§6Sihir terserap: §f${n}/${MUATAN_MAKS} §7(klik kanan untuk melepaskan)`);
  });
}

/**
 * Dipanggil tiap 10 tick dari main.js.
 * @param {import("@minecraft/server").Player} player
 */
export function pasifPedang(player) {
  const id = itemDiTangan(player)?.typeId;
  if (!id?.startsWith("asta:demon_")) return;
  switch (id) {
    case "asta:demon_slayer":
      // anti-sihir: kutukan pada pemegang langsung dibatalkan
      bersihkanEfekBuruk(player);
      break;
    case "asta:demon_destroyer":
      // menghancurkan serangan yang mendekat
      hancurkanProyektil(player.dimension, posisiDada(player), 3);
      break;
    case "asta:demon_slasher":
      tambahEfek(player, "speed", 30, 1);
      bersihkanEfekBuruk(player);
      break;
    default:
      break;
  }
}

export function mulaiPedang() {
  mulaiPenyerapan();
}

