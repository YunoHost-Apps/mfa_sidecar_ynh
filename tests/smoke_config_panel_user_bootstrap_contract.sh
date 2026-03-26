#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PANEL="$ROOT_DIR/package-base/config_panel.toml"
CONFIG_SCRIPT="$ROOT_DIR/package-base/scripts/config"
RESTORE_SCRIPT="$ROOT_DIR/package-base/scripts/restore"
UPGRADE_SCRIPT="$ROOT_DIR/package-base/scripts/upgrade"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"

# Package lifecycle should ship the management helper consistently.
grep -q 'manage_authelia_users.py' "$INSTALL_SCRIPT"
grep -q 'manage_authelia_users.py' "$UPGRADE_SCRIPT"
grep -q 'manage_authelia_users.py' "$RESTORE_SCRIPT"

# Config panel should expose first-user bootstrap controls.
grep -q '\[main.operations.show_users_file\]' "$CONFIG_PANEL"
grep -q '\[main.operations.seed_first_user\]' "$CONFIG_PANEL"
grep -q '\[main.operations.first_username\]' "$CONFIG_PANEL"
grep -q '\[main.operations.first_password\]' "$CONFIG_PANEL"

# Config script should implement those actions.
grep -q '^run__show_users_file() {' "$CONFIG_SCRIPT"
grep -q '^run__seed_first_user() {' "$CONFIG_SCRIPT"
grep -q 'manage_authelia_users.py" ensure-user' "$CONFIG_SCRIPT"

echo "smoke_config_panel_user_bootstrap_contract: ok"
