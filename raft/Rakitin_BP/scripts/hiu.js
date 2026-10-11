// Hiu: muncul di sekitar pemain, menyerang pemain di air (AI entity),
// dan sesekali berenang ke tepi rakit lalu menggigit Fondasi Rakit.
import { EntityDamageCause, system, world } from "@minecraft/server";
import { sedangBadai } from "./cuaca.js";
import { tambahStat } from "./statistik.js";
import {
  acak,
  adalahAir,
  bisaBertahan,
  blokAman,
  jarak,
  lautY,
  overworld,
  partikel,
  peluang,
  pesanBar,
  suara,
} from "./util.js";

const TIPE = "rakit:hiu";
const MASA_TENANG = 3000; // 2,5 menit pertama tanpa hiu
const GIGITAN_PER_BLOK = 4;
const LAJU_RENANG = 0.35; // blok per 2 tick saat menuju rakit

/** Status tiap hiu: santai -> menuju -> gigit -> santai. */
const status = new Map();

function malam() {
  const t = world.getTimeOfDay();
  return t >= 13000 && t <= 23000;
}

function jedaGigit() {
  const j = acak(900, 1800);
  return sedangBadai() ? Math.floor(j / 2) : j;
}

function ambilStatus(hiu) {
  let s = status.get(hiu.id);
  if (!s) {
    s = { mode: "santai", siap: system.currentTick + acak(600, 1200) };
    status.set(hiu.id, s);
  }
  return s;
}

// --- Kemunculan ------------------------------------------------------------
function munculkan() {
  const mulai = world.getDynamicProperty("rakit:mulaiDunia");
  if (typeof mulai === "number" && world.getAbsoluteTime() - mulai < MASA_TENANG) return;

  const dim = overworld();
  const y = lautY();
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id !== "minecraft:overworld" || !bisaBertahan(p)) continue;
    const maks = 1 + (malam() ? 1 : 0) + (sedangBadai() ? 1 : 0);
    const ada = dim.getEntities({ type: TIPE, location: p.location, maxDistance: 48 }).length;
    if (ada >= maks || !peluang(0.35)) continue;

    const sudut = Math.random() * Math.PI * 2;
    const r = acak(18, 28);
    const x = Math.floor(p.location.x + Math.cos(sudut) * r);
    const z = Math.floor(p.location.z + Math.sin(sudut) * r);
    const cukupDalam = [0, 2, 3].every((d) => adalahAir(blokAman(dim, { x, y: y - d, z })));
    if (!cukupDalam) continue;
    dim.spawnEntity(TIPE, { x: x + 0.5, y: y - 2, z: z + 0.5 });
  }
}

// --- Menggigit rakit -------------------------------------------------------
/** Cari Fondasi Rakit di tepi (bersebelahan dengan air) dekat pemain. */
function cariTepiRakit(dim, pusat, hiuLoc) {
  const y = lautY();
  let terbaik;
  let jTerbaik = Infinity;
  const cx = Math.floor(pusat.x);
  const cz = Math.floor(pusat.z);
  for (let dx = -8; dx <= 8; dx++) {
    for (let dz = -8; dz <= 8; dz++) {
      const b = blokAman(dim, { x: cx + dx, y, z: cz + dz });
      if (b?.typeId !== "rakit:fondasi_rakit") continue;
      for (const [ox, oz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const sebelah = { x: b.location.x + ox, y, z: b.location.z + oz };
        if (!adalahAir(blokAman(dim, sebelah))) continue;
        const posAir = { x: sebelah.x + 0.5, y: y - 0.4, z: sebelah.z + 0.5 };
        const j = jarak(posAir, hiuLoc);
        if (j < jTerbaik) {
          jTerbaik = j;
          terbaik = { blok: b.location, posAir };
        }
      }
    }
  }
  return terbaik;
}

function adaPemainDiAir(dim, loc) {
  return world.getAllPlayers().some(
    (p) => p.dimension.id === dim.id && p.isInWater && bisaBertahan(p) && jarak(p.location, loc) < 16
  );
}

function pemainDiRakitTerdekat(dim, loc) {
  let terbaik;
  let j = 24;
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id !== dim.id || !bisaBertahan(p) || p.isInWater) continue;
    const d = jarak(p.location, loc);
    if (d < j) {
      j = d;
      terbaik = p;
    }
  }
  return terbaik;
}

function peringatkan(dim, loc, teks) {
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id === dim.id && jarak(p.location, loc) < 32) pesanBar(p, teks);
  }
}

/** Keputusan tiap detik: kapan hiu mulai mengincar rakit, dan proses menggigit. */
function pikir() {
  const dim = overworld();
  const t = system.currentTick;
  const hidup = new Set();
  for (const hiu of dim.getEntities({ type: TIPE })) {
    hidup.add(hiu.id);
    const s = ambilStatus(hiu);
    const loc = hiu.location;

    if (adaPemainDiAir(dim, loc)) {
      // Ada mangsa di air: biarkan AI hiu menyerang pemain.
      if (s.mode !== "santai") Object.assign(s, { mode: "santai", siap: t + 200 });
      continue;
    }

    if (s.mode === "santai") {
      if (t < s.siap) continue;
      const target = pemainDiRakitTerdekat(dim, loc);
      const tepi = target && cariTepiRakit(dim, target.location, loc);
      if (!tepi) {
        s.siap = t + 400;
        continue;
      }
      Object.assign(s, { mode: "menuju", blok: tepi.blok, posAir: tepi.posAir, mulai: t });
      peringatkan(dim, loc, "§c§l! §r§cHiu mendekati rakitmu! Pukul dia sebelum rakitmu digigit!");
    } else if (s.mode === "menuju") {
      if (t - s.mulai > 400) Object.assign(s, { mode: "santai", siap: t + 400 });
    } else if (s.mode === "gigit") {
      const b = blokAman(dim, s.blok);
      if (b?.typeId !== "rakit:fondasi_rakit") {
        Object.assign(s, { mode: "santai", siap: t + jedaGigit() });
        continue;
      }
      s.gigitan += 1;
      const tengah = { x: s.blok.x + 0.5, y: s.blok.y + 0.5, z: s.blok.z + 0.5 };
      suara(dim, "mob.zombie.wood", tengah, 0.8, 0.8);
      partikel(dim, "minecraft:water_splash_particle_manual", tengah);
      if (s.gigitan >= GIGITAN_PER_BLOK) {
        dim.setBlockType(s.blok, "minecraft:water");
        suara(dim, "random.break", tengah);
        peringatkan(dim, tengah, "§c§lHiu menghancurkan sebagian rakitmu!");
        Object.assign(s, { mode: "santai", siap: t + jedaGigit() });
      }
    }
  }
  for (const id of status.keys()) if (!hidup.has(id)) status.delete(id);
}

/** Gerakkan hiu yang sedang menuju / menggigit rakit. */
function gerak() {
  const dim = overworld();
  for (const hiu of dim.getEntities({ type: TIPE })) {
    const s = status.get(hiu.id);
    if (!s || (s.mode !== "menuju" && s.mode !== "gigit")) continue;
    const loc = hiu.location;
    const tujuan = s.posAir;
    const sasaran = { x: s.blok.x + 0.5, y: s.blok.y + 0.3, z: s.blok.z + 0.5 };
    const j = jarak(loc, tujuan);
    if (s.mode === "menuju" && j < 1) {
      Object.assign(s, { mode: "gigit", gigitan: 0 });
    }
    const langkah = Math.min(LAJU_RENANG, j);
    const baru =
      j < 0.01
        ? tujuan
        : {
            x: loc.x + ((tujuan.x - loc.x) / j) * langkah,
            y: loc.y + ((tujuan.y - loc.y) / j) * langkah,
            z: loc.z + ((tujuan.z - loc.z) / j) * langkah,
          };
    hiu.teleport(baru, { facingLocation: sasaran });
  }
}

export function mulaiHiu() {
  system.runInterval(munculkan, 200);
  system.runInterval(pikir, 20);
  system.runInterval(gerak, 2);

  // Hiu yang dipukul pemain berhenti mengincar rakit untuk sementara.
  world.afterEvents.entityHurt.subscribe(({ hurtEntity, damageSource }) => {
    if (hurtEntity.typeId !== TIPE) return;
    if (damageSource.damagingEntity?.typeId !== "minecraft:player") return;
    const s = ambilStatus(hurtEntity);
    if (s.mode !== "santai") pesanBar(/** @type {any} */ (damageSource.damagingEntity), "§aHiu kabur dari rakit!");
    Object.assign(s, { mode: "santai", siap: system.currentTick + jedaGigit() });
  });

  world.afterEvents.entityDie.subscribe(({ deadEntity, damageSource }) => {
    if (deadEntity.typeId !== TIPE) return;
    status.delete(deadEntity.id);
    const pembunuh = damageSource.damagingEntity;
    if (pembunuh?.typeId !== "minecraft:player") return;
    const p = world.getAllPlayers().find((x) => x.id === pembunuh.id);
    if (p) tambahStat(p, "hiu");
  });
}

/** Bonus damage Tombak terhadap hiu (dipanggil dari komponen item). */
export function seranganTombak(penyerang, sasaran, bonus) {
  if (sasaran.typeId !== TIPE) return;
  system.run(() => {
    if (!sasaran.isValid) return;
    sasaran.applyDamage(bonus, { cause: EntityDamageCause.entityAttack, damagingEntity: penyerang });
  });
}
