#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )/.." && pwd)"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
BOOTSTRAP="$ROOT_DIR/package-base/sources/bootstrap_authelia_users.py"
FIRST_BOOT="$ROOT_DIR/docs/OPERATOR-FIRST-BOOT.md"
CONFIG_PANEL="$ROOT_DIR/package-base/config_panel.toml"
CONFIG_SCRIPT="$ROOT_DIR/package-base/scripts/config"

# Install should ship and use the bootstrap helper.
grep -q 'bootstrap_authelia_users.py' "$INSTALL_SCRIPT"
grep -q '_mfa_sidecar_ensure_users_file_template' "$INSTALL_SCRIPT"
grep -q '^_mfa_sidecar_ensure_users_file_template() {' "$COMMON"

# Bootstrap helper should create a disabled but syntactically valid placeholder user.
grep -q 'admin-bootstrap' "$BOOTSTRAP"
grep -q 'disabled": True' "$BOOTSTRAP"
grep -q '\$argon2id\$v=19' "$BOOTSTRAP"
grep -q "'admins'" "$BOOTSTRAP" || grep -q '"admins"' "$BOOTSTRAP"

# Operator docs/panel should point to the users file reality.
grep -q '/etc/mfa-sidecar/authelia/users.yml' "$FIRST_BOOT"
grep -q 'authelia crypto hash generate argon2' "$FIRST_BOOT"
grep -q 'users file' "$CONFIG_PANEL"
grep -q 'Users file:' "$CONFIG_SCRIPT"

echo "smoke_users_bootstrap_contract: ok"
