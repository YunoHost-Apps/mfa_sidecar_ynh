#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/include-idempotence"
CONF="$OUT_DIR/example.conf"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cat > "$CONF" <<'EOF'
server {
  listen 443 ssl;
  server_name demo.example.tld;
}
EOF

HELPER="$ROOT_DIR/scripts/inject_protected_include.py"
INCLUDE="/etc/mfa-sidecar/nginx/protected/demo.example.tld.conf"
python3 "$HELPER" inject "$CONF" "$INCLUDE"
FIRST_HASH=$(sha256sum "$CONF" | awk '{print $1}')
python3 "$HELPER" inject "$CONF" "$INCLUDE"
SECOND_HASH=$(sha256sum "$CONF" | awk '{print $1}')
[[ "$FIRST_HASH" == "$SECOND_HASH" ]]
python3 "$HELPER" remove "$CONF"
python3 "$HELPER" remove "$CONF"
! grep -q "BEGIN mfa-sidecar managed block" "$CONF"

echo "smoke_include_idempotence: ok"
