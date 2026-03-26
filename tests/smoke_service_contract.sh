#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTHELIA_SERVICE="$ROOT_DIR/package-base/sources/authelia.service"
ADMIN_SERVICE="$ROOT_DIR/package-base/sources/mfa-sidecar-admin.service"

grep -q '^ExecStart=/usr/local/bin/authelia --config /etc/mfa-sidecar/authelia/configuration.yml$' "$AUTHELIA_SERVICE"
grep -q '^EnvironmentFile=-/etc/mfa-sidecar/mfa-sidecar.env$' "$AUTHELIA_SERVICE"
grep -q '^PrivateTmp=true$' "$AUTHELIA_SERVICE"
grep -q '^ProtectHome=true$' "$AUTHELIA_SERVICE"
grep -q '^UMask=0077$' "$AUTHELIA_SERVICE"
! grep -q '^WorkingDirectory=' "$AUTHELIA_SERVICE"
! grep -q '^ExecStartPre=' "$AUTHELIA_SERVICE"
! grep -q '^ReadWritePaths=' "$AUTHELIA_SERVICE"
! grep -q '^ProtectSystem=' "$AUTHELIA_SERVICE"

grep -q '^ExecStart=/usr/bin/python3 /opt/yunohost/mfa_sidecar/bin/admin_ui_app.py$' "$ADMIN_SERVICE"
grep -q '^Environment=MFA_SIDECAR_ADMIN_PORT=9087$' "$ADMIN_SERVICE"
grep -q '^EnvironmentFile=-/etc/mfa-sidecar/mfa-sidecar.env$' "$ADMIN_SERVICE"
grep -q '^PrivateTmp=true$' "$ADMIN_SERVICE"
grep -q '^ProtectHome=true$' "$ADMIN_SERVICE"
grep -q '^UMask=0077$' "$ADMIN_SERVICE"
! grep -q '^WorkingDirectory=' "$ADMIN_SERVICE"
! grep -q '^ExecStartPre=' "$ADMIN_SERVICE"
! grep -q '^ReadWritePaths=' "$ADMIN_SERVICE"
! grep -q '^ProtectSystem=' "$ADMIN_SERVICE"

echo "smoke_service_contract: ok"
