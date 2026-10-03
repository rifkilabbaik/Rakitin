#!/usr/bin/env bash
# Membuat paket siap pasang di folder dist/:
#   Rakitin.mcaddon  -> berisi BP + RP (cukup buka file ini di HP/PC)
#   Rakitin_BP.mcpack, Rakitin_RP.mcpack -> paket terpisah (opsional)
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist

zip_pack() {
  (cd "$1" && zip -qrX "../dist/$1.mcpack" . -x '*.DS_Store' -x '*/__pycache__/*')
}

zip_pack Rakitin_BP
zip_pack Rakitin_RP
zip -qrX dist/Rakitin.mcaddon Rakitin_BP Rakitin_RP -x '*.DS_Store' -x '*/__pycache__/*'

ls -la dist
