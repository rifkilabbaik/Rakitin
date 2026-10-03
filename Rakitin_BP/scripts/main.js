// Rakitin - addon bertahan hidup di lautan dengan rakit.
// Titik masuk script: mendaftarkan komponen custom lalu menyalakan semua sistem.
import { system, world } from "@minecraft/server";
import { mulaiAwal } from "./awal.js";
import { daftarKomponen } from "./blok.js";
import { mulaiCuaca } from "./cuaca.js";
import { mulaiHaus } from "./haus.js";
import { mulaiHiu } from "./hiu.js";
import { mulaiKail } from "./kail.js";
import { mulaiLayar } from "./layar.js";
import { mulaiPortal } from "./portal.js";
import { mulaiPuing } from "./puing.js";
import { mulaiPulau } from "./pulau.js";
import { mulaiStatistik, tambahStat } from "./statistik.js";

system.beforeEvents.startup.subscribe((e) => {
  daftarKomponen(e.blockComponentRegistry, e.itemComponentRegistry);
});

world.afterEvents.worldLoad.subscribe(() => {
  mulaiCuaca();
  mulaiHaus();
  mulaiStatistik();
  mulaiKail();
  mulaiAwal();
  mulaiPuing();
  mulaiHiu();
  mulaiLayar();
  mulaiPulau();
  mulaiPortal();

  world.afterEvents.playerPlaceBlock.subscribe(({ player, block }) => {
    if (block.typeId === "rakit:fondasi_rakit" || block.typeId === "rakit:fondasi_kuat") {
      tambahStat(player, "fondasi");
    }
  });
});
