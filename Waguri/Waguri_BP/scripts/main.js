// Waguri YSM - pilih model pemain anime (ala Yes Steve Model) & emote.
//
// Model dan emote disimpan sebagai property entitas pemain
// (waguri:model, waguri:emote) yang disinkronkan ke semua klien, sehingga
// pemain lain di dunia/server yang sama juga melihat modelmu.
import { ItemStack, system, world } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { EMOTE, MODEL } from "./data.js";

const PROP_MODEL = "waguri:model";
const PROP_EMOTE = "waguri:emote";
const PROP_SUDAH_DAPAT = "waguri:lemari_diberikan";
const LAMA_EMOTE = 70; // tick (3,5 detik)

/** @param {import("@minecraft/server").Player} player */
function modelSekarang(player) {
  const v = player.getProperty(PROP_MODEL);
  return typeof v === "number" ? v : 0;
}

/** @param {import("@minecraft/server").Player} player */
function pakaiModel(player, indeks) {
  player.setProperty(PROP_MODEL, indeks);
  player.setProperty(PROP_EMOTE, 0);
  const m = MODEL[indeks];
  player.onScreenDisplay.setActionBar(indeks === 0 ? "§7Kembali ke skin sendiri." : `§dModel: §f${m.nama}`);
  try {
    player.dimension.spawnParticle("minecraft:villager_happy", { ...player.location, y: player.location.y + 1 });
    player.playSound("random.orb", { pitch: 1.4 });
  } catch {
    // abaikan
  }
}

const giliranEmote = new Map(); // player.id -> nomor urut emote terakhir

/** @param {import("@minecraft/server").Player} player */
function putarEmote(player, id) {
  if (modelSekarang(player) === 0) {
    player.onScreenDisplay.setActionBar("§7Pilih model dulu untuk memakai emote.");
    return;
  }
  const urut = (giliranEmote.get(player.id) ?? 0) + 1;
  giliranEmote.set(player.id, urut);
  player.setProperty(PROP_EMOTE, id);
  system.runTimeout(() => {
    if (player.isValid && giliranEmote.get(player.id) === urut) player.setProperty(PROP_EMOTE, 0);
  }, LAMA_EMOTE);
}

/** @param {import("@minecraft/server").Player} player */
function menuEmote(player) {
  const f = new ActionFormData().title("Emote").body("Pilih gerakan:");
  for (const e of EMOTE) f.button(e.nama);
  f.button("§8« Kembali");
  f.show(player).then((r) => {
    if (r.canceled || r.selection === undefined) return;
    if (r.selection >= EMOTE.length) return menuModel(player);
    putarEmote(player, EMOTE[r.selection].id);
  });
}

/** @param {import("@minecraft/server").Player} player */
function menuModel(player) {
  const aktif = modelSekarang(player);
  const f = new ActionFormData()
    .title("Lemari Model")
    .body("Pilih model 3D untuk tubuhmu.\n§7Kaoru Hana wa Rin to Saku - Kaoruko Waguri & teman-teman.");
  MODEL.forEach((m, i) => f.button(`${i === aktif ? "§a» " : ""}${m.nama}\n§8${m.ket.slice(0, 40)}`));
  f.button("§dEmote...");
  f.show(player).then((r) => {
    if (r.canceled || r.selection === undefined) return;
    if (r.selection === MODEL.length) return menuEmote(player);
    pakaiModel(player, r.selection);
  });
}

/** @param {import("@minecraft/server").Player} player */
function beriLemari(player) {
  if (player.getDynamicProperty(PROP_SUDAH_DAPAT)) return;
  const inv = player.getComponent("minecraft:inventory")?.container;
  if (!inv) return;
  const sisa = inv.addItem(new ItemStack("waguri:lemari", 1));
  if (sisa) player.dimension.spawnItem(sisa, player.location);
  player.setDynamicProperty(PROP_SUDAH_DAPAT, true);
  player.sendMessage("§d[Waguri YSM] §fKamu mendapat §dLemari Model§f. Klik kanan untuk memilih model & emote.");
}

system.beforeEvents.startup.subscribe((e) => {
  e.itemComponentRegistry.registerCustomComponent("waguri:lemari", {
    onUse(ev) {
      const player = ev.source;
      // jongkok + klik kanan = langsung buka emote
      if (player.isSneaking) menuEmote(player);
      else menuModel(player);
    },
  });
});

world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => {
  if (initialSpawn) system.runTimeout(() => player.isValid && beriLemari(player), 40);
});
