#!/usr/bin/env bash
set -euo pipefail

REQ="/workspace/backend/requirements.txt"
STAMP="/workspace/.deps_installed"

echo "[startup] Renku session starting"

if [[ -f "$REQ" ]]; then
  if [[ ! -f "$STAMP" ]]; then
    echo "[startup] Installing Python dependencies"
    pip install --user --no-cache-dir -r "$REQ"
    touch "$STAMP"
  else
    echo "[startup] Dependencies already installed"
  fi
else
  echo "[startup] No requirements.txt found, skipping"
fi
