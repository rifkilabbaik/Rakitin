// Statistik pemain, pencapaian, dan Buku Catatan Rakit.
import { system, world } from "@minecraft/server";
import { ActionFormData, FormCancelationReason } from "@minecraft/server-ui";
import { ambilHaus } from "./haus.js";
import { bacaJSON, beriItemId, pesanSemua, suara, tulisJSON } from "./util.js";

const KUNCI = "rakit:stat";

const STAT_AWAL = {
  tangkapan: 0,
  puing: 0,
  hiu: 0,
  fondasi: 0,
  pulau: 0,
  tierMax: 1,
  hari: 0,
  naga: 0,
  mulaiWaktu: -1,
  pulauDikunjungi: [],
  capaian: [],
};

export function bacaStat(player) {
  return Object.assign(JSON.parse(JSON.stringify(STAT_AWAL)), bacaJSON(player, KUNCI, {}));
}

function simpanStat(player, s) {
  tulisJSON(player, KUNCI, s);
}

export function tambahStat(player, kunci, n = 1) {
  const s = bacaStat(player);
  s[kunci] = (s[kunci] ?? 0) + n;
  simpanStat(player, s);
  cekPencapaian(player, s);
}

export function statMaks(player, kunci, nilai) {
  const s = bacaStat(player);
  if ((s[kunci] ?? 0) >= nilai) return;
  s[kunci] = nilai;
  simpanStat(player, s);
  cekPencapaian(player, s);
}

/** Tandai pulau sudah dikunjungi. Mengembalikan true jika baru pertama kali. */
export function kunjungiPulau(player, idPulau) {
  const s = bacaStat(player);
  if (s.pulauDikunjungi.includes(idPulau)) return false;
  s.pulauDikunjungi.push(idPulau);
  s.pulau += 1;
  simpanStat(player, s);
  cekPencapaian(player, s);
  return true;
}

export function aturMulai(player) {
  const s = bacaStat(player);
  if (s.mulaiWaktu < 0) {
    s.mulaiWaktu = world.getAbsoluteTime();
    simpanStat(player, s);
  }
}

// --- Pencapaian ------------------------------------------------------------
export const PENCAPAIAN = [
  { id: "tangkap10", judul: "Pemancing Pemula", desk: "Dapatkan 10 hasil pancingan", syarat: (s) => s.tangkapan >= 10, hadiah: [["rakit:plastik", 4]] },
  { id: "tangkap100", judul: "Pemancing Handal", desk: "Dapatkan 100 hasil pancingan", syarat: (s) => s.tangkapan >= 100, hadiah: [["rakit:air_bersih", 3]] },
  { id: "tangkap500", judul: "Raja Pancing", desk: "Dapatkan 500 hasil pancingan", syarat: (s) => s.tangkapan >= 500, hadiah: [["minecraft:diamond", 3]] },
  { id: "puing25", judul: "Pemulung Laut", desk: "Ambil 25 puing hanyut", syarat: (s) => s.puing >= 25, hadiah: [["rakit:besi_tua", 2]] },
  { id: "puing100", judul: "Kolektor Samudra", desk: "Ambil 100 puing hanyut", syarat: (s) => s.puing >= 100, hadiah: [["rakit:besi_tua", 5]] },
  { id: "hiu1", judul: "Pemburu Hiu", desk: "Kalahkan 1 hiu", syarat: (s) => s.hiu >= 1, hadiah: [["minecraft:golden_carrot", 2]] },
  { id: "hiu10", judul: "Teror Lautan", desk: "Kalahkan 10 hiu", syarat: (s) => s.hiu >= 10, hadiah: [["minecraft:diamond", 1]] },
  { id: "fondasi50", judul: "Arsitek Rakit", desk: "Pasang 50 fondasi rakit", syarat: (s) => s.fondasi >= 50, hadiah: [["rakit:fondasi_kuat", 8]] },
  { id: "pulau1", judul: "Penjelajah Pulau", desk: "Kunjungi sebuah pulau", syarat: (s) => s.pulau >= 1, hadiah: [["minecraft:oak_sapling", 2]] },
  { id: "tier3", judul: "Kail Emas", desk: "Punya kail Tier 3", syarat: (s) => s.tierMax >= 3, hadiah: [] },
  { id: "tier5", judul: "Kail Pamungkas", desk: "Punya kail Tier 5", syarat: (s) => s.tierMax >= 5, hadiah: [["minecraft:experience_bottle", 8]] },
  { id: "hari7", judul: "Seminggu di Laut", desk: "Bertahan 7 hari", syarat: (s) => s.hari >= 7, hadiah: [["minecraft:golden_apple", 1]] },
  { id: "naga", judul: "Penakluk Naga", desk: "Kalahkan Naga Ender", syarat: (s) => s.naga >= 1, hadiah: [] },
];

function cekPencapaian(player, s) {
  let berubah = false;
  for (const c of PENCAPAIAN) {
    if (s.capaian.includes(c.id) || !c.syarat(s)) continue;
    s.capaian.push(c.id);
    berubah = true;
    for (const [id, n] of c.hadiah) beriItemId(player, String(id), Number(n));
    pesanSemua(`§e[Pencapaian] §f${player.name}§e meraih §6${c.judul}§e!`);
    player.onScreenDisplay.setTitle("§6Pencapaian!", {
      subtitle: `§e${c.judul}`,
      fadeInDuration: 5,
      stayDuration: 50,
      fadeOutDuration: 15,
    });
    suara(player.dimension, "random.levelup", player.location);
  }
  if (berubah) simpanStat(player, s);
}

/** Hitung hari bertahan tiap menit. */
export function mulaiStatistik() {
  system.runInterval(() => {
    const sekarang = world.getAbsoluteTime();
    for (const p of world.getAllPlayers()) {
      const s = bacaStat(p);
      if (s.mulaiWaktu < 0) continue;
      const hari = Math.floor((sekarang - s.mulaiWaktu) / 24000);
      if (hari > s.hari) {
        s.hari = hari;
        simpanStat(p, s);
        p.onScreenDisplay.setTitle(`§bHari ke-${hari + 1}`, {
          subtitle: "§7di tengah lautan",
          fadeInDuration: 10,
          stayDuration: 40,
          fadeOutDuration: 20,
        });
        cekPencapaian(p, s);
      }
    }
  }, 1200);
}

// --- Buku Catatan ----------------------------------------------------------
const PANDUAN = [
  [
    "Bertahan Hidup",
    "§bHaus§r turun pelan-pelan, lebih cepat saat berlari atau berenang. " +
      "Minum §fBotol Air Bersih§r (+8). §fBotol Air Laut§r hanya +3 dan membuat mual.\n\n" +
      "Isi §fBotol Kosong§r dengan klik kanan ke air laut. Ubah air laut jadi air bersih dengan " +
      "§fPenyaring Air§r, merebusnya di Tungku/Api Unggun, atau tampung hujan dengan §fPenampung Air Hujan§r.",
  ],
  [
    "Memancing",
    "Kail punya 5 tier. Semakin tinggi tier, semakin sedikit sampah dan semakin besar peluang " +
      "barang langka, harta, dan tangkapan ganda.\n\n" +
      "Upgrade di §fMeja Kerajinan§r: saat membuka meja, kailmu otomatis berubah jadi item. " +
      "Setelah selesai, §eklik kanan item kail§r untuk mengaktifkannya lagi.\n\n" +
      "Kail Tier 5 bisa memancing §5Pecahan Portal§r.",
  ],
  [
    "Puing & Hiu",
    "Puing (papan, plastik, daun, barel) hanyut terbawa arus. Ambil dengan mendekatinya, memukulnya, " +
      "atau melempar kail ke arahnya.\n\n" +
      "§cHiu§r menyerang pemain di air dan kadang menggigit §fFondasi Rakit§r. " +
      "Pukul hiu supaya kabur, pakai §fTombak§r, atau pasang §fFondasi Diperkuat§r yang tidak bisa digigit.",
  ],
  [
    "Berlayar & Pulau",
    "Pasang §fLayar§r dan §fKemudi§r di atas rakit. Klik kanan kemudi untuk berlayar ke arah pandanganmu; " +
      "klik lagi untuk berhenti. Makin banyak layar (maks 3), makin cepat.\n\n" +
      "Saat menjelajah, kadang muncul §apulau kecil§r berisi pohon dan peti harta.",
  ],
  [
    "Mengalahkan Naga",
    "Kumpulkan 8 §5Pecahan Portal§r dari Kail Tier 5 (atau peti pulau) dan 1 §fMata Ender§r, lalu buat " +
      "§5Inti Portal End§r. Klik kanan di atas rakit untuk membangun portal yang langsung aktif.\n\n" +
      "Siapkan senjata, baju besi, makanan, dan blok sebelum masuk. Kalahkan §dNaga Ender§r untuk menang!",
  ],
];

function batangHaus(h) {
  const n = Math.round(h / 2);
  return `§b${"■".repeat(n)}§8${"■".repeat(10 - n)}`;
}

async function tampilkan(player, form) {
  for (let i = 0; i < 3; i++) {
    const r = await form.show(player);
    if (r.cancelationReason !== FormCancelationReason.UserBusy) return r;
    await new Promise((selesai) => system.runTimeout(() => selesai(undefined), 10));
  }
  return undefined;
}

export async function bukaBuku(player) {
  const s = bacaStat(player);
  const haus = ambilHaus(player);
  const isi =
    `§lStatistik ${player.name}§r\n\n` +
    `§bHaus: ${batangHaus(haus)} §f${Math.ceil(haus)}/20\n` +
    `§fHari bertahan: §e${s.hari + 1}\n` +
    `§fHasil pancingan: §e${s.tangkapan}\n` +
    `§fPuing diambil: §e${s.puing}\n` +
    `§fHiu dikalahkan: §e${s.hiu}\n` +
    `§fFondasi dipasang: §e${s.fondasi}\n` +
    `§fPulau dikunjungi: §e${s.pulau}\n` +
    `§fTier kail tertinggi: §e${s.tierMax}\n` +
    `§fPencapaian: §e${s.capaian.length}/${PENCAPAIAN.length}`;

  const form = new ActionFormData()
    .title("Buku Catatan Rakit")
    .body(isi)
    .button("Pencapaian")
    .button("Panduan")
    .button("Tutup");
  const r = await tampilkan(player, form);
  if (!r || r.canceled) return;
  if (r.selection === 0) await bukaPencapaian(player);
  else if (r.selection === 1) await bukaPanduan(player);
}

async function bukaPencapaian(player) {
  const s = bacaStat(player);
  const baris = PENCAPAIAN.map((c) =>
    s.capaian.includes(c.id) ? `§a[Selesai] ${c.judul}§7 - ${c.desk}` : `§8[Belum] ${c.judul}§7 - ${c.desk}`
  );
  const form = new ActionFormData().title("Pencapaian").body(baris.join("\n")).button("Kembali");
  const r = await tampilkan(player, form);
  if (r && !r.canceled) await bukaBuku(player);
}

async function bukaPanduan(player) {
  const form = new ActionFormData().title("Panduan Rakitin").body("Pilih topik:");
  for (const [judul] of PANDUAN) form.button(judul);
  form.button("Kembali");
  const r = await tampilkan(player, form);
  if (!r || r.canceled || r.selection === undefined) return;
  if (r.selection >= PANDUAN.length) {
    await bukaBuku(player);
    return;
  }
  const [judul, teks] = PANDUAN[r.selection];
  const halaman = new ActionFormData().title(judul).body(teks).button("Kembali");
  const r2 = await tampilkan(player, halaman);
  if (r2 && !r2.canceled) await bukaPanduan(player);
}
