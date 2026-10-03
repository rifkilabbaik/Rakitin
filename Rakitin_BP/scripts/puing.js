// Puing hanyut: papan, plastik, daun palem, dan barel yang terbawa arus.
import { ItemStack, system, world } from "@minecraft/server";
import { pemilikKail } from "./kail.js";
import { isiPuing, JENIS_PUING } from "./loot.js";
import { tambahStat } from "./statistik.js";
import {
  acak,
  adalahAir,
  beriItem,
  blokAman,
  jarak,
  lautY,
  overworld,
  peluang,
  pemainTerdekat,
  pesanBar,
  pilihBerbobot,
  suara,
} from "./util.js";

const TIPE = "rakit:puing";
const MAKS_PER_PEMAIN = 8;
const UMUR_MAKS = 6000; // 5 menit
const KECEPATAN = 0.05; // blok per 2 tick
const KUNCI_ARUS = "rakit:arus";

let sudutArus = 0;
const lahir = new Map();

function vektorArus() {
  const r = (sudutArus * Math.PI) / 180;
  return { x: Math.cos(r), z: Math.sin(r) };
}

/** Arus laut berubah arah pelan-pelan supaya puing datang dari arah berbeda. */
function geserArus() {
  sudutArus = (sudutArus + acak(-40, 40) + 360) % 360;
  world.setDynamicProperty(KUNCI_ARUS, sudutArus);
}

function munculkanUntuk(player) {
  const dim = overworld();
  const ada = dim.getEntities({ type: TIPE, location: player.location, maxDistance: 40 }).length;
  if (ada >= MAKS_PER_PEMAIN || !peluang(0.6)) return;

  const arus = vektorArus();
  const mundur = acak(20, 30);
  const samping = acak(-14, 14);
  const x = Math.floor(player.location.x - arus.x * mundur - arus.z * samping);
  const z = Math.floor(player.location.z - arus.z * mundur + arus.x * samping);
  const y = lautY();
  if (!adalahAir(blokAman(dim, { x, y, z }))) return;
  if (!blokAman(dim, { x, y: y + 1, z })?.isAir) return;

  const pilihan = pilihBerbobot(JENIS_PUING);
  const e = dim.spawnEntity(TIPE, { x: x + 0.5, y: y + 0.75, z: z + 0.5 });
  e.setProperty("rakit:jenis", pilihan.jenis);
  lahir.set(e.id, system.currentTick);
}

/** Gerakkan semua puing mengikuti arus. Puing berhenti saat menabrak rakit. */
function hanyutkan() {
  const dim = overworld();
  const arus = vektorArus();
  const y = lautY();
  for (const e of dim.getEntities({ type: TIPE })) {
    const loc = e.location;
    const baru = { x: loc.x + arus.x * KECEPATAN, y: y + 0.75, z: loc.z + arus.z * KECEPATAN };
    const depan = blokAman(dim, {
      x: Math.floor(baru.x + arus.x * 0.5),
      y,
      z: Math.floor(baru.z + arus.z * 0.5),
    });
    if (!adalahAir(depan)) continue;
    e.teleport(baru);
  }
}

/** Ambil puing: isi langsung masuk inventori pemain. */
export function kumpulkan(player, e) {
  if (!e.isValid) return;
  const jenis = Number(e.getProperty("rakit:jenis") ?? 0);
  e.remove();
  const hasil = isiPuing(jenis);
  for (const h of hasil) {
    const stack = new ItemStack(h.id, 1);
    stack.amount = Math.min(h.jumlah, stack.maxAmount);
    beriItem(player, stack);
  }
  suara(player.dimension, jenis === 3 ? "random.chestopen" : "random.pop", player.location);
  const nama = JENIS_PUING.find((j) => j.jenis === jenis)?.nama ?? "Puing";
  pesanBar(player, `§a+ ${nama} §7(${hasil.length} jenis barang)`);
  tambahStat(player, "puing");
}

function periksaPengambilan() {
  const dim = overworld();
  const kail = dim.getEntities({ type: "minecraft:fishing_hook" });
  const sekarang = system.currentTick;
  for (const e of dim.getEntities({ type: TIPE })) {
    const loc = e.location;

    const dekat = pemainTerdekat(dim, loc, 1.8);
    if (dekat) {
      kumpulkan(dekat, e);
      continue;
    }

    const k = kail.find((h) => jarak(h.location, loc) <= 1.6);
    if (k) {
      const pemilik = pemilikKail(dim, k.location);
      if (pemilik) {
        kumpulkan(pemilik, e);
        continue;
      }
    }

    if (!lahir.has(e.id)) lahir.set(e.id, sekarang);
    const tua = sekarang - lahir.get(e.id) > UMUR_MAKS;
    if (tua || !pemainTerdekat(dim, loc, 64)) {
      lahir.delete(e.id);
      e.remove();
    }
  }
}

export function mulaiPuing() {
  const tersimpan = world.getDynamicProperty(KUNCI_ARUS);
  sudutArus = typeof tersimpan === "number" ? tersimpan : acak(0, 359);

  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      if (p.dimension.id === "minecraft:overworld") munculkanUntuk(p);
    }
  }, 40);
  system.runInterval(hanyutkan, 2);
  system.runInterval(periksaPengambilan, 4);
  system.runInterval(geserArus, 6000);

  world.afterEvents.entityHitEntity.subscribe(({ damagingEntity, hitEntity }) => {
    if (hitEntity.typeId !== TIPE || damagingEntity.typeId !== "minecraft:player") return;
    const player = world.getAllPlayers().find((p) => p.id === damagingEntity.id);
    if (player) kumpulkan(player, hitEntity);
  });
}
