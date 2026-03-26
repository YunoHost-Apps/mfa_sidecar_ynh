#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PANEL="$ROOT_DIR/package-base/config_panel.toml"
CONFIG_SCRIPT="$ROOT_DIR/package-base/scripts/config"
HELPER="$ROOT_DIR/package-base/sources/manage_authelia_users.py"

# Config surface should expose user sync.
grep -q '\[main.operations.sync_users_from_yunohost\]' "$CONFIG_PANEL"
grep -q '^run__sync_users_from_yunohost() {' "$CONFIG_SCRIPT"
grep -q 'sync-from-yunohost' "$CONFIG_SCRIPT"

# Helper should implement managed disable-on-removal sync behavior.
grep -q 'managed_by_mfa_sidecar_sync' "$HELPER"
grep -q 'sync-from-yunohost' "$HELPER"
grep -q 'user\["disabled"\] = True' "$HELPER"

echo "smoke_user_sync_config_contract: ok"
