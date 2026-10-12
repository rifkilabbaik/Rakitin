#!/usr/bin/env bash
# Membuat paket siap pasang di dist/:
#   HardcoreStarterPack.mcaddon dan HardcoreStarterPack_BP.mcpack
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist
(cd HardcoreStarterPack_BP && zip -qrX ../dist/HardcoreStarterPack_BP.mcpack . -x '*.DS_Store' -x '*/__pycache__/*')
zip -qrX dist/HardcoreStarterPack.mcaddon HardcoreStarterPack_BP -x '*.DS_Store' -x '*/__pycache__/*'
ls -la dist
