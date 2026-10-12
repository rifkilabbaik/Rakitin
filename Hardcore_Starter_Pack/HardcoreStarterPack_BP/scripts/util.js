// Fungsi bantu umum.
import { EquipmentSlot, GameMode, ItemStack, system, world } from "@minecraft/server";

export function acak(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

export function jarak(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const dz = a.z - b.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

export function bacaJSON(sumber, kunci, bawaan) {
  try {
    const s = sumber.getDynamicProperty(kunci);
    return typeof s === "string" ? JSON.parse(s) : bawaan;
  } catch {
    return bawaan;
  }
}

export function tulisJSON(sumber, kunci, nilai) {
  sumber.setDynamicProperty(kunci, JSON.stringify(nilai));
}

/** getBlock yang tidak melempar error untuk chunk yang belum dimuat. */
export function blokAman(dimensi, lokasi) {
  try {
    return dimensi.getBlock(lokasi);
  } catch {
    return undefined;
  }
}

/** @param {import("@minecraft/server").Player} player */
export function perlengkapan(player) {
  return player.getComponent("minecraft:equippable");
}

/** @param {import("@minecraft/server").Player} player */
export function itemTangan(player, slot = EquipmentSlot.Mainhand) {
  return perlengkapan(player)?.getEquipment(slot);
}

export function modeKreatif(player) {
  const m = player.getGameMode();
  return m === GameMode.Creative || m === GameMode.Spectator;
}

export function suara(dimensi, id, lokasi, volume = 1, pitch = 1) {
  try {
    dimensi.playSound(id, lokasi, { volume, pitch });
  } catch {
    // suara tidak tersedia
  }
}

// --- HUD actionbar -----------------------------------------------------------
// Beberapa fitur memakai actionbar; pesan penting menahan HUD navigasi sebentar.
const pesanTerakhir = new Map();

/** @param {string | import("@minecraft/server").RawMessage} teks */
export function pesanBar(player, teks) {
  player.onScreenDisplay.setActionBar(teks);
  pesanTerakhir.set(player.id, system.currentTick);
}

export function barSibuk(player) {
  const t = pesanTerakhir.get(player.id);
  return t !== undefined && system.currentTick - t < 40;
}

// --- Navigasi ----------------------------------------------------------------
const PANAH = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"];

/** Panah arah sasaran relatif terhadap arah pandang pemain + tanda naik/turun. */
export function arahKe(player, sasaran) {
  const asal = player.getHeadLocation();
  const dx = sasaran.x - asal.x;
  const dz = sasaran.z - asal.z;
  const dy = sasaran.y - asal.y;
  // Yaw Bedrock: 0 = selatan (+Z), 90 = barat (-X).
  const yawSasaran = (Math.atan2(-dx, dz) * 180) / Math.PI;
  let beda = (yawSasaran - player.getRotation().y) % 360;
  if (beda < 0) beda += 360;
  const panah = Math.hypot(dx, dz) < 1.5 ? "" : PANAH[Math.round(beda / 45) % 8];
  const vertikal = dy >= 2 ? "▲" : dy <= -2 ? "▼" : "";
  return `${panah}${vertikal}` || "•";
}

/** Partikel penunjuk arah 1,5 blok di depan mata, hanya terlihat oleh pemain itu. */
export function partikelPenunjuk(player, sasaran, partikel) {
  const asal = player.getHeadLocation();
  const d = jarak(asal, sasaran);
  if (d < 2) return;
  const k = 1.5 / d;
  try {
    player.spawnParticle(partikel, {
      x: asal.x + (sasaran.x - asal.x) * k,
      y: asal.y - 0.3 + (sasaran.y - asal.y) * k,
      z: asal.z + (sasaran.z - asal.z) * k,
    });
  } catch {
    // partikel gagal: abaikan
  }
}

/** Gabungkan tumpukan item sejenis supaya entitas item yang dijatuhkan sedikit. */
export class Kumpulan {
  constructor() {
    /** @type {Map<string, number>} */
    this.jumlah = new Map();
    /** @type {ItemStack[]} */
    this.khusus = [];
  }

  /** @param {ItemStack} item */
  tambah(item) {
    if (item.maxAmount > 1 && !item.nameTag) {
      this.jumlah.set(item.typeId, (this.jumlah.get(item.typeId) ?? 0) + item.amount);
    } else {
      this.khusus.push(item);
    }
  }

  jatuhkan(dimensi, lokasi) {
    for (const [id, total] of this.jumlah) {
      let sisa = total;
      while (sisa > 0) {
        const stack = new ItemStack(id, 1);
        const n = Math.min(sisa, stack.maxAmount);
        stack.amount = n;
        dimensi.spawnItem(stack, lokasi);
        sisa -= n;
      }
    }
    for (const item of this.khusus) dimensi.spawnItem(item, lokasi);
  }
}

export function semuaPemain() {
  return world.getAllPlayers();
}
