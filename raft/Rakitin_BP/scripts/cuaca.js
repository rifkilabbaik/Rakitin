// Mencatat cuaca dunia (dipakai penampung hujan, hiu, dan puing).
import { WeatherType, world } from "@minecraft/server";
import { pesanSemua } from "./util.js";

const KUNCI = "rakit:cuaca";
let cuaca = WeatherType.Clear;

export function sedangHujan() {
  return cuaca === WeatherType.Rain || cuaca === WeatherType.Thunder;
}

export function sedangBadai() {
  return cuaca === WeatherType.Thunder;
}

export function mulaiCuaca() {
  const tersimpan = world.getDynamicProperty(KUNCI);
  if (typeof tersimpan === "string") cuaca = /** @type {WeatherType} */ (tersimpan);

  world.afterEvents.weatherChange.subscribe((e) => {
    if (e.dimension !== "minecraft:overworld" && e.dimension !== "overworld") return;
    const sebelumnya = cuaca;
    cuaca = e.newWeather;
    world.setDynamicProperty(KUNCI, cuaca);
    if (cuaca === WeatherType.Thunder && sebelumnya !== WeatherType.Thunder) {
      pesanSemua("§c§l[Badai]§r§c Badai datang! Hiu menjadi lebih ganas.");
    } else if (cuaca === WeatherType.Rain && sebelumnya === WeatherType.Clear) {
      pesanSemua("§9[Hujan]§7 Hujan turun. Penampung Air Hujan mulai terisi.");
    }
  });
}
