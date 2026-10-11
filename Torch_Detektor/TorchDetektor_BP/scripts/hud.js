// HUD radar di actionbar: jenis ore terdekat + jarak + arah (berfungsi menembus dinding).
import { MAKS_HUD, ORE } from "./config.js";
import { barSedangDipakai } from "./util.js";

/** @typedef {import("./deteksi.js").Keadaan} Keadaan */
/** @typedef {import("./pengaturan.js").Atur} Atur */

// 8 arah relatif terhadap pandangan: depan, kanan-depan, kanan, ... (searah jarum jam)
const PANAH = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"];

/**
 * Panah arah dari pemain ke titik (dx, dz), relatif terhadap yaw pemain.
 * Yaw Bedrock: 0 = selatan (+Z), 90 = barat (-X), bertambah saat berbelok ke kanan.
 */
function panahArah(/** @type {number} */ yaw, /** @type {number} */ dx, /** @type {number} */ dz) {
  if (dx * dx + dz * dz < 0.5) return "";
  const arahTarget = (Math.atan2(-dx, dz) * 180) / Math.PI;
  const relatif = arahTarget - yaw;
  const idx = ((Math.round(relatif / 45) % 8) + 8) % 8;
  return PANAH[idx];
}

/**
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 */
export function teksHud(player, st) {
  const kepala = player.getHeadLocation();
  const yaw = player.getRotation().y;
  const awal = `§6Detektor §7r${st.radius}`;

  // Ore terdekat per jenis (jarak dihitung ulang dari posisi kepala sekarang).
  /** @type {({ j: number, dx: number, dy: number, dz: number } | undefined)[]} */
  const terdekat = new Array(ORE.length);
  for (const b of st.ore) {
    const dx = b.x + 0.5 - kepala.x;
    const dy = b.y + 0.5 - kepala.y;
    const dz = b.z + 0.5 - kepala.z;
    const j = Math.sqrt(dx * dx + dy * dy + dz * dz);
    const lama = terdekat[b.i];
    if (!lama || j < lama.j) terdekat[b.i] = { j, dx, dy, dz };
  }

  // Jenis yang tampil dipilih menurut urutan tabel ORE (prioritas), maks 3.
  const entri = [];
  for (let i = 0; i < ORE.length && entri.length < MAKS_HUD; i++) {
    const t = terdekat[i];
    if (!t) continue;
    const o = ORE[i];
    let arah = panahArah(yaw, t.dx, t.dz);
    if (t.dy >= 2) arah += "▲";
    else if (t.dy <= -2) arah += "▼";
    if (!arah) arah = "•";
    entri.push(`${o.kode}■ ${o.nama} ${Math.round(t.j)}m ${arah}`);
  }

  if (entri.length === 0) return `${awal} §8| tidak ada ore di dekatmu`;
  // +N = jumlah blok ore lain di sekitar selain yang tampil di atas.
  const lain = st.ore.length - entri.length;
  return `${awal} §f| ${entri.join(" ")}${lain > 0 ? ` §7+${lain}` : ""}`;
}

/**
 * Dipanggil tiap 10 tick selama detektor aktif.
 * @param {import("@minecraft/server").Player} player
 * @param {Keadaan} st
 * @param {Atur} atur
 */
export function perbaruiHud(player, st, atur) {
  if (!atur.hud || barSedangDipakai(player)) return;
  try {
    player.onScreenDisplay.setActionBar(teksHud(player, st));
  } catch {
    // pemain sudah keluar
  }
}
