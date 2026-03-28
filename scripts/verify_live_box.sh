#!/bin/bash
set -euo pipefail

APP="mfa_sidecar"
INSTALL_DIR="/opt/yunohost/mfa_sidecar"
POLICY_FILE="$INSTALL_DIR/config/domain-policy.yaml"
GENERATED_DIR="$INSTALL_DIR/deploy/generated-runtime"
RUNTIME_DIR="/etc/mfa-sidecar"

say() {
  printf '\n== %s ==\n' "$1"
}

say "services"
systemctl status nginx mfa-sidecar-admin mfa-sidecar-authelia --no-pager || true

say "policy enforcement"
grep -n 'enforcement_enabled\|default_policy\|host:\|path:\|enabled:' "$POLICY_FILE" || true

say "generated runtime index"
cat "$GENERATED_DIR/render-index.json" || true

say "generated protected snippets"
find "$GENERATED_DIR/nginx" -maxdepth 1 -type f -print | sort || true
find "$RUNTIME_DIR/nginx/protected" -maxdepth 1 -type f -print | sort || true

say "auth-request snippet sanity"
for f in "$RUNTIME_DIR"/nginx/protected/*.conf; do
  [ -f "$f" ] || continue
  echo "--- $f ---"
  sed -n '1,40p' "$f"
  break
done

say "authelia mfa config"
grep -A20 '^totp:\|^webauthn:' "$RUNTIME_DIR/authelia/configuration.yml" || true

say "notes"
echo "Use this checklist before public submission or after risky upgrades:"
echo "- confirm services are healthy"
echo "- confirm protected snippets exist"
echo "- confirm auth-request snippet includes SSOwat bypass + required Authelia headers"
echo "- confirm enforcement_enabled reflects intended state"
echo "- manually test one protected target in an incognito window"
