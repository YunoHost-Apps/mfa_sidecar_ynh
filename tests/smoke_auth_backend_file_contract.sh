#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
MANIFEST="$ROOT_DIR/package-base/manifest.toml"
RENDERER="$ROOT_DIR/package-base/sources/render_alpha_config.py"
EXAMPLE="$ROOT_DIR/configs/domain-policy.example.yaml"

# Package should not expose the old LDAP bind-password install question.
! grep -q '\[install\.ldap_bind_password\]' "$MANIFEST"
! grep -q 'ldap-utils' "$MANIFEST"

# Runtime env should not export LDAP bind password anymore.
! grep -q 'AUTHELIA_LDAP_PASSWORD' "$COMMON"

# Seeded/example policy should use a file-backed local identity store.
grep -q 'local:' "$COMMON"
grep -q 'path: /etc/mfa-sidecar/authelia/users.yml' "$COMMON"
grep -q 'source: yunohost-ldap-readonly' "$COMMON"
grep -q 'local:' "$EXAMPLE"

# Renderer should target the file auth backend.
grep -q '"authentication_backend": build_authentication_backend(policy)' "$RENDERER"
grep -q '"file": {' "$RENDERER"
! grep -q '"ldap": ldap_backend' "$RENDERER"

echo "smoke_auth_backend_file_contract: ok"
