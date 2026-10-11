// Torch Detektor - Obor Detektor di tangan kiri + beliung di tangan kanan = deteksi ore di dekatmu.
// Titik masuk script: daftarkan komponen item saat startup, nyalakan semua sistem saat dunia dimuat.
import { system, world } from "@minecraft/server";
import { mulaiCahaya } from "./cahaya.js";
import { mulaiDeteksi } from "./deteksi.js";
import { mulaiGambar } from "./gambar.js";
import { daftarKomponen, mulaiPengaturan } from "./pengaturan.js";

system.beforeEvents.startup.subscribe((e) => {
  daftarKomponen(e.itemComponentRegistry);
});

world.afterEvents.worldLoad.subscribe(() => {
  mulaiPengaturan();
  mulaiGambar();
  mulaiDeteksi();
  mulaiCahaya();
});
