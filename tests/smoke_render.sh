#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/smoke-render"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

python3 "$ROOT_DIR/src/config-render/render_alpha_config.py" \
  "$ROOT_DIR/configs/domain-policy.example.yaml" \
  "$OUT_DIR"

test -f "$OUT_DIR/authelia-config.generated.yml"
test -f "$OUT_DIR/nginx/portal.generated.conf"
test -f "$OUT_DIR/nginx/root_site.generated.conf"
test -f "$OUT_DIR/nginx/nextcloud_exception.generated.conf"
grep -q "default_policy: bypass" "$OUT_DIR/authelia-config.generated.yml"
grep -q "resources:" "$OUT_DIR/authelia-config.generated.yml"
grep -q "auth_request /authelia-auth-root_site;" "$OUT_DIR/nginx/root_site.generated.conf"
grep -q "location / {" "$OUT_DIR/nginx/root_site.generated.conf"
grep -q "domain: example.tld" "$OUT_DIR/authelia-config.generated.yml"
grep -q "location \^~ /admin" "$OUT_DIR/nginx/portal.generated.conf"
grep -q "X-MFA-Sidecar-Admin-Secret" "$OUT_DIR/nginx/portal.generated.conf"
grep -q "proxy_pass http://127.0.0.1:9087;" "$OUT_DIR/nginx/portal.generated.conf"

echo "smoke_render: ok"
