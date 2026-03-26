#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
CONFIG_SCRIPT="$ROOT_DIR/package-base/scripts/config"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"
UPGRADE_SCRIPT="$ROOT_DIR/package-base/scripts/upgrade"
RESTORE_SCRIPT="$ROOT_DIR/package-base/scripts/restore"
BACKUP_SCRIPT="$ROOT_DIR/package-base/scripts/backup"
REMOVE_SCRIPT="$ROOT_DIR/package-base/scripts/remove"

# Common resolver exists and explicitly rejects unresolved app placeholders.
grep -q '^_mfa_sidecar_resolve_paths() {' "$COMMON"
grep -Fq "*'\$app'*" "$COMMON"
grep -Fq "*'__APP__'*" "$COMMON"
grep -Fq 'resolved_install_dir="/opt/yunohost/${app}"' "$COMMON"
grep -Fq 'resolved_data_dir="/var/lib/${app}"' "$COMMON"

# Lifecycle scripts must normalize paths before touching install/data trees.
grep -q '^_mfa_sidecar_resolve_paths$' "$INSTALL_SCRIPT"
grep -q '^_mfa_sidecar_resolve_paths$' "$UPGRADE_SCRIPT"
grep -q '^_mfa_sidecar_resolve_paths$' "$RESTORE_SCRIPT"
grep -q '^_mfa_sidecar_resolve_paths$' "$BACKUP_SCRIPT"
grep -q '^_mfa_sidecar_resolve_paths$' "$REMOVE_SCRIPT"

# Config script must also normalize unresolved values and refuse literal $app leakage.
grep -Fq 'APP_INSTALL_DIR="${install_dir:-}"' "$CONFIG_SCRIPT"
grep -Fq 'APP_DATA_DIR="${data_dir:-}"' "$CONFIG_SCRIPT"
grep -Fq 'APP_INSTALL_DIR="/opt/yunohost/${app}"' "$CONFIG_SCRIPT"
grep -Fq 'APP_DATA_DIR="/var/lib/${app}"' "$CONFIG_SCRIPT"

echo "smoke_path_resolution: ok"
