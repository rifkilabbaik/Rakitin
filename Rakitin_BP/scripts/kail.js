// Kail 5 tier: membuat kail ber-enchant maksimal, mengganti hasil pancingan
// vanilla dengan tabel loot sesuai tier, dan konversi kail <-> item upgrade.
import {
  EnchantmentTypes,
  EntityInitializationCause,
  EquipmentSlot,
  ItemStack,
  system,
  world,
} from "@minecraft/server";
import { gulirTangkapan, INFO_KATEGORI, PELUANG_GANDA, peluangBagus } from "./loot.js";
import { statMaks, tambahStat } from "./statistik.js";
import {
  beriItem,
  inventori,
  jarak,
  peluang,
  pemainTerdekat,
  pesanBar,
  suara,
} from "./util.js";

export const TIER = {
  1: { nama: "Kayu", warna: "§f" },
  2: { nama: "Besi", warna: "§7" },
  3: { nama: "Emas", warna: "§e" },
  4: { nama: "Berlian", warna: "§b" },
  5: { nama: "Netherite", warna: "§d" },
};

/** @type {[string, number][]} */
const ENCHANT_MAKS = [
  ["lure", 3],
  ["luck_of_the_sea", 3],
  ["unbreaking", 3],
  ["mending", 1],
];

const PENANDA = "Rakitin";

/** Kail vanilla siap pakai dengan nama, lore tier, dan enchant maksimal. */
export function buatKail(tier) {
  const t = TIER[tier] ?? TIER[1];
  const item = new ItemStack("minecraft:fishing_rod", 1);
  item.nameTag = `§r${t.warna}Kail ${t.nama} §7(Tier ${tier})`;
  item.setLore([
    `§r§7Tier ${tier} §8${PENANDA}`,
    `§r§7Peluang tangkapan bagus: §6${peluangBagus(tier)}%`,
    `§r§7Tangkapan ganda: §a${Math.round(PELUANG_GANDA[tier] * 100)}%`,
  ]);
  const ench = item.getComponent("minecraft:enchantable");
  if (ench) {
    for (const [id, level] of ENCHANT_MAKS) {
      const type = EnchantmentTypes.get(id);
      if (!type) continue;
      try {
        ench.addEnchantment({ type, level });
      } catch {
        // enchant tidak cocok: lewati
      }
    }
  }
  return item;
}

/** Tier sebuah kail vanilla (0 = bukan kail Rakitin). */
export function tierKail(item) {
  if (!item || item.typeId !== "minecraft:fishing_rod") return 0;
  for (const baris of item.getLore()) {
    const m = /Tier (\d)/.exec(baris);
    if (m && baris.includes(PENANDA)) return Number(m[1]);
  }
  return 0;
}

function kailDiTangan(player) {
  const eq = player.getComponent("minecraft:equippable");
  const item = eq?.getEquipment(EquipmentSlot.Mainhand);
  if (item?.typeId === "minecraft:fishing_rod") return item;
  const kiri = eq?.getEquipment(EquipmentSlot.Offhand);
  if (kiri?.typeId === "minecraft:fishing_rod") return kiri;
  return undefined;
}

/** Pemain pemilik kail: pemain terdekat yang memegang pancingan. */
export function pemilikKail(dimensi, lokasi) {
  return pemainTerdekat(dimensi, lokasi, 48, (p) => kailDiTangan(p) !== undefined);
}

// --- Item kail (bentuk untuk upgrade) -------------------------------------
/** Klik kanan item rakit:kail_tN -> jadi kail aktif. */
export function aktifkanKail(player, tier) {
  const c = inventori(player);
  if (!c) return;
  c.setItem(player.selectedSlotIndex, buatKail(tier));
  statMaks(player, "tierMax", tier);
  suara(player.dimension, "random.orb", player.location);
  pesanBar(player, `${TIER[tier].warna}Kail ${TIER[tier].nama} aktif! §7Klik kanan lagi untuk memancing.`);
}

/** Saat membuka meja kerajinan, kail aktif diubah jadi item agar bisa di-upgrade. */
function ubahKailJadiItem(player) {
  const c = inventori(player);
  if (!c) return;
  let jumlah = 0;
  for (let i = 0; i < c.size; i++) {
    const tier = tierKail(c.getItem(i));
    if (tier === 0) continue;
    c.setItem(i, new ItemStack(`rakit:kail_t${tier}`, 1));
    jumlah++;
  }
  if (jumlah > 0) {
    player.sendMessage(
      "§e[Rakitin] §7Kail diubah menjadi item agar bisa di-upgrade. " +
        "§fKlik kanan item kail§7 untuk memakainya lagi."
    );
  }
}

// --- Deteksi hasil pancingan ----------------------------------------------
// Kail (fishing hook) dicatat tiap tick. Item yang muncul tepat di posisi kail
// lalu kailnya hilang = hasil tarikan pancingan.
const kailTerlihat = new Map();
const DIMENSI_MANCING = ["overworld", "the_end"];

function catatKail() {
  const t = system.currentTick;
  for (const id of DIMENSI_MANCING) {
    const dim = world.getDimension(id);
    for (const e of dim.getEntities({ type: "minecraft:fishing_hook" })) {
      const lama = kailTerlihat.get(e.id);
      kailTerlihat.set(e.id, { loc: e.location, dim: dim.id, tick: t, dipakai: lama?.dipakai ?? false });
    }
  }
  for (const [id, d] of kailTerlihat) {
    if (t - d.tick > 60) kailTerlihat.delete(id);
  }
}

function itemMuncul(entity) {
  let loc;
  try {
    loc = entity.location;
  } catch {
    return;
  }
  const t = system.currentTick;
  const dimId = entity.dimension.id;
  for (const [id, d] of kailTerlihat) {
    if (d.dipakai || d.dim !== dimId || t - d.tick > 3) continue;
    if (jarak(d.loc, loc) > 2.5) continue;
    d.dipakai = true;
    // Pastikan kail benar-benar ditarik (hilang), bukan sekadar item jatuh di dekat kail.
    system.runTimeout(() => periksaTangkapan(id, d, entity), 2);
    return;
  }
}

function periksaTangkapan(idKail, data, itemVanilla) {
  if (world.getEntity(idKail)) {
    data.dipakai = false;
    return;
  }
  if (!itemVanilla.isValid) return;
  const dim = world.getDimension(data.dim);
  const pemain = pemilikKail(dim, data.loc);
  if (!pemain) return;
  const tier = Math.max(1, tierKail(kailDiTangan(pemain)));
  itemVanilla.remove();

  berikanTangkapan(pemain, tier);
  if (peluang(PELUANG_GANDA[tier])) {
    system.runTimeout(() => {
      if (!pemain.isValid) return;
      pesanBar(pemain, "§a§lTANGKAPAN GANDA!");
      berikanTangkapan(pemain, tier);
    }, 15);
  }
}

function berikanTangkapan(pemain, tier) {
  const hasil = gulirTangkapan(tier);
  const stack = new ItemStack(hasil.id, 1);
  stack.amount = Math.min(hasil.jumlah, stack.maxAmount);
  beriItem(pemain, stack);
  tambahStat(pemain, "tangkapan");

  const info = INFO_KATEGORI[hasil.kategori];
  const bintang = { langka: "★ ", harta: "★★ ", portal: "✦ " }[hasil.kategori] ?? "";
  pesanBar(pemain, {
    rawtext: [
      { text: `${info.warna}${bintang}${info.nama}: §f` },
      { translate: stack.localizationKey },
      { text: ` §7x${stack.amount}` },
    ],
  });

  if (hasil.kategori === "langka") {
    suara(pemain.dimension, "random.orb", pemain.location, 1, 1.4);
  } else if (hasil.kategori === "harta" || hasil.kategori === "portal") {
    suara(pemain.dimension, "random.levelup", pemain.location);
    world.sendMessage({
      rawtext: [
        { text: `${info.warna}[${info.nama}] §f${pemain.name} §7memancing ` },
        { translate: stack.localizationKey },
        { text: "§7!" },
      ],
    });
  }
}

export function mulaiKail() {
  system.runInterval(catatKail, 1);

  world.afterEvents.entitySpawn.subscribe(({ entity, cause }) => {
    if (cause !== EntityInitializationCause.Spawned) return;
    if (entity.typeId !== "minecraft:item") return;
    itemMuncul(entity);
  });

  world.beforeEvents.playerInteractWithBlock.subscribe((e) => {
    if (!e.isFirstEvent || e.block.typeId !== "minecraft:crafting_table") return;
    const player = e.player;
    system.run(() => ubahKailJadiItem(player));
  });
}

