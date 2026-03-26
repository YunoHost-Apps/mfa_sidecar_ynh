#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/fetch-contract"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

python3 "$ROOT_DIR/package-base/sources/install_authelia_from_vendor.py" \
  "$ROOT_DIR/package-base/sources/authelia-release.json" \
  "$ROOT_DIR/package-base/sources/vendor" \
  "$OUT_DIR" > "$OUT_DIR/result.json"

grep -q '"version": "4.39.16"' "$OUT_DIR/result.json"
grep -q '"verified": true' "$OUT_DIR/result.json"
test -x "$OUT_DIR/authelia"

echo "smoke_fetch_contract: ok"
