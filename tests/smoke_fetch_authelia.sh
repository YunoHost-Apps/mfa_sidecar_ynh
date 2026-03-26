#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/fetch-authelia"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

python3 "$ROOT_DIR/scripts/fetch_authelia_release.py" \
  "$ROOT_DIR/deploy/authelia-install/pinned-release.json" \
  "$OUT_DIR" > "$OUT_DIR/result.json"

test -f "$OUT_DIR/authelia"
grep -q '"verified": true' "$OUT_DIR/result.json"
"$OUT_DIR/authelia" --version >/dev/null 2>&1 || true

echo "smoke_fetch_authelia: ok"
