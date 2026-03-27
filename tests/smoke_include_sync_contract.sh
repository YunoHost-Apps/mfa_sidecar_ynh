#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
CONFIG_SCRIPT="$ROOT_DIR/package-base/scripts/config"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"
UPGRADE_SCRIPT="$ROOT_DIR/package-base/scripts/upgrade"
REMOVE_SCRIPT="$ROOT_DIR/package-base/scripts/remove"

grep -q '^_mfa_sidecar_sync_protected_domain_includes() {' "$COMMON"
grep -q '^_mfa_sidecar_remove_protected_domain_includes() {' "$COMMON"
grep -q 'mfa-sidecar-' "$COMMON"
grep -q '_mfa_sidecar_sync_protected_domain_includes' "$CONFIG_SCRIPT"
grep -q '_mfa_sidecar_remove_protected_domain_includes' "$CONFIG_SCRIPT"
grep -q '_mfa_sidecar_sync_protected_domain_includes' "$INSTALL_SCRIPT"
grep -q '_mfa_sidecar_sync_protected_domain_includes' "$UPGRADE_SCRIPT"
grep -q '_mfa_sidecar_remove_protected_domain_includes' "$REMOVE_SCRIPT"

echo "smoke_include_sync_contract: ok"
