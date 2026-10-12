// Pengaturan per pemain + menu /setting.
import { EnchantmentTypes, EquipmentSlot, system } from "@minecraft/server";
import { ActionFormData, FormCancelationReason, ModalFormData } from "@minecraft/server-ui";
import { ORE } from "./data.js";
import { STRUKTUR, hapusMemoriStruktur } from "./struktur.js";
import { bacaJSON, perlengkapan, pesanBar, suara, tulisJSON } from "./util.js";

const KUNCI = "hsp:atur";

const BAWAAN = {
  pohon: true,
  vein: true,
  lebur: true,
  panen: true,
  tambang3: true,
  batasVein: 64,
  batasPohon: 256,
  enchant: true,
  pilihanTambang: "fortune", // "fortune" | "silk_touch" | "tidak"
  enchantMati: [],
  detektor: true,
  radiusDetektor: 16,
  oreMati: [],
  kompas: true,
  radiusKompas: 3,
  strukturMati: [],
};

const cache = new Map();

/** Pengaturan pemain (selalu lengkap dengan nilai bawaan). */
export function atur(player) {
  let a = cache.get(player.id);
  if (!a) {
    a = { ...JSON.parse(JSON.stringify(BAWAAN)), ...bacaJSON(player, KUNCI, {}) };
    cache.set(player.id, a);
  }
  return a;
}

/** Nomor versi pengaturan; naik setiap kali disimpan (dipakai cache fitur lain). */
const versi = new Map();
export function versiAtur(player) {
  return versi.get(player.id) ?? 0;
}

function simpan(player, a) {
  cache.set(player.id, a);
  versi.set(player.id, versiAtur(player) + 1);
  tulisJSON(player, KUNCI, a);
}

export function lupakanPemain(id) {
  cache.delete(id);
  versi.delete(id);
}

// --- Offhand -------------------------------------------------------------------
/** Tukar isi tangan kanan dan tangan kiri. */
export function tukarTangan(player) {
  const eq = perlengkapan(player);
  if (!eq) return;
  const kanan = eq.getEquipment(EquipmentSlot.Mainhand);
  const kiri = eq.getEquipment(EquipmentSlot.Offhand);
  if (!kanan && !kiri) {
    pesanBar(player, "§7Kedua tangan kosong.");
    return;
  }
  let berhasil = true;
  try {
    eq.setEquipment(EquipmentSlot.Offhand, kanan);
  } catch {
    berhasil = false;
  }
  if (kanan && eq.getEquipment(EquipmentSlot.Offhand)?.typeId !== kanan.typeId) berhasil = false;
  // Tangan kiri vanilla menolak sebagian item: coba lewat perintah untuk item polos.
  if (!berhasil && kanan && !kanan.nameTag && !kanan.getComponent("minecraft:enchantable")?.getEnchantments().length) {
    try {
      player.runCommand(`replaceitem entity @s slot.weapon.offhand 0 ${kanan.typeId} ${kanan.amount}`);
      berhasil = eq.getEquipment(EquipmentSlot.Offhand)?.typeId === kanan.typeId;
    } catch {
      berhasil = false;
    }
  }
  if (!berhasil) {
    try {
      eq.setEquipment(EquipmentSlot.Offhand, kiri);
    } catch {
      // biarkan
    }
    pesanBar(player, "§cItem ini tidak bisa dipegang di tangan kiri. §7Pakai §fTorch Detector§7 / §fCompass Finder§7.");
    return;
  }
  eq.setEquipment(EquipmentSlot.Mainhand, kiri);
  suara(player.dimension, "armor.equip_generic", player.location);
}

// --- Form ------------------------------------------------------------------------
async function tampilkan(player, form) {
  // Saat dipanggil dari chat, layar chat masih terbuka: coba lagi sampai pemain siap.
  for (let i = 0; i < 40; i++) {
    const r = await form.show(player);
    if (r.cancelationReason !== FormCancelationReason.UserBusy) return r;
    await new Promise((selesai) => system.runTimeout(() => selesai(undefined), 10));
  }
  return undefined;
}

const nama = (id) => id.replace(/^minecraft:/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export function daftarEnchantPilihan() {
  return EnchantmentTypes.getAll()
    .map((t) => t.id.replace(/^minecraft:/, ""))
    .filter((id) => !["binding", "vanishing", "fortune", "silk_touch"].includes(id))
    .sort();
}

export async function bukaMenu(player) {
  const a = atur(player);
  const on = (v) => (v ? "§aON" : "§cOFF");
  const form = new ActionFormData()
    .title("Hardcore Starter Pack")
    .body("§7Fitur tambang & panen aktif saat §fjongkok§7.\nPilih menu pengaturan:")
    .button(`Tambang & Panen`)
    .button(`Hold to Enchant ${on(a.enchant)}`)
    .button(`Ore Detector ${on(a.detektor)}`)
    .button(`Compass Finder ${on(a.kompas)}`)
    .button("Tukar Tangan (Offhand)")
    .button("Tutup");
  const r = await tampilkan(player, form);
  if (!r || r.canceled) return;
  if (r.selection === 0) await menuTambang(player);
  else if (r.selection === 1) await menuEnchant(player);
  else if (r.selection === 2) await menuDetektor(player);
  else if (r.selection === 3) await menuKompas(player);
  else if (r.selection === 4) tukarTangan(player);
}

async function menuTambang(player) {
  const a = atur(player);
  const form = new ModalFormData()
    .title("Tambang & Panen")
    .toggle("Tree Capitator (kapak)", { defaultValue: a.pohon })
    .toggle("Vein Miner (beliung + ore)", { defaultValue: a.vein })
    .toggle("Auto Smelt (ore langsung matang)", { defaultValue: a.lebur })
    .toggle("Crop Capitator (cangkul)", { defaultValue: a.panen })
    .toggle("3x3x3 Mining (beliung/sekop/kapak)", { defaultValue: a.tambang3 })
    .slider("Batas blok Vein Miner", 16, 128, { defaultValue: a.batasVein, valueStep: 16 })
    .slider("Batas batang Tree Capitator", 64, 512, { defaultValue: a.batasPohon, valueStep: 64 });
  const r = await tampilkan(player, form);
  if (!r || r.canceled || !r.formValues) return;
  const v = r.formValues;
  simpan(player, {
    ...a,
    pohon: !!v[0], vein: !!v[1], lebur: !!v[2], panen: !!v[3], tambang3: !!v[4],
    batasVein: Number(v[5]), batasPohon: Number(v[6]),
  });
  pesanBar(player, "§aPengaturan tambang disimpan.");
  await bukaMenu(player);
}

async function menuEnchant(player) {
  const a = atur(player);
  const pilihan = ["fortune", "silk_touch", "tidak"];
  const enchant = daftarEnchantPilihan();
  const form = new ModalFormData()
    .title("Hold to Enchant")
    .toggle("Aktifkan Hold to Enchant", { defaultValue: a.enchant })
    .dropdown("Enchant alat tambang", ["Fortune", "Silk Touch", "Tanpa keduanya"], {
      defaultValueIndex: Math.max(0, pilihan.indexOf(a.pilihanTambang)),
    });
  for (const id of enchant) form.toggle(nama(id), { defaultValue: !a.enchantMati.includes(id) });
  const r = await tampilkan(player, form);
  if (!r || r.canceled || !r.formValues) return;
  const v = r.formValues;
  simpan(player, {
    ...a,
    enchant: !!v[0],
    pilihanTambang: pilihan[Number(v[1])] ?? "fortune",
    enchantMati: enchant.filter((_, i) => !v[i + 2]),
  });
  pesanBar(player, "§aPengaturan enchant disimpan.");
  await bukaMenu(player);
}

async function menuDetektor(player) {
  const a = atur(player);
  const form = new ModalFormData()
    .title("Ore Detector")
    .toggle("Aktifkan (obor di tangan kiri)", { defaultValue: a.detektor })
    .slider("Jarak deteksi (blok)", 8, 24, { defaultValue: a.radiusDetektor, valueStep: 2 });
  for (const o of ORE) form.toggle(`${o.warna}${o.nama}`, { defaultValue: !a.oreMati.includes(o.kunci) });
  const r = await tampilkan(player, form);
  if (!r || r.canceled || !r.formValues) return;
  const v = r.formValues;
  simpan(player, {
    ...a,
    detektor: !!v[0],
    radiusDetektor: Number(v[1]),
    oreMati: ORE.filter((_, i) => !v[i + 2]).map((o) => o.kunci),
  });
  pesanBar(player, "§aPengaturan detektor disimpan.");
  await bukaMenu(player);
}

async function menuKompas(player) {
  const a = atur(player);
  const form = new ModalFormData()
    .title("Compass Finder")
    .toggle("Aktifkan (kompas di tangan kiri)", { defaultValue: a.kompas })
    .slider("Jangkauan pindai (chunk)", 2, 6, { defaultValue: a.radiusKompas, valueStep: 1 })
    .toggle("§cHapus memori struktur yang sudah ditemukan", { defaultValue: false });
  for (const s of STRUKTUR) form.toggle(s.nama, { defaultValue: !a.strukturMati.includes(s.kunci) });
  const r = await tampilkan(player, form);
  if (!r || r.canceled || !r.formValues) return;
  const v = r.formValues;
  if (v[2]) hapusMemoriStruktur();
  simpan(player, {
    ...a,
    kompas: !!v[0],
    radiusKompas: Number(v[1]),
    strukturMati: STRUKTUR.filter((_, i) => !v[i + 3]).map((s) => s.kunci),
  });
  pesanBar(player, v[2] ? "§aPengaturan disimpan, memori struktur dihapus." : "§aPengaturan kompas disimpan.");
  await bukaMenu(player);
}
