#!/usr/bin/env bash
# Membuat paket siap pasang di folder dist/:
#   Waguri_YSM.mcaddon  -> Waguri_BP + Waguri_RP
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist
mkdir -p dist
zip -qrX dist/Waguri_YSM.mcaddon Waguri_BP Waguri_RP -x '*.DS_Store' -x '*/__pycache__/*'
ls -la dist
