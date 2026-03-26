#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOVE_SCRIPT="$ROOT_DIR/package-base/scripts/remove"

grep -q 'rm -rf /etc/mfa-sidecar' "$REMOVE_SCRIPT"
grep -q 'rm -rf /var/lib/mfa_sidecar' "$REMOVE_SCRIPT"
grep -Eq 'rm -rf "?\$install_dir"?' "$REMOVE_SCRIPT"
grep -q 'rm -f /etc/systemd/system/mfa-sidecar-authelia.service' "$REMOVE_SCRIPT"
grep -q 'rm -f /etc/systemd/system/mfa-sidecar-admin.service' "$REMOVE_SCRIPT"
grep -q 'portal_nginx_conf="/etc/nginx/conf.d/\${domain}.conf"' "$REMOVE_SCRIPT"
grep -q 'portal_nginx_dir="/etc/nginx/conf.d/\${domain}.d"' "$REMOVE_SCRIPT"
grep -q 'rm -f "\$portal_nginx_conf"' "$REMOVE_SCRIPT"
grep -q 'rmdir "\$portal_nginx_dir"' "$REMOVE_SCRIPT"

echo "smoke_remove_contract: ok"
