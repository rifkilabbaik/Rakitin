// Torch Detektor X-Ray (pack opsional, butuh eksperimen "Beta APIs").
// Pack ini TIDAK memindai blok sendiri. Ia hanya menerima daftar ore dari pack inti
// lewat scriptevent "td:ore", lalu menggambar kotak wireframe berwarna (DebugBox) yang
// terlihat menembus dinding, khusus untuk pemain pemegang Obor Detektor (visibleTo).
// Heartbeat "td:xray_hidup" memberi tahu pack inti bahwa pack ini aktif, sehingga pack
// inti berhenti menggambar outline partikel dan mulai mengirim data ore ke sini.
import { system, world } from "@minecraft/server";
import { DebugBox, debugDrawer } from "@minecraft/debug-utilities";

/** @typedef {import("@minecraft/server").Player} Player */
/** @typedef {import("@minecraft/server").Dimension} Dimension */
/** @typedef {import("@minecraft/server").RGBA} RGBA */

const ID_ORE = "td:ore";
const ID_HIDUP = "td:xray_hidup";
const JEDA_HIDUP = 40; // tick antar heartbeat
const JEDA_BERSIH = 20; // tick antar pemeriksaan kotak yatim

// Umur kotak (detik). Diperbarui setiap pesan masuk; pack inti mengirim minimal tiap
// 40 tick (2 detik), jadi kotak hanya hilang sendiri bila pack inti berhenti mengirim.
const UMUR_KOTAK = 3;
const UMUR_KOTAK_TICK = UMUR_KOTAK * 20;
const UMUR_KOTAK_MS = UMUR_KOTAK * 1000;
// Bila jeda antar pesan mendekati umur kotak, anggap kotak lama sudah dihapus mesin
// lalu buat ulang semuanya (jaga-jaga kalau timeLeft yang diperbarui tidak sempat terkirim).
const BATAS_SEGAR_TICK = UMUR_KOTAK_TICK - 5;
const BATAS_SEGAR_MS = UMUR_KOTAK_MS - 250;

const MAKS_ORE = 64;
const BATAS_KOORDINAT = 30000000;

// Ukuran kotak: bound 1x1x1 dikali scale = 1,02 blok, sedikit lebih besar dari blok
// supaya garis tidak berkedip bertumpuk dengan permukaan blok.
const UKURAN = { x: 1, y: 1, z: 1 };
const SKALA = 1.02;
// Menurut d.ts @minecraft/debug-utilities: "For most shapes the location is the centre
// of the shape". Jika di game kotak tampak bergeser setengah blok, ubah ke false
// (lokasi dianggap sudut minimum kotak).
const LOKASI_DI_PUSAT = true;

const WARNA_CADANGAN = "FFFFFF";

/**
 * @typedef {{ box: DebugBox, warna: string }} Kotak
 * @typedef {{ player: Player, dimensi: string, kotak: Map<string, Kotak>, tick: number, ms: number }} DataPemain
 */

/** Kotak aktif per pemain (kunci: id pemain). @type {Map<string, DataPemain>} */
const dataPemain = new Map();
/** Warna terakhir per indeks ore, dari kolom "w" pesan sebelumnya. @type {Map<number, string>} */
const warnaIndeks = new Map();
/** Cache hasil ubah hex -> RGBA. @type {Map<string, RGBA>} */
const cacheRGBA = new Map();

/** "RRGGBB" (boleh diawali #) -> hex huruf besar, atau undefined jika tidak sah. */
function rapikanHex(nilai) {
  if (typeof nilai !== "string") return undefined;
  const h = nilai.startsWith("#") ? nilai.slice(1) : nilai;
  return /^[0-9a-fA-F]{6}$/.test(h) ? h.toUpperCase() : undefined;
}

/** @returns {RGBA} warna 0..1 untuk DebugShape.color */
function rgba(hex) {
  let w = cacheRGBA.get(hex);
  if (!w) {
    const n = parseInt(hex, 16);
    w = { red: ((n >> 16) & 255) / 255, green: ((n >> 8) & 255) / 255, blue: (n & 255) / 255, alpha: 1 };
    cacheRGBA.set(hex, w);
  }
  return w;
}

function lokasiKotak(x, y, z) {
  if (LOKASI_DI_PUSAT) return { x: x + 0.5, y: y + 0.5, z: z + 0.5 };
  const geser = 0.5 - SKALA / 2;
  return { x: x + geser, y: y + geser, z: z + geser };
}

/** @returns {Player | undefined} */
function cariPemain(id) {
  for (const p of world.getAllPlayers()) {
    if (p.id === id) return p;
  }
  return undefined;
}

/** @param {Kotak} k */
function hapusKotak(k) {
  try {
    k.box.remove();
  } catch {
    // kotak sudah tidak ada (kedaluwarsa / dunia ditutup)
  }
}

/** Hapus semua kotak milik satu pemain. */
function hapusSemua(idPemain) {
  const data = dataPemain.get(idPemain);
  if (!data) return;
  for (const k of data.kotak.values()) hapusKotak(k);
  dataPemain.delete(idPemain);
}

/**
 * @param {Player} player
 * @param {Dimension} dimensi
 * @returns {DebugBox | undefined}
 */
function buatKotak(player, dimensi, x, y, z, hex) {
  try {
    const box = new DebugBox(lokasiKotak(x, y, z));
    box.bound = UKURAN;
    box.scale = SKALA;
    box.color = rgba(hex);
    // visibleTo WAJIB diisi sebelum addShape: daftar kosong = terlihat semua pemain.
    box.visibleTo = [player];
    box.timeLeft = UMUR_KOTAK;
    debugDrawer.addShape(box, dimensi);
    return box;
  } catch {
    return undefined;
  }
}

/**
 * Ambil daftar ore yang sah dari pesan.
 * @returns {Map<string, { x: number, y: number, z: number, warna: string }>}
 */
function bacaDaftarOre(data) {
  const palet = data.w && typeof data.w === "object" ? data.w : {};
  for (const kunci of Object.keys(palet)) {
    const idx = Number(kunci);
    const hex = rapikanHex(palet[kunci]);
    if (Number.isInteger(idx) && idx >= 0 && idx < 256 && hex) warnaIndeks.set(idx, hex);
  }

  /** @type {Map<string, { x: number, y: number, z: number, warna: string }>} */
  const hasil = new Map();
  for (const o of data.o) {
    if (hasil.size >= MAKS_ORE) break;
    if (!Array.isArray(o) || o.length < 4) continue;
    const [x, y, z, idx] = o;
    if (![x, y, z].every((v) => typeof v === "number" && Number.isFinite(v) && Math.abs(v) < BATAS_KOORDINAT)) continue;
    const bx = Math.floor(x);
    const by = Math.floor(y);
    const bz = Math.floor(z);
    hasil.set(`${bx},${by},${bz}`, { x: bx, y: by, z: bz, warna: warnaIndeks.get(Number(idx)) ?? WARNA_CADANGAN });
  }
  return hasil;
}

/** Proses satu pesan "td:ore" dari pack inti. */
function terimaOre(pesan) {
  let data;
  try {
    data = JSON.parse(pesan);
  } catch {
    return; // JSON rusak: abaikan, kotak lama hilang sendiri lewat timeLeft
  }
  if (!data || typeof data !== "object" || typeof data.p !== "string") return;

  const idPemain = data.p;
  const player = cariPemain(idPemain);
  if (!player || !player.isValid) {
    hapusSemua(idPemain);
    return;
  }
  // Daftar kosong / tidak ada = detektor mati: hapus semua kotak pemain ini.
  if (!Array.isArray(data.o) || data.o.length === 0) {
    hapusSemua(idPemain);
    return;
  }
  const dimensi = player.dimension;
  // Pesan untuk dimensi lain berarti basi (pemain baru saja pindah dimensi).
  if (typeof data.d === "string" && data.d !== dimensi.id) {
    hapusSemua(idPemain);
    return;
  }

  const sekarangTick = system.currentTick;
  const sekarangMs = Date.now();
  let st = dataPemain.get(idPemain);
  if (
    st &&
    (st.dimensi !== dimensi.id ||
      !st.player.isValid ||
      sekarangTick - st.tick >= BATAS_SEGAR_TICK ||
      sekarangMs - st.ms >= BATAS_SEGAR_MS)
  ) {
    hapusSemua(idPemain);
    st = undefined;
  }
  if (!st) {
    st = { player, dimensi: dimensi.id, kotak: new Map(), tick: sekarangTick, ms: sekarangMs };
    dataPemain.set(idPemain, st);
  }
  st.tick = sekarangTick;
  st.ms = sekarangMs;

  const baru = bacaDaftarOre(data);

  // Buang kotak ore yang sudah tidak ada di daftar (dipecah / di luar radius).
  for (const [kunci, k] of st.kotak) {
    if (!baru.has(kunci)) {
      hapusKotak(k);
      st.kotak.delete(kunci);
    }
  }

  // Perpanjang umur kotak lama, tambah kotak baru.
  for (const [kunci, o] of baru) {
    const lama = st.kotak.get(kunci);
    if (lama) {
      try {
        lama.box.timeLeft = UMUR_KOTAK;
        if (lama.warna !== o.warna) {
          lama.box.color = rgba(o.warna);
          lama.warna = o.warna;
        }
        continue;
      } catch {
        hapusKotak(lama);
        st.kotak.delete(kunci);
      }
    }
    const box = buatKotak(player, dimensi, o.x, o.y, o.z, o.warna);
    if (box) st.kotak.set(kunci, { box, warna: o.warna });
  }

  if (st.kotak.size === 0) dataPemain.delete(idPemain);
}

/** Bersihkan kotak milik pemain yang keluar, pindah dimensi, atau tidak lagi dikirimi data. */
function bersihkan() {
  const sekarangTick = system.currentTick;
  for (const [idPemain, st] of dataPemain) {
    let buang = !st.player.isValid || sekarangTick - st.tick > UMUR_KOTAK_TICK;
    if (!buang) {
      try {
        buang = st.player.dimension.id !== st.dimensi;
      } catch {
        buang = true;
      }
    }
    if (buang) hapusSemua(idPemain);
  }
}

function kirimHidup() {
  try {
    system.sendScriptEvent(ID_HIDUP, "1");
  } catch {
    // dunia sedang ditutup
  }
}

world.afterEvents.worldLoad.subscribe(() => {
  system.afterEvents.scriptEventReceive.subscribe(
    (e) => {
      if (e.id !== ID_ORE) return;
      // Hanya terima dari script (system.sendScriptEvent), bukan /scriptevent oleh pemain/blok/NPC.
      if (e.sourceEntity || e.sourceBlock || e.initiator) return;
      terimaOre(e.message);
    },
    { namespaces: ["td"] }
  );

  world.afterEvents.playerLeave.subscribe(({ playerId }) => hapusSemua(playerId));
  world.afterEvents.playerDimensionChange.subscribe(({ player }) => hapusSemua(player.id));

  kirimHidup();
  system.runInterval(kirimHidup, JEDA_HIDUP);
  system.runInterval(bersihkan, JEDA_BERSIH);
});
