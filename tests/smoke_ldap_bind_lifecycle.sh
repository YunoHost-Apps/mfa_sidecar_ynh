#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
INSTALL="$ROOT_DIR/package-base/scripts/install"
UPGRADE="$ROOT_DIR/package-base/scripts/upgrade"
REMOVE="$ROOT_DIR/package-base/scripts/remove"
RESTORE="$ROOT_DIR/package-base/scripts/restore"
MANIFEST="$ROOT_DIR/package-base/manifest.toml"
LDAP_NOTES="$ROOT_DIR/docs/LDAP-NOTES.md"

# LDAP lifecycle helpers must exist.
grep -q '^_mfa_sidecar_ldap_bind_dn() {' "$COMMON"
grep -q '^_mfa_sidecar_ensure_ldap_bind_account() {' "$COMMON"
grep -q '^_mfa_sidecar_remove_ldap_bind_account() {' "$COMMON"

# Lifecycle hooks must reconcile/remove the account.
grep -q '_mfa_sidecar_ensure_ldap_bind_account' "$INSTALL"
grep -q '_mfa_sidecar_ensure_ldap_bind_account' "$UPGRADE"
grep -q '_mfa_sidecar_ensure_ldap_bind_account' "$RESTORE"
grep -q '_mfa_sidecar_remove_ldap_bind_account' "$REMOVE"

# Package must declare the LDAP client utilities it now depends on.
grep -q 'ldap-utils' "$MANIFEST"

# Docs should mention the managed account model.
grep -q 'managed service bind account' "$LDAP_NOTES"

echo "smoke_ldap_bind_lifecycle: ok"
