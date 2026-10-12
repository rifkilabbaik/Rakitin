// Hardcore Starter Pack - titik masuk script.
import { CommandPermissionLevel, CustomCommandStatus, system, world } from "@minecraft/server";
import { mulaiDetektor } from "./detektor.js";
import { mulaiEnchant } from "./enchant.js";
import { mulaiKompas } from "./kompas.js";
import { bukaMenu, lupakanPemain, tukarTangan } from "./pengaturan.js";
import { mulaiTambang } from "./tambang.js";

/** Ambil pemain dari asal perintah, atau undefined jika bukan pemain. */
function pemainDari(asal) {
  const e = asal.sourceEntity ?? asal.initiator;
  return e?.typeId === "minecraft:player" ? world.getAllPlayers().find((p) => p.id === e.id) : undefined;
}

system.beforeEvents.startup.subscribe(({ customCommandRegistry, itemComponentRegistry }) => {
  // Torch Detector / Compass Finder: klik kanan di tangan kanan -> pindah ke tangan kiri.
  itemComponentRegistry.registerCustomComponent("hsp:pasang_offhand", {
    onUse: ({ source }) => system.run(() => tukarTangan(source)),
  });

  customCommandRegistry.registerCommand(
    {
      name: "hsp:setting",
      description: "Buka menu pengaturan Hardcore Starter Pack",
      permissionLevel: CommandPermissionLevel.Any,
      cheatsRequired: false,
    },
    (asal) => {
      const p = pemainDari(asal);
      if (!p) return { status: CustomCommandStatus.Failure, message: "Hanya bisa dipakai pemain." };
      system.run(() => bukaMenu(p));
      return { status: CustomCommandStatus.Success, message: "§7Tutup chat untuk membuka menu pengaturan." };
    }
  );
  customCommandRegistry.registerCommand(
    {
      name: "hsp:offhand",
      description: "Tukar item tangan kanan dengan tangan kiri",
      permissionLevel: CommandPermissionLevel.Any,
      cheatsRequired: false,
    },
    (asal) => {
      const p = pemainDari(asal);
      if (!p) return { status: CustomCommandStatus.Failure, message: "Hanya bisa dipakai pemain." };
      system.run(() => tukarTangan(p));
      return { status: CustomCommandStatus.Success };
    }
  );
});

world.afterEvents.worldLoad.subscribe(() => {
  mulaiTambang();
  mulaiEnchant();
  mulaiDetektor();
  mulaiKompas();
  world.afterEvents.playerLeave.subscribe(({ playerId }) => lupakanPemain(playerId));
  world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => {
    if (initialSpawn) {
      player.sendMessage(
        "§6[Hardcore Starter Pack] §fKetik §e/setting§f untuk pengaturan. Fitur tambang & panen aktif saat §ejongkok§f."
      );
    }
  });
});
