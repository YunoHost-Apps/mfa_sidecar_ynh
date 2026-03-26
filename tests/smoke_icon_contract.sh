#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="$ROOT_DIR/package-base"

# Package should include a YunoHost logo asset in the conventional package tree.
test -f "$PACKAGE_DIR/assets/logo.png"

# Export pipeline should not forget package assets.
EXPORT_OUT="$ROOT_DIR/tests/out/icon-contract-export"
rm -rf "$EXPORT_OUT"
mkdir -p "$EXPORT_OUT"
"$ROOT_DIR/scripts/export_package_root.sh" >/dev/null

test -f "$ROOT_DIR/dist/package-root/assets/logo.png"

echo "smoke_icon_contract: ok"
