#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUT_DIR=${1:-"$ROOT_DIR/dist/package-root"}

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cp "$ROOT_DIR/package-base/manifest.toml" "$OUT_DIR/manifest.toml"
cp "$ROOT_DIR/package-base/tests.toml" "$OUT_DIR/tests.toml"
cp -R "$ROOT_DIR/package-base/assets" "$OUT_DIR/assets"
cp -R "$ROOT_DIR/package-base/conf" "$OUT_DIR/conf"
cp -R "$ROOT_DIR/package-base/scripts" "$OUT_DIR/scripts"
cp -R "$ROOT_DIR/package-base/sources" "$OUT_DIR/sources"

find "$OUT_DIR" -type d -exec chmod 755 {} +
find "$OUT_DIR" -type f -path '*/scripts/*' -exec chmod 755 {} +
find "$OUT_DIR" -type f ! -path '*/scripts/*' -exec chmod 644 {} +

echo "Exported package-root tree to: $OUT_DIR"
