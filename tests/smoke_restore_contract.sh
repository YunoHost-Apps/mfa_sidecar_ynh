#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESTORE="$ROOT_DIR/package-base/scripts/restore"

grep -q 'mfa-sidecar-authelia' "$RESTORE"
grep -q 'mfa-sidecar-admin' "$RESTORE"
grep -q '_mfa_sidecar_sync_protected_domain_includes' "$RESTORE"

echo "smoke_restore_contract: ok"
