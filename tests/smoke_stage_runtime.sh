#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/stage-runtime"
GEN_DIR="$ROOT_DIR/tests/out/stage-runtime-generated"
rm -rf "$OUT_DIR" "$GEN_DIR"
mkdir -p "$OUT_DIR" "$GEN_DIR"

python3 "$ROOT_DIR/src/config-render/render_alpha_config.py" \
  "$ROOT_DIR/configs/domain-policy.example.yaml" \
  "$GEN_DIR"
python3 "$ROOT_DIR/scripts/stage_alpha_runtime.py" "$GEN_DIR" "$OUT_DIR"

test -f "$OUT_DIR/etc/mfa-sidecar/authelia/configuration.yml"
test -f "$OUT_DIR/etc/mfa-sidecar/runtime-metadata.json"
test -f "$OUT_DIR/etc/mfa-sidecar/nginx/portal.conf"
test -f "$OUT_DIR/etc/mfa-sidecar/nginx/protected/root_site.conf"
test -f "$OUT_DIR/etc/mfa-sidecar/nginx/protected/nextcloud_exception.conf"
grep -q '"backend": "file"' "$OUT_DIR/etc/mfa-sidecar/runtime-metadata.json"
grep -q '"user_database_path": "/etc/mfa-sidecar/authelia/users.yml"' "$OUT_DIR/etc/mfa-sidecar/runtime-metadata.json"

echo "smoke_stage_runtime: ok"
