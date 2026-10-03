// Inti Portal End: membangun portal End yang langsung aktif.
// Mengalahkan Naga Ender = menang.
import { BlockPermutation, world } from "@minecraft/server";
import { statMaks } from "./statistik.js";
import { arahPandang, blokAman, pakaiItemDiTangan, pesanBar, suara } from "./util.js";

// Arah hadap bingkai supaya semuanya menghadap ke tengah portal.
function hadapBingkai(dx, dz) {
  if (dz === -2) return "south";
  if (dz === 2) return "north";
  if (dx === -2) return "east";
  return "west";
}

function bingkai(arah) {
  try {
    return BlockPermutation.resolve("minecraft:end_portal_frame", {
      end_portal_eye_bit: true,
      "minecraft:cardinal_direction": arah,
    });
  } catch {
    return BlockPermutation.resolve("minecraft:end_portal_frame");
  }
}

export function gunakanIntiPortal(player) {
  const dim = player.dimension;
  if (dim.id === "minecraft:the_end") {
    pesanBar(player, "§cKamu sudah berada di The End!");
    return;
  }
  const arah = arahPandang(player);
  const cx = Math.floor(player.location.x) + arah.dx * 3;
  const cz = Math.floor(player.location.z) + arah.dz * 3;
  const y = Math.floor(player.location.y);

  for (let dx = -2; dx <= 2; dx++) {
    for (let dz = -2; dz <= 2; dz++) {
      for (let dy = 0; dy <= 1; dy++) {
        if (!blokAman(dim, { x: cx + dx, y: y + dy, z: cz + dz })?.isAir) {
          pesanBar(player, "§cButuh ruang kosong 5x5 (setinggi 2 blok) di depanmu untuk portal.");
          return;
        }
      }
    }
  }

  for (let dx = -2; dx <= 2; dx++) {
    for (let dz = -2; dz <= 2; dz++) {
      const lok = { x: cx + dx, y, z: cz + dz };
      const tepi = Math.abs(dx) === 2 || Math.abs(dz) === 2;
      const sudut = Math.abs(dx) === 2 && Math.abs(dz) === 2;
      if (sudut) continue;
      if (tepi) dim.getBlock(lok)?.setPermutation(bingkai(hadapBingkai(dx, dz)));
      else dim.setBlockType(lok, "minecraft:end_portal");
    }
  }
  pakaiItemDiTangan(player, 1);
  suara(dim, "block.end_portal.spawn", { x: cx + 0.5, y, z: cz + 0.5 });
  world.sendMessage(
    `§5[Portal] §f${player.name} membuka §5Portal End§f! Siapkan senjata dan baju besi sebelum melawan §dNaga Ender§f.`
  );
}

export function mulaiPortal() {
  world.afterEvents.entityDie.subscribe(({ deadEntity }) => {
    if (deadEntity.typeId !== "minecraft:ender_dragon") return;
    for (const p of world.getAllPlayers()) {
      p.onScreenDisplay.setTitle("§6§lKAMU MENANG!", {
        subtitle: "§eNaga Ender telah dikalahkan. Lautan adalah milikmu!",
        fadeInDuration: 20,
        stayDuration: 120,
        fadeOutDuration: 40,
      });
      suara(p.dimension, "random.totem", p.location);
      statMaks(p, "naga", 1);
    }
    world.sendMessage("§6§l[Rakitin] Selamat! Naga Ender telah dikalahkan. Kalian memenangkan permainan!");
    world.setDynamicProperty("rakit:menang", true);
  });
}
