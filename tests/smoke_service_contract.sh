#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTHELIA_SERVICE="$ROOT_DIR/package-base/sources/authelia.service"
ADMIN_SERVICE="$ROOT_DIR/package-base/sources/mfa-sidecar-admin.service"

grep -q '^ExecStart=/usr/local/bin/authelia --config /etc/mfa-sidecar/authelia/configuration.yml$' "$AUTHELIA_SERVICE"
grep -q '^EnvironmentFile=-/etc/mfa-sidecar/mfa-sidecar.env$' "$AUTHELIA_SERVICE"
grep -q '^WorkingDirectory=/opt/yunohost/mfa_sidecar$' "$AUTHELIA_SERVICE"

grep -q '^ExecStart=/usr/bin/python3 /opt/yunohost/mfa_sidecar/bin/admin_ui_app.py$' "$ADMIN_SERVICE"
grep -q '^Environment=MFA_SIDECAR_ADMIN_PORT=9087$' "$ADMIN_SERVICE"
grep -q '^EnvironmentFile=-/etc/mfa-sidecar/mfa-sidecar.env$' "$ADMIN_SERVICE"

echo "smoke_service_contract: ok"
