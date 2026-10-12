// Cahaya obor: Torch Detector (atau obor biasa) yang dipegang di tangan mana pun
// menerangi sekitar pemain dengan blok cahaya tak terlihat yang ikut berpindah.
import { EquipmentSlot, system, world } from "@minecraft/server";
import { OBOR } from "./data.js";
import { atur } from "./pengaturan.js";
import { bacaJSON, blokAman, itemTangan, tulisJSON } from "./util.js";

const CAHAYA = "minecraft:light_block_14";
const KUNCI = "hsp:cahaya";

/** Cahaya aktif per pemain: { d, x, y, z } */
let aktif = new Map();
/** Cahaya lama yang belum bisa dihapus karena chunk-nya belum termuat. */
let sisa = [];

function simpan() {
  tulisJSON(world, KUNCI, { aktif: Object.fromEntries(aktif), sisa });
}

function pegangObor(player) {
  return (
    OBOR.has(itemTangan(player, EquipmentSlot.Offhand)?.typeId ?? "") ||
    OBOR.has(itemTangan(player, EquipmentSlot.Mainhand)?.typeId ?? "")
  );
}

/** Hapus blok cahaya di lokasi tsb. Mengembalikan false jika chunk belum termuat. */
function hapus(pos) {
  let dim;
  try {
    dim = world.getDimension(pos.d);
  } catch {
    return true;
  }
  const b = blokAman(dim, pos);
  if (!b) return false;
  if (b.typeId === CAHAYA) b.setType("minecraft:air");
  return true;
}

function sama(a, b) {
  return a && b && a.d === b.d && a.x === b.x && a.y === b.y && a.z === b.z;
}

function dipakaiPemainLain(pos, id) {
  for (const [lain, p] of aktif) if (lain !== id && sama(p, pos)) return true;
  return false;
}

function lepas(id) {
  const lama = aktif.get(id);
  if (!lama) return;
  aktif.delete(id);
  if (!dipakaiPemainLain(lama, id) && !hapus(lama)) sisa.push(lama);
}

function perbarui(player) {
  const lama = aktif.get(player.id);
  const nyala = atur(player).cahaya && pegangObor(player);
  if (!nyala) {
    if (lama) lepas(player.id);
    return;
  }
  const dim = player.dimension;
  const kepala = player.getHeadLocation();
  const calon = [
    { x: Math.floor(kepala.x), y: Math.floor(kepala.y), z: Math.floor(kepala.z) },
    { x: Math.floor(player.location.x), y: Math.floor(player.location.y), z: Math.floor(player.location.z) },
  ];
  for (const c of calon) {
    const pos = { d: dim.id, ...c };
    if (sama(lama, pos)) return;
    const b = blokAman(dim, c);
    if (!b) continue;
    if (b.typeId !== "minecraft:air" && b.typeId !== CAHAYA) continue;
    if (b.typeId === "minecraft:air") b.setType(CAHAYA);
    if (lama) lepas(player.id);
    aktif.set(player.id, pos);
    return;
  }
  // Tidak ada tempat (mis. di dalam air): matikan cahaya lama.
  if (lama) lepas(player.id);
}

export function mulaiCahaya() {
  const data = bacaJSON(world, KUNCI, { aktif: {}, sisa: [] });
  // Semua cahaya tersimpan dari sesi sebelumnya dibersihkan.
  sisa = [...Object.values(data.aktif ?? {}), ...(data.sisa ?? [])];
  aktif = new Map();

  system.runInterval(() => {
    const awal = JSON.stringify([...aktif]) + sisa.length;
    for (const p of world.getAllPlayers()) {
      try {
        perbarui(p);
      } catch {
        // pemain sedang berpindah dimensi
      }
    }
    if (sisa.length) sisa = sisa.filter((pos) => dipakaiPemainLain(pos, "") || !hapus(pos));
    if (JSON.stringify([...aktif]) + sisa.length !== awal) simpan();
  }, 4);

  world.afterEvents.playerLeave.subscribe(({ playerId }) => {
    lepas(playerId);
    simpan();
  });
  world.afterEvents.entityDie.subscribe(({ deadEntity }) => {
    if (deadEntity.typeId === "minecraft:player") lepas(deadEntity.id);
  });
}
