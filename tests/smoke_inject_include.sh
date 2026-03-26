#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/inject-include"
CONF="$OUT_DIR/example.conf"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cat > "$CONF" <<'EOF'
server {
  listen 443 ssl;
  server_name demo.example.tld;
}
EOF

python3 "$ROOT_DIR/scripts/inject_protected_include.py" inject "$CONF" "/etc/mfa-sidecar/nginx/protected/demo.example.tld.conf"
grep -q "BEGIN mfa-sidecar managed block" "$CONF"
grep -q "include /etc/mfa-sidecar/nginx/protected/demo.example.tld.conf;" "$CONF"
python3 "$ROOT_DIR/scripts/inject_protected_include.py" remove "$CONF"
! grep -q "BEGIN mfa-sidecar managed block" "$CONF"

echo "smoke_inject_include: ok"
