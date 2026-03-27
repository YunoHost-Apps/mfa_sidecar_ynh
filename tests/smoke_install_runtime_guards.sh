#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"
UPGRADE_SCRIPT="$ROOT_DIR/package-base/scripts/upgrade"
RESTORE_SCRIPT="$ROOT_DIR/package-base/scripts/restore"

grep -q '_mfa_sidecar_wait_for_local_http()' "$COMMON"
grep -q '_mfa_sidecar_assert_service_active()' "$COMMON"
grep -q 'journalctl -u "\$service" -n 80 --no-pager' "$COMMON"
grep -q 'urllib.request.urlopen' "$COMMON"
grep -q 'expected_status' "$COMMON"
grep -q 'urllib.error.HTTPError' "$COMMON"

grep -q '_mfa_sidecar_assert_service_active mfa-sidecar-authelia' "$INSTALL_SCRIPT"
grep -q '_mfa_sidecar_assert_service_active mfa-sidecar-admin' "$INSTALL_SCRIPT"
grep -q '127.0.0.1:9087/admin' "$INSTALL_SCRIPT"
grep -q '200; then' "$INSTALL_SCRIPT"
grep -q 'mkdir -p "/etc/nginx/conf.d/\${domain}.d"' "$INSTALL_SCRIPT"

grep -q '_mfa_sidecar_assert_service_active mfa-sidecar-authelia' "$UPGRADE_SCRIPT"
grep -q '_mfa_sidecar_assert_service_active mfa-sidecar-admin' "$UPGRADE_SCRIPT"
grep -q '127.0.0.1:9087/admin after upgrade' "$UPGRADE_SCRIPT"
grep -q '200; then' "$UPGRADE_SCRIPT"
grep -q 'mkdir -p "/etc/nginx/conf.d/\${domain}.d"' "$UPGRADE_SCRIPT"

grep -q '_mfa_sidecar_assert_service_active mfa-sidecar-authelia' "$RESTORE_SCRIPT"
grep -q '_mfa_sidecar_assert_service_active mfa-sidecar-admin' "$RESTORE_SCRIPT"
grep -q '127.0.0.1:9087/admin after restore' "$RESTORE_SCRIPT"
grep -q '200; then' "$RESTORE_SCRIPT"
grep -q 'mkdir -p "/etc/nginx/conf.d/\${domain}.d"' "$RESTORE_SCRIPT"

echo "smoke_install_runtime_guards: ok"
