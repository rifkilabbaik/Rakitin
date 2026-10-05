#!/usr/bin/env bash
# Membuat paket siap pasang di folder dist/:
#   Asta.mcaddon       -> Asta_BP + Asta_RP (pedang, armor iblis, elytra)
#   Asta_RP.mcpack     -> hanya tekstur armor & elytra (tanpa pedang baru)
#   Asta_Skin.mcpack   -> skin pack Asta
#   asta.png / asta_iblis.png -> file skin untuk diimpor langsung
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist

zip_pack() {
  (cd "$1" && zip -qrX "../dist/$1.mcpack" . -x '*.DS_Store' -x '*/__pycache__/*')
}

zip_pack Asta_RP
zip_pack Asta_Skin
zip -qrX dist/Asta.mcaddon Asta_BP Asta_RP -x '*.DS_Store' -x '*/__pycache__/*'
cp Asta_Skin/asta.png Asta_Skin/asta_iblis.png dist/

ls -la dist
