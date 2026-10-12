// Hold to Enchant: item yang dipegang otomatis mendapat semua enchant pada level maksimal.
//
// 1. Enchant yang cocok untuk jenis item dicari dengan canAddEnchantment pada item kosong.
// 2. Kutukan (binding, vanishing) tidak pernah dipasang; Fortune / Silk Touch dipilih di /setting.
// 3. Enchant yang ditolak API karena bentrok (mis. Sharpness + Smite) dipasang lewat loot table
//    `hsp/enchant/<item>` buatan tools/buat_loot.py, lalu daya tahan, nama, dan lore item lama disalin.
import { EnchantmentTypes, EquipmentSlot, ItemStack, system, world } from "@minecraft/server";
import { atur, versiAtur } from "./pengaturan.js";
import { perlengkapan } from "./util.js";

const KUTUKAN = new Set(["binding", "vanishing"]);
const TAMBANG = new Set(["fortune", "silk_touch"]);
const ALAT_TAMBANG = /_(pickaxe|axe|shovel|hoe)$/;

const polos = (id) => id.replace(/^minecraft:/, "");

/** Cache per jenis item: daftar enchant yang bisa dipasang ({type, id, level}). */
const cocokPerItem = new Map();

function enchantCocok(typeId) {
  let daftar = cocokPerItem.get(typeId);
  if (daftar) return daftar;
  daftar = [];
  let kosong;
  try {
    kosong = new ItemStack(typeId, 1);
  } catch {
    cocokPerItem.set(typeId, daftar);
    return daftar;
  }
  const ench = kosong.getComponent("minecraft:enchantable");
  if (ench) {
    for (const type of EnchantmentTypes.getAll()) {
      const id = polos(type.id);
      if (KUTUKAN.has(id)) continue;
      try {
        if (ench.canAddEnchantment({ type, level: 1 })) daftar.push({ type, id, level: type.maxLevel });
      } catch {
        // tidak cocok
      }
    }
  }
  cocokPerItem.set(typeId, daftar);
  return daftar;
}

/** Enchant sasaran untuk item ini menurut pengaturan pemain. */
function sasaran(item, a) {
  return enchantCocok(item.typeId).filter((e) => {
    if (a.enchantMati.includes(e.id)) return false;
    if (TAMBANG.has(e.id)) return a.pilihanTambang === e.id;
    return true;
  });
}

function kurang(item, daftar) {
  const ench = item.getComponent("minecraft:enchantable");
  if (!ench) return [];
  return daftar.filter((e) => (ench.getEnchantment(e.type)?.level ?? 0) < e.level);
}

/** Pasang lewat API. Mengembalikan enchant yang gagal (bentrok). */
function pasangLewatApi(item, daftar) {
  const ench = item.getComponent("minecraft:enchantable");
  const gagal = [];
  if (!ench) return gagal;
  for (const e of daftar) {
    const lama = ench.getEnchantment(e.type);
    try {
      if (lama) ench.removeEnchantment(e.type);
      ench.addEnchantment({ type: e.type, level: e.level });
    } catch {
      if (lama) {
        try {
          ench.addEnchantment(lama);
        } catch {
          // tidak bisa dikembalikan
        }
      }
      gagal.push(e);
    }
  }
  return gagal;
}

/** Salin data penting dari item lama ke item baru hasil loot table. */
function salinData(dari, ke) {
  ke.amount = dari.amount;
  if (dari.nameTag) ke.nameTag = dari.nameTag;
  const lore = dari.getLore();
  if (lore.length) ke.setLore(lore);
  ke.lockMode = dari.lockMode;
  ke.keepOnDeath = dari.keepOnDeath;
  const d1 = dari.getComponent("minecraft:durability");
  const d2 = ke.getComponent("minecraft:durability");
  if (d1 && d2) d2.damage = Math.min(d2.maxDurability, d1.damage);
  const w1 = dari.getComponent("minecraft:dyeable");
  const w2 = ke.getComponent("minecraft:dyeable");
  if (w1?.color && w2) w2.color = w1.color;
  for (const id of dari.getDynamicPropertyIds()) ke.setDynamicProperty(id, dari.getDynamicProperty(id));
}

/** Item penuh enchant dari loot table (bisa memuat enchant yang saling bentrok). */
function lewatLootTable(item, a) {
  const nama = polos(item.typeId);
  const varian = ALAT_TAMBANG.test(nama) ? `_${a.pilihanTambang === "silk_touch" ? "silk" : a.pilihanTambang === "fortune" ? "fortune" : "polos"}` : "";
  const lm = world.getLootTableManager();
  const tabel = lm.getLootTable(`hsp/enchant/${nama}${varian}`);
  if (!tabel) return undefined;
  const baru = (lm.generateLootFromTable(tabel) ?? []).find((it) => it.typeId === item.typeId);
  if (!baru) return undefined;
  salinData(item, baru);
  // Enchant lama yang tidak ada di tabel tetap dipertahankan (jika cocok).
  const ench = baru.getComponent("minecraft:enchantable");
  for (const e of item.getComponent("minecraft:enchantable")?.getEnchantments() ?? []) {
    if (!ench?.hasEnchantment(e.type)) {
      try {
        ench?.addEnchantment(e);
      } catch {
        // bentrok: abaikan
      }
    }
  }
  // Enchant yang dimatikan pemain dibuang lagi.
  for (const e of ench?.getEnchantments() ?? []) {
    const id = polos(e.type.id);
    if (a.enchantMati.includes(id) || KUTUKAN.has(id) || (TAMBANG.has(id) && a.pilihanTambang !== id)) {
      ench?.removeEnchantment(e.type);
    }
  }
  return baru;
}

function sidik(item, v) {
  const e = item.getComponent("minecraft:enchantable")?.getEnchantments() ?? [];
  return `${item.typeId}|${v}|${e.map((x) => `${x.type.id}:${x.level}`).sort().join(",")}`;
}

/** Sidik item yang sudah diproses per pemain+slot, supaya tidak diproses berulang. */
const sudah = new Map();

function proses(player, slot) {
  const eq = perlengkapan(player);
  const item = eq?.getEquipment(slot);
  if (!item || item.amount !== 1 || !item.getComponent("minecraft:enchantable")) return;
  const a = atur(player);
  const kunciSlot = `${player.id}:${slot}`;
  const v = versiAtur(player);
  if (sudah.get(kunciSlot) === sidik(item, v)) return;

  const daftar = kurang(item, sasaran(item, a));
  if (daftar.length) {
    let hasil = item;
    const gagal = pasangLewatApi(hasil, daftar);
    if (gagal.length) {
      const dariLoot = lewatLootTable(item, a);
      if (dariLoot) {
        hasil = dariLoot;
        pasangLewatApi(hasil, kurang(hasil, sasaran(hasil, a)));
      }
    }
    eq.setEquipment(slot, hasil);
    sudah.set(kunciSlot, sidik(hasil, v));
    return;
  }
  sudah.set(kunciSlot, sidik(item, v));
}

export function mulaiEnchant() {
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      if (!atur(p).enchant) continue;
      try {
        proses(p, EquipmentSlot.Mainhand);
        proses(p, EquipmentSlot.Offhand);
      } catch {
        // item berubah di tengah proses: coba lagi berikutnya
      }
    }
  }, 10);
  world.afterEvents.playerLeave.subscribe(({ playerId }) => {
    for (const k of sudah.keys()) if (k.startsWith(`${playerId}:`)) sudah.delete(k);
  });
}
