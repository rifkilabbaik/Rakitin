#!/usr/bin/env bash
# Membuat paket siap pasang di dist/:
#   HardcoreStarterPack.mcaddon (BP + RP) dan .mcpack terpisah
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist
for p in HardcoreStarterPack_BP HardcoreStarterPack_RP; do
  (cd "$p" && zip -qrX "../dist/$p.mcpack" . -x '*.DS_Store' -x '*/__pycache__/*')
done
zip -qrX dist/HardcoreStarterPack.mcaddon HardcoreStarterPack_BP HardcoreStarterPack_RP -x '*.DS_Store' -x '*/__pycache__/*'
ls -la dist
