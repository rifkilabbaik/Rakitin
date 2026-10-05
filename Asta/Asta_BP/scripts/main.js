// Asta (Black Clover) - titik masuk script.
import { system, world } from "@minecraft/server";
import { pasifArmor } from "./armor.js";
import { komponenPedang, mulaiPedang, pasifPedang } from "./pedang.js";

system.beforeEvents.startup.subscribe((e) => {
  e.itemComponentRegistry.registerCustomComponent("asta:pedang", komponenPedang);
});

world.afterEvents.worldLoad.subscribe(() => {
  mulaiPedang();
  system.runInterval(() => {
    for (const p of world.getAllPlayers()) {
      try {
        pasifPedang(p);
        pasifArmor(p);
      } catch {
        // pemain sedang berpindah dimensi / keluar
      }
    }
  }, 10);
});
