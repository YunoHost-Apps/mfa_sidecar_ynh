#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
INSTALL_SCRIPT="$ROOT_DIR/package-base/scripts/install"
UPGRADE_SCRIPT="$ROOT_DIR/package-base/scripts/upgrade"
RESTORE_SCRIPT="$ROOT_DIR/package-base/scripts/restore"

# Local readiness probe must support authenticated checks.
grep -q 'header_name="\${4:-}"' "$COMMON"
grep -q 'header_value="\${5:-}"' "$COMMON"
grep -q 'request.add_header(header_name, header_value)' "$COMMON"
grep -q '^_mfa_sidecar_dump_admin_diagnostics() {' "$COMMON"
grep -q "journalctl -u mfa-sidecar-admin --since '-2 minutes' --no-pager" "$COMMON"
grep -q "ss -ltnp" "$COMMON"

# Lifecycle scripts must probe /admin with the admin-gate header.
grep -q 'X-MFA-Sidecar-Admin-Secret' "$INSTALL_SCRIPT"
grep -q 'X-MFA-Sidecar-Admin-Secret' "$UPGRADE_SCRIPT"
grep -q 'X-MFA-Sidecar-Admin-Secret' "$RESTORE_SCRIPT"
grep -q '_mfa_sidecar_dump_admin_diagnostics' "$INSTALL_SCRIPT"
grep -q '_mfa_sidecar_dump_admin_diagnostics' "$UPGRADE_SCRIPT"
grep -q '_mfa_sidecar_dump_admin_diagnostics' "$RESTORE_SCRIPT"

echo "smoke_admin_probe_contract: ok"
