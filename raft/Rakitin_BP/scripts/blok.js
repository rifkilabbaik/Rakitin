// Komponen custom untuk blok (penyaring, penampung, pot, layar, kemudi)
// dan item (botol, minuman, kail, tombak, buku, inti portal, fondasi).
import { ItemStack } from "@minecraft/server";
import { sedangHujan } from "./cuaca.js";
import { minum } from "./haus.js";
import { seranganTombak } from "./hiu.js";
import { aktifkanKail } from "./kail.js";
import { interaksiKemudi, infoLayar } from "./layar.js";
import { gunakanIntiPortal } from "./portal.js";
import { bukaBuku, tambahStat } from "./statistik.js";
import {
  acak,
  adalahAir,
  aturState,
  bacaState,
  beriItem,
  itemDiTangan,
  pakaiItemDiTangan,
  partikel,
  peluang,
  pesanBar,
  suara,
} from "./util.js";

/** Ganti satu item di tangan dengan item lain (misal botol kosong -> air laut). */
function tukarSatu(player, idBaru) {
  pakaiItemDiTangan(player, 1);
  beriItem(player, new ItemStack(idBaru, 1));
}

// --- Penyaring air ---------------------------------------------------------
const penyaring = {
  onPlayerInteract(e) {
    const { block, player } = e;
    if (!player) return;
    const isi = bacaState(block, "rakit:isi");
    const tangan = itemDiTangan(player)?.typeId;
    if (isi === 0 && tangan === "rakit:air_laut") {
      tukarSatu(player, "rakit:botol_kosong");
      aturState(block, "rakit:isi", 1);
      suara(block.dimension, "bucket.empty_water", block.location);
      pesanBar(player, "§bMenyaring air laut... §7(±30 detik)");
    } else if (isi === 4 && tangan === "rakit:botol_kosong") {
      tukarSatu(player, "rakit:air_bersih");
      aturState(block, "rakit:isi", 0);
      suara(block.dimension, "bucket.fill_water", block.location);
      pesanBar(player, "§a+1 Botol Air Bersih");
    } else if (isi === 0) {
      pesanBar(player, "§7Penyaring kosong. Masukkan §fBotol Air Laut§7.");
    } else if (isi === 4) {
      pesanBar(player, "§aAir bersih siap! §7Ambil dengan §fBotol Kosong§7.");
    } else {
      pesanBar(player, `§bSedang menyaring... §7(${isi}/3)`);
    }
  },
  onTick(e) {
    const isi = bacaState(e.block, "rakit:isi");
    if (isi >= 1 && isi <= 3) {
      aturState(e.block, "rakit:isi", isi + 1);
      if (isi + 1 === 4) suara(e.dimension, "random.orb", e.block.location, 0.6, 1.2);
    }
  },
};

// --- Penampung air hujan ---------------------------------------------------
function langitTerbuka(block) {
  const atas = block.dimension.getTopmostBlock({ x: block.location.x, z: block.location.z });
  return !atas || atas.location.y <= block.location.y;
}

const penampung = {
  onPlayerInteract(e) {
    const { block, player } = e;
    if (!player) return;
    const isi = bacaState(block, "rakit:isi");
    if (itemDiTangan(player)?.typeId === "rakit:botol_kosong" && isi > 0) {
      tukarSatu(player, "rakit:air_bersih");
      aturState(block, "rakit:isi", isi - 1);
      suara(block.dimension, "bucket.fill_water", block.location);
      pesanBar(player, `§a+1 Botol Air Bersih §7(sisa ${isi - 1}/4)`);
    } else {
      const ket = langitTerbuka(block) ? "" : " §c(tertutup atap!)";
      pesanBar(player, `§9Penampung Hujan: §f${isi}/4 botol${ket}`);
    }
  },
  onTick(e) {
    const isi = bacaState(e.block, "rakit:isi");
    if (isi < 4 && sedangHujan() && peluang(0.5) && langitTerbuka(e.block)) {
      aturState(e.block, "rakit:isi", isi + 1);
    }
  },
};

// --- Pot tanam -------------------------------------------------------------
const BIBIT = {
  "minecraft:wheat_seeds": 0,
  "minecraft:potato": 1,
  "minecraft:carrot": 2,
  "minecraft:beetroot_seeds": 3,
};

const PANEN = [
  () => [["minecraft:wheat", 1], ["minecraft:wheat_seeds", acak(1, 2)]],
  () => [["minecraft:potato", acak(2, 4)]],
  () => [["minecraft:carrot", acak(2, 4)]],
  () => [["minecraft:beetroot", 1], ["minecraft:beetroot_seeds", acak(1, 2)]],
];

const pot = {
  onPlayerInteract(e) {
    const { block, player } = e;
    if (!player) return;
    const tahap = bacaState(block, "rakit:tahap");
    const tangan = itemDiTangan(player)?.typeId;
    const atas = { x: block.location.x + 0.5, y: block.location.y + 0.8, z: block.location.z + 0.5 };

    if (tahap === 0 && tangan && tangan in BIBIT) {
      pakaiItemDiTangan(player, 1);
      aturState(block, "rakit:jenis", BIBIT[tangan]);
      aturState(block, "rakit:tahap", 1);
      suara(block.dimension, "dig.grass", atas);
    } else if ((tahap === 1 || tahap === 2) && tangan === "minecraft:bone_meal") {
      pakaiItemDiTangan(player, 1);
      aturState(block, "rakit:tahap", tahap + 1);
      partikel(block.dimension, "minecraft:crop_growth_emitter", atas);
      suara(block.dimension, "item.bone_meal.use", atas);
    } else if (tahap === 3) {
      const jenis = bacaState(block, "rakit:jenis");
      for (const [id, n] of PANEN[jenis]()) beriItem(player, new ItemStack(id, n));
      aturState(block, "rakit:tahap", 0);
      suara(block.dimension, "dig.grass", atas);
      pesanBar(player, "§aPanen berhasil!");
    } else if (tahap === 0) {
      pesanBar(player, "§7Tanam §fbibit gandum, kentang, wortel, §7atau §fbibit bit§7.");
    } else {
      pesanBar(player, `§aTanaman tumbuh... §7(${tahap}/3) Gunakan Bone Meal agar lebih cepat.`);
    }
  },
  onTick(e) {
    const tahap = bacaState(e.block, "rakit:tahap");
    if (tahap === 1 || tahap === 2) aturState(e.block, "rakit:tahap", tahap + 1);
  },
};

// --- Item ------------------------------------------------------------------
const botolKosong = {
  onUse(e) {
    const player = e.source;
    const hit = player.getBlockFromViewDirection({ maxDistance: 5, includeLiquidBlocks: true, includePassableBlocks: true });
    if (!hit || !adalahAir(hit.block)) return;
    tukarSatu(player, "rakit:air_laut");
    suara(player.dimension, "bucket.fill_water", hit.block.location);
  },
};

const minuman = {
  onConsume(e, p) {
    const prm = /** @type {any} */ (p.params);
    if (e.source.typeId !== "minecraft:player") return;
    minum(e.source, prm.haus ?? 0, !!prm.asin);
  },
};

const kail = {
  onUse(e, p) {
    const prm = /** @type {any} */ (p.params);
    aktifkanKail(e.source, prm.tier ?? 1);
  },
};

const tombak = {
  onHitEntity(e, p) {
    const prm = /** @type {any} */ (p.params);
    seranganTombak(e.attackingEntity, e.hitEntity, prm.bonus_hiu ?? 6);
  },
};

const buku = {
  onUse(e) {
    bukaBuku(e.source);
  },
};

const intiPortal = {
  onUse(e) {
    gunakanIntiPortal(e.source);
  },
};

/** Klik kanan ke permukaan air memasang fondasi langsung di laut. */
const fondasiAir = {
  onUse(e) {
    const player = e.source;
    const item = e.itemStack;
    if (!item) return;
    const hit = player.getBlockFromViewDirection({ maxDistance: 6, includeLiquidBlocks: true, includePassableBlocks: true });
    if (!hit || !adalahAir(hit.block)) return;
    const atas = hit.block.above();
    if (!atas?.isAir) return;
    hit.block.setType(item.typeId);
    pakaiItemDiTangan(player, 1);
    suara(player.dimension, "dig.wood", hit.block.location);
    tambahStat(player, "fondasi");
  },
};

/** Didaftarkan saat startup (lihat main.js). */
export function daftarKomponen(blokReg, itemReg) {
  blokReg.registerCustomComponent("rakit:penyaring", penyaring);
  blokReg.registerCustomComponent("rakit:penampung", penampung);
  blokReg.registerCustomComponent("rakit:pot", pot);
  blokReg.registerCustomComponent("rakit:layar", {
    onPlayerInteract(e) {
      if (e.player) infoLayar(e.player, e.block);
    },
  });
  blokReg.registerCustomComponent("rakit:kemudi", {
    onPlayerInteract(e) {
      if (e.player) interaksiKemudi(e.player, e.block);
    },
  });

  itemReg.registerCustomComponent("rakit:botol_kosong", botolKosong);
  itemReg.registerCustomComponent("rakit:minuman", minuman);
  itemReg.registerCustomComponent("rakit:kail", kail);
  itemReg.registerCustomComponent("rakit:tombak", tombak);
  itemReg.registerCustomComponent("rakit:buku", buku);
  itemReg.registerCustomComponent("rakit:inti_portal", intiPortal);
  itemReg.registerCustomComponent("rakit:fondasi_air", fondasiAir);
}
