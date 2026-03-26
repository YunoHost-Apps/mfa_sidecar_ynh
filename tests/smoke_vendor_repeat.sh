#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_ROOT="$ROOT_DIR/tests/out/vendor-repeat"
rm -rf "$OUT_ROOT"
mkdir -p "$OUT_ROOT"

for i in 1 2 3; do
  OUT_DIR="$OUT_ROOT/run-$i"
  mkdir -p "$OUT_DIR"
  python3 "$ROOT_DIR/package-base/sources/install_authelia_from_vendor.py" \
    "$ROOT_DIR/package-base/sources/authelia-release.json" \
    "$ROOT_DIR/package-base/sources/vendor" \
    "$OUT_DIR" > "$OUT_DIR/result.json"
  test -x "$OUT_DIR/authelia"
  SHA=$(sha256sum "$OUT_DIR/authelia" | awk '{print $1}')
  echo "$SHA" > "$OUT_DIR/binary.sha256"
done

cmp "$OUT_ROOT/run-1/binary.sha256" "$OUT_ROOT/run-2/binary.sha256"
cmp "$OUT_ROOT/run-2/binary.sha256" "$OUT_ROOT/run-3/binary.sha256"

echo "smoke_vendor_repeat: ok"
