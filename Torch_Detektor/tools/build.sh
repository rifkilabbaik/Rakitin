#!/usr/bin/env bash
# Membuat paket siap pasang di folder Torch_Detektor/dist/:
#   TorchDetektor.mcaddon        -> berisi BP + RP + X-Ray (cukup buka file ini di HP/PC)
#   TorchDetektor_BP.mcpack      -> pack inti (perilaku, wajib)
#   TorchDetektor_RP.mcpack      -> tekstur & partikel (wajib)
#   TorchDetektor_XRay_BP.mcpack -> X-Ray tembus dinding (opsional, butuh "Beta APIs")
# Pemakaian: bash Torch_Detektor/tools/build.sh   (bisa dijalankan dari folder mana saja)
set -euo pipefail
cd "$(dirname "$0")/.."

PAKET=(TorchDetektor_BP TorchDetektor_RP TorchDetektor_XRay_BP)
KECUALI=(-x '*.DS_Store' -x '*__pycache__*' -x '*.pyc')

command -v zip >/dev/null || { echo "Perintah 'zip' tidak ditemukan. Pasang dulu paket zip." >&2; exit 1; }

for p in "${PAKET[@]}"; do
  [[ -f "$p/manifest.json" ]] || { echo "manifest.json tidak ditemukan di $p" >&2; exit 1; }
done

rm -rf dist
mkdir -p dist

zip_pack() {
  (cd "$1" && zip -qrX "../dist/$1.mcpack" . "${KECUALI[@]}")
}

for p in "${PAKET[@]}"; do
  zip_pack "$p"
done
zip -qrX dist/TorchDetektor.mcaddon "${PAKET[@]}" "${KECUALI[@]}"

ls -la dist
