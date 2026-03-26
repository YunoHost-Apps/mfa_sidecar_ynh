#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$ROOT_DIR/package-base/scripts/_common.sh"
OUT_DIR="$ROOT_DIR/tests/out/alpha-notes-contract"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/install"

source "$COMMON"

app="mfa_sidecar"
domain="auth.example.tld"
default_policy="open"
session_duration="168h"
upstream_scheme="https"
upstream_host="127.0.0.1"
upstream_port="443"
install_dir="$OUT_DIR/install"

_mfa_sidecar_write_alpha_notes

test -f "$OUT_DIR/install/README.alpha"
grep -Fq '/etc/mfa-sidecar/secrets/ldap_bind_password' "$OUT_DIR/install/README.alpha"
grep -Fq 'when you need `/admin` access during alpha validation' "$OUT_DIR/install/README.alpha"
grep -Fq 'the admin control plane (`/admin`)' "$OUT_DIR/install/README.alpha"

echo "smoke_alpha_notes_contract: ok"
