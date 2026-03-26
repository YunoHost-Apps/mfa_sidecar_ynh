#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"
UPGRADE_SCRIPT="$ROOT_DIR/package-base/scripts/upgrade"
RESTORE_SCRIPT="$ROOT_DIR/package-base/scripts/restore"
REMOVE_SCRIPT="$ROOT_DIR/package-base/scripts/remove"

grep -q '^_mfa_sidecar_authelia_bin() {' "$COMMON"
grep -q '"$install_dir/bin/authelia"' "$COMMON"

grep -q 'chown -R "\$app:\$app" "\$install_dir" "\$data_dir"' "$INSTALL_SCRIPT"
grep -q 'chown root:"\$app" /etc/mfa-sidecar/mfa-sidecar.env' "$INSTALL_SCRIPT"
grep -q 'chmod 640 /etc/mfa-sidecar/secrets/\* /etc/mfa-sidecar/mfa-sidecar.env' "$INSTALL_SCRIPT"
grep -q 'chown "\$app:\$app" /etc/mfa-sidecar/authelia/configuration.yml' "$INSTALL_SCRIPT"
grep -q 'chmod 640 /etc/mfa-sidecar/authelia/configuration.yml' "$INSTALL_SCRIPT"

grep -q 'chown -R "\$app:\$app" "\$install_dir" "\$data_dir"' "$UPGRADE_SCRIPT"
grep -q 'chown -R "\$app:\$app" "\$install_dir" "\$data_dir"' "$RESTORE_SCRIPT"
grep -q -- '--owner "\$app"' "$COMMON"
grep -q -- '--group "\$app"' "$COMMON"
grep -q 'rm -rf "\$install_dir"' "$REMOVE_SCRIPT"

echo "smoke_least_privilege_contract: ok"
