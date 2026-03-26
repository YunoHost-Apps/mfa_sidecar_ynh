#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/publication-shape"
EXPORT_DIR="$OUT_DIR/exported-package-root"
DEV_CLONE_DIR="$OUT_DIR/dev-root-clone"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

"$ROOT_DIR/scripts/export_package_root.sh" "$EXPORT_DIR" >/dev/null

# Positive case: the exported package-root tree should look directly installable by YunoHost.
test -f "$EXPORT_DIR/manifest.toml"
test -f "$EXPORT_DIR/tests.toml"
test -d "$EXPORT_DIR/scripts"
test -d "$EXPORT_DIR/conf"
test -d "$EXPORT_DIR/sources"

grep -q '^packaging_format = 2$' "$EXPORT_DIR/manifest.toml"
test -x "$EXPORT_DIR/scripts/install"
test -x "$EXPORT_DIR/scripts/upgrade"
test -x "$EXPORT_DIR/scripts/remove"

# Negative/guardrail case: the dev repo root is not directly installable by YunoHost from repo root.
git clone --depth 1 "file://$ROOT_DIR" "$DEV_CLONE_DIR" >/dev/null 2>&1
if [[ -f "$DEV_CLONE_DIR/manifest.toml" ]]; then
  echo "dev repo root unexpectedly contains manifest.toml; publication-shape assumptions changed" >&2
  exit 1
fi

test -f "$DEV_CLONE_DIR/package-base/manifest.toml"

echo "smoke_publication_shape: ok"
