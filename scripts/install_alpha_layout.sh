#!/usr/bin/env bash
set -euo pipefail

PREFIX="${1:-/tmp/mfa-sidecar-alpha-root}"
mkdir -p \
  "$PREFIX/etc/mfa-sidecar/authelia" \
  "$PREFIX/etc/mfa-sidecar/nginx/protected" \
  "$PREFIX/etc/mfa-sidecar/secrets" \
  "$PREFIX/var/lib/mfa_sidecar" \
  "$PREFIX/etc/systemd/system"

echo "Alpha layout created under $PREFIX"
