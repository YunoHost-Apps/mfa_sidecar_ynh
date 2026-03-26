#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/tampered-vendor"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/vendor"

cp "$ROOT_DIR/package-base/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz" "$OUT_DIR/vendor/"
printf 'x' >> "$OUT_DIR/vendor/authelia-v4.39.16-linux-amd64.tar.gz"

if python3 "$ROOT_DIR/package-base/sources/install_authelia_from_vendor.py" \
  "$ROOT_DIR/package-base/sources/authelia-release.json" \
  "$OUT_DIR/vendor" \
  "$OUT_DIR/install" > "$OUT_DIR/output.txt" 2>&1; then
  echo "expected tampered vendor failure but got success" >&2
  exit 1
fi

grep -q 'sha256 mismatch:' "$OUT_DIR/output.txt"

echo "smoke_tampered_vendor: ok"
