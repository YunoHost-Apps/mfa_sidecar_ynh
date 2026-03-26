#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTHELIA_SERVICE="$ROOT_DIR/package-base/sources/authelia.service"
ADMIN_SERVICE="$ROOT_DIR/package-base/sources/mfa-sidecar-admin.service"

grep -q '^User=mfa_sidecar$' "$AUTHELIA_SERVICE"
grep -q '^Group=mfa_sidecar$' "$AUTHELIA_SERVICE"
grep -q '^ExecStart=/opt/yunohost/mfa_sidecar/bin/authelia --config /etc/mfa-sidecar/authelia/configuration.yml$' "$AUTHELIA_SERVICE"
grep -q '^EnvironmentFile=-/etc/mfa-sidecar/mfa-sidecar.env$' "$AUTHELIA_SERVICE"
grep -q '^PrivateTmp=true$' "$AUTHELIA_SERVICE"
grep -q '^ProtectHome=true$' "$AUTHELIA_SERVICE"
grep -q '^ProtectSystem=strict$' "$AUTHELIA_SERVICE"
grep -q '^ReadWritePaths=/etc/mfa-sidecar /var/lib/mfa_sidecar /opt/yunohost/mfa_sidecar/run$' "$AUTHELIA_SERVICE"
grep -q '^UMask=0027$' "$AUTHELIA_SERVICE"
grep -q '^WorkingDirectory=/opt/yunohost/mfa_sidecar$' "$AUTHELIA_SERVICE"
! grep -q '^ExecStartPre=' "$AUTHELIA_SERVICE"

grep -q '^User=mfa_sidecar$' "$ADMIN_SERVICE"
grep -q '^Group=mfa_sidecar$' "$ADMIN_SERVICE"
grep -q '^ExecStart=/usr/bin/python3 /opt/yunohost/mfa_sidecar/bin/admin_ui_app.py$' "$ADMIN_SERVICE"
grep -q '^Environment=MFA_SIDECAR_ADMIN_PORT=9087$' "$ADMIN_SERVICE"
grep -q '^EnvironmentFile=-/etc/mfa-sidecar/mfa-sidecar.env$' "$ADMIN_SERVICE"
grep -q '^PrivateTmp=true$' "$ADMIN_SERVICE"
grep -q '^ProtectHome=true$' "$ADMIN_SERVICE"
grep -q '^ProtectSystem=strict$' "$ADMIN_SERVICE"
grep -q '^ReadWritePaths=/etc/mfa-sidecar /var/lib/mfa_sidecar /opt/yunohost/mfa_sidecar /etc/nginx/conf.d$' "$ADMIN_SERVICE"
grep -q '^UMask=0027$' "$ADMIN_SERVICE"
grep -q '^WorkingDirectory=/opt/yunohost/mfa_sidecar$' "$ADMIN_SERVICE"
! grep -q '^ExecStartPre=' "$ADMIN_SERVICE"

echo "smoke_service_contract: ok"
