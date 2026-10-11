// Pengaturan per pemain (disimpan di dynamic property pemain) + form UI,
// dan komponen item `td:obor` (klik kanan obor).
import { EquipmentSlot, system, world } from "@minecraft/server";
import { FormCancelationReason, ModalFormData } from "@minecraft/server-ui";
import { ID_OBOR, KUNCI_ATUR, ORE, RADIUS_MAKS, RADIUS_MIN } from "./config.js";
import { bacaJSON, pesanBar, perlengkapan, suaraPemain, tulisJSON } from "./util.js";

/**
 * @typedef {{ outline: boolean, hud: boolean, cahaya: boolean, batasRadius: number, ore: Record<string, boolean> }} Atur
 */

/** @returns {Atur} */
function aturAwal() {
  /** @type {Record<string, boolean>} */
  const ore = {};
  for (const o of ORE) ore[o.kunci] = true;
  return { outline: true, hud: true, cahaya: true, batasRadius: RADIUS_MAKS, ore };
}

/**
 * Lengkapi & bersihkan data tersimpan (bisa rusak/berasal dari versi lama).
 * @param {any} data
 * @returns {Atur}
 */
function rapikan(data) {
  const a = aturAwal();
  if (!data || typeof data !== "object") return a;
  if (typeof data.outline === "boolean") a.outline = data.outline;
  if (typeof data.hud === "boolean") a.hud = data.hud;
  if (typeof data.cahaya === "boolean") a.cahaya = data.cahaya;
  if (typeof data.batasRadius === "number" && Number.isFinite(data.batasRadius)) {
    a.batasRadius = Math.min(RADIUS_MAKS, Math.max(RADIUS_MIN, Math.round(data.batasRadius)));
  }
  if (data.ore && typeof data.ore === "object") {
    for (const o of ORE) {
      if (typeof data.ore[o.kunci] === "boolean") a.ore[o.kunci] = data.ore[o.kunci];
    }
  }
  return a;
}

// Cache supaya JSON tidak di-parse tiap 10 tick: idPemain -> { atur, tanda }
/** @type {Map<string, { atur: Atur, tanda: string }>} */
const cache = new Map();

/** @param {import("@minecraft/server").Player} player */
function muat(player) {
  let c = cache.get(player.id);
  if (!c) {
    const atur = rapikan(bacaJSON(player, KUNCI_ATUR, undefined));
    c = { atur, tanda: JSON.stringify(atur) };
    cache.set(player.id, c);
  }
  return c;
}

/**
 * Pengaturan pemain (jangan diubah langsung; pakai simpanAtur).
 * @param {import("@minecraft/server").Player} player
 * @returns {Atur}
 */
export function bacaAtur(player) {
  return muat(player).atur;
}

/**
 * Teks penanda pengaturan; berubah setiap kali pengaturan disimpan.
 * @param {import("@minecraft/server").Player} player
 */
export function tandaAtur(player) {
  return muat(player).tanda;
}

/**
 * @param {import("@minecraft/server").Player} player
 * @param {Atur} atur
 */
export function simpanAtur(player, atur) {
  const a = rapikan(atur);
  tulisJSON(player, KUNCI_ATUR, a);
  cache.set(player.id, { atur: a, tanda: JSON.stringify(a) });
}

/**
 * Daftar id blok ore yang diaktifkan pemain (untuk filter getBlocks).
 * @param {Atur} atur
 * @returns {string[]}
 */
export function idBlokAktif(atur) {
  const hasil = [];
  for (const o of ORE) {
    if (atur.ore[o.kunci]) hasil.push(...o.blok);
  }
  return hasil;
}

// --- Form ------------------------------------------------------------------
/**
 * Tampilkan form; ulangi jika pemain sedang sibuk (mis. chat/inventori masih terbuka).
 * @param {import("@minecraft/server").Player} player
 * @param {ModalFormData} form
 */
async function tampilkan(player, form) {
  for (let i = 0; i < 3; i++) {
    if (!player.isValid) return undefined;
    const r = await form.show(player);
    if (r.cancelationReason !== FormCancelationReason.UserBusy) return r;
    await new Promise((selesai) => system.runTimeout(() => selesai(undefined), 10));
  }
  return undefined;
}

// Pemain yang sedang membuka form (supaya form tidak terbuka dua kali).
/** @type {Set<string>} */
const formTerbuka = new Set();

/** @param {import("@minecraft/server").Player} player */
export async function bukaPengaturan(player) {
  if (formTerbuka.has(player.id)) return;
  formTerbuka.add(player.id);
  try {
    await isiPengaturan(player);
  } finally {
    formTerbuka.delete(player.id);
  }
}

/** @param {import("@minecraft/server").Player} player */
async function isiPengaturan(player) {
  const a = bacaAtur(player);
  const form = new ModalFormData()
    .title("Pengaturan Obor Detektor")
    .toggle("Outline warna di ore", { defaultValue: a.outline })
    .toggle("HUD radar (actionbar)", { defaultValue: a.hud })
    .toggle("Cahaya obor", { defaultValue: a.cahaya })
    .slider("Batas radius (blok)", RADIUS_MIN, RADIUS_MAKS, {
      defaultValue: a.batasRadius,
      valueStep: 1,
      tooltip: "Radius sebenarnya = yang lebih kecil antara batas ini dan radius beliungmu.",
    });
  for (const o of ORE) {
    form.toggle(`${o.kode}■ §r${o.nama}`, { defaultValue: a.ore[o.kunci] });
  }
  form.submitButton("Simpan");

  let r;
  try {
    r = await tampilkan(player, form);
  } catch {
    return;
  }
  if (!r || r.canceled || !r.formValues || !player.isValid) return;
  const v = r.formValues;

  /** @type {Atur} */
  const baru = {
    outline: v[0] === true,
    hud: v[1] === true,
    cahaya: v[2] === true,
    batasRadius: typeof v[3] === "number" ? v[3] : a.batasRadius,
    ore: {},
  };
  ORE.forEach((o, i) => {
    const nilai = v[4 + i];
    baru.ore[o.kunci] = typeof nilai === "boolean" ? nilai : a.ore[o.kunci];
  });
  // Tanda pengaturan berubah -> deteksi.js otomatis memindai ulang.
  simpanAtur(player, baru);
  pesanBar(player, "§aPengaturan Obor Detektor disimpan.");
  suaraPemain(player, "random.click", 1.2, 0.6);
}

// --- Komponen item ---------------------------------------------------------
/**
 * Pindahkan obor dari tangan kanan ke tangan kiri (tukar dengan isi tangan kiri).
 * @param {import("@minecraft/server").Player} player
 */
function pasangDiKiri(player) {
  const eq = perlengkapan(player);
  if (!eq) return;
  const kanan = eq.getEquipment(EquipmentSlot.Mainhand);
  if (kanan?.typeId !== ID_OBOR) return;
  const kiri = eq.getEquipment(EquipmentSlot.Offhand);
  if (kiri?.typeId === ID_OBOR) {
    pesanBar(player, "§eObor Detektor sudah ada di tangan kiri.");
    return;
  }
  if (!eq.setEquipment(EquipmentSlot.Offhand, kanan)) {
    pesanBar(player, "§cObor tidak bisa dipasang di tangan kiri.");
    return;
  }
  eq.setEquipment(EquipmentSlot.Mainhand, kiri);
  suaraPemain(player, "armor.equip_generic");
  pesanBar(player, "§aObor dipasang di tangan kiri. Pegang beliung untuk mendeteksi ore.");
}

// Tick pemakaian terakhir per pemain (klik kanan yang ditahan tidak diproses berulang).
/** @type {Map<string, number>} */
const pakaiTerakhir = new Map();

/** @type {import("@minecraft/server").ItemCustomComponent} */
const komponenObor = {
  onUse(e) {
    const player = e.source;
    const t = pakaiTerakhir.get(player.id);
    if (t !== undefined && system.currentTick - t < 5) return;
    pakaiTerakhir.set(player.id, system.currentTick);
    const jongkok = player.isSneaking;
    // Ditunda 1 tick supaya aman mengubah perlengkapan / membuka form.
    system.run(() => {
      if (!player.isValid) return;
      if (jongkok) bukaPengaturan(player);
      else pasangDiKiri(player);
    });
  },
};

/**
 * Didaftarkan saat startup (lihat main.js).
 * @param {import("@minecraft/server").ItemComponentRegistry} itemReg
 */
export function daftarKomponen(itemReg) {
  itemReg.registerCustomComponent("td:obor", komponenObor);
}

/** Bersihkan cache saat pemain keluar. */
export function mulaiPengaturan() {
  world.afterEvents.playerLeave.subscribe(({ playerId }) => {
    cache.delete(playerId);
    pakaiTerakhir.delete(playerId);
    formTerbuka.delete(playerId);
  });
}
