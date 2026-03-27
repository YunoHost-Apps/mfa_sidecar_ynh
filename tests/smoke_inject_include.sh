#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/inject-include"
CONF="$OUT_DIR/example.conf"
LOC_CONF="$OUT_DIR/location.conf"
INDEX_JSON="$OUT_DIR/render-index.json"
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

cat > "$LOC_CONF" <<'EOF'
server {
  listen 443 ssl;
  server_name demo.example.tld;

  location ^~ /nextcloud {
    client_max_body_size 10G;
    fastcgi_pass unix:/run/php.sock;
  }
}
EOF

python3 "$ROOT_DIR/scripts/inject_protected_include.py" inject-into-location "$LOC_CONF" "/nextcloud" "/authelia-auth-nextcloud" "auth.example.tld"
grep -q "auth_request /authelia-auth-nextcloud;" "$LOC_CONF"
grep -q "error_page 401 =302 https://auth.example.tld/?rd=\$scheme://\$http_host\$request_uri;" "$LOC_CONF"
grep -q "client_max_body_size 10G;" "$LOC_CONF"
python3 "$ROOT_DIR/scripts/inject_protected_include.py" remove "$LOC_CONF"
! grep -q "BEGIN mfa-sidecar managed block" "$LOC_CONF"

cat > "$INDEX_JSON" <<EOF
{
  "enabled": [
    {
      "id": "nextcloud",
      "path": "/nextcloud",
      "portal_domain": "auth.example.tld",
      "auth_location": "/authelia-auth-nextcloud",
      "target_conf": "$LOC_CONF"
    }
  ],
  "disabled": []
}
EOF
python3 "$ROOT_DIR/scripts/inject_protected_include.py" reinject-all "$INDEX_JSON"
grep -q "auth_request /authelia-auth-nextcloud;" "$LOC_CONF"

echo "smoke_inject_include: ok"
