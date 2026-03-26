#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
MANIFEST="$ROOT_DIR/package-base/manifest.toml"

# No placeholder fallback should remain.
! grep -q 'CHANGEME_LDAP_BIND_PASSWORD' "$COMMON"

# Blank install input should auto-generate via the generic secret helper.
grep -q 'ldap_password_file="\$(_mfa_sidecar_secret_file ldap_bind_password)"' "$COMMON"
grep -q '_mfa_sidecar_write_secret_if_missing "\$ldap_password_file"' "$COMMON"

# Manifest should describe blank-as-auto-generate behavior, not manual surgery as the default.
grep -q 'generate a strong local secret automatically' "$MANIFEST"
! grep -q 'Leave blank only if you will set' "$MANIFEST"

echo "smoke_ldap_secret_handling: ok"
