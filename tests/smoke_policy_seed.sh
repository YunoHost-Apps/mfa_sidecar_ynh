#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"

grep -q '^access_control:$' "$COMMON"
grep -q '^  managed_sites: \[\]$' "$COMMON"
! grep -q 'portal_root_seed' "$COMMON"
grep -q 'MFA_SIDECAR_ADMIN_GATE_SECRET' "$COMMON"

echo "smoke_policy_seed: ok"
