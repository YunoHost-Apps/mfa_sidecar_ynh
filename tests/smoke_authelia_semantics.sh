#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/authelia-semantics"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/with-rule" "$OUT_DIR/empty"

cat > "$OUT_DIR/with-rule/policy.yaml" <<'EOF'
version: 1
portal:
  domain: auth.example.tld
  path: /
  default_redirect_url: https://auth.example.tld/
  listen:
    host: 127.0.0.1
    port: 9091
session:
  name: mfa_sidecar_session
  secret_file: /etc/mfa-sidecar/secrets/session_secret
  expiration: 24h
  inactivity: 1h
  remember_me: 24h
storage:
  encryption_key_file: /etc/mfa-sidecar/secrets/storage_encryption_key
identity:
  display_name: MFA Sidecar
  local:
    path: /etc/mfa-sidecar/authelia/users.yml
    watch: false
    search:
      email: true
      case_insensitive: true
    password:
      algorithm: argon2
      argon2:
        variant: argon2id
        iterations: 3
        memory: 65536
        parallelism: 4
        key_length: 32
        salt_length: 16
  sync:
    enabled: false
    source: yunohost-ldap-readonly
    fields:
      - username
      - email
mfa:
  issuer: MFA Sidecar
  webauthn:
    enabled: true
    display_name: MFA Sidecar
    attestation_conveyance_preference: indirect
    user_verification: preferred
    timeout: 60s
  totp:
    enabled: true
    issuer: MFA Sidecar
access_control:
  default_policy: open
  managed_sites:
    - id: protected_site
      host: wm3v.com
      path: /
      enabled: true
      upstream: https://127.0.0.1:443
recovery:
  mode: authelia-reset-password-and-enrollment
  disable_reset: false
alpha:
  generate_nginx_snippets: true
  generate_authelia_config: true
  enforce_tls_upstream_verification: false
EOF

cat > "$OUT_DIR/empty/policy.yaml" <<'EOF'
version: 1
portal:
  domain: auth.example.tld
  path: /
  default_redirect_url: https://auth.example.tld/
  listen:
    host: 127.0.0.1
    port: 9091
session:
  name: mfa_sidecar_session
  secret_file: /etc/mfa-sidecar/secrets/session_secret
  expiration: 24h
  inactivity: 1h
  remember_me: 24h
storage:
  encryption_key_file: /etc/mfa-sidecar/secrets/storage_encryption_key
identity:
  display_name: MFA Sidecar
  local:
    path: /etc/mfa-sidecar/authelia/users.yml
    watch: false
    search:
      email: true
      case_insensitive: true
    password:
      algorithm: argon2
      argon2:
        variant: argon2id
        iterations: 3
        memory: 65536
        parallelism: 4
        key_length: 32
        salt_length: 16
  sync:
    enabled: false
    source: yunohost-ldap-readonly
    fields:
      - username
      - email
mfa:
  issuer: MFA Sidecar
  webauthn:
    enabled: true
    display_name: MFA Sidecar
    attestation_conveyance_preference: indirect
    user_verification: preferred
    timeout: 60s
  totp:
    enabled: true
    issuer: MFA Sidecar
access_control:
  default_policy: open
  managed_sites: []
recovery:
  mode: authelia-reset-password-and-enrollment
  disable_reset: false
alpha:
  generate_nginx_snippets: true
  generate_authelia_config: true
  enforce_tls_upstream_verification: false
EOF

python3 "$ROOT_DIR/package-base/sources/render_alpha_config.py" "$OUT_DIR/with-rule/policy.yaml" "$OUT_DIR/with-rule/rendered"
python3 "$ROOT_DIR/package-base/sources/render_alpha_config.py" "$OUT_DIR/empty/policy.yaml" "$OUT_DIR/empty/rendered"

WITH_RULE="$OUT_DIR/with-rule/rendered/authelia-config.generated.yml"
EMPTY="$OUT_DIR/empty/rendered/authelia-config.generated.yml"

test -f "$WITH_RULE"
test -f "$EMPTY"

grep -q 'default_policy: bypass' "$WITH_RULE"
grep -q 'policy: two_factor' "$WITH_RULE"
grep -q 'authentication_backend:' "$WITH_RULE"
grep -q 'file:' "$WITH_RULE"
! grep -q 'default_policy: open' "$WITH_RULE"
! grep -q 'default_redirection_url:' "$WITH_RULE"
! grep -q 'ldap:' "$WITH_RULE"

grep -q 'default_policy: one_factor' "$EMPTY"
grep -q 'rules: \[\]' "$EMPTY"
grep -q 'authentication_backend:' "$EMPTY"
grep -q 'file:' "$EMPTY"
! grep -q 'default_policy: bypass' "$EMPTY"
! grep -q 'default_policy: open' "$EMPTY"
! grep -q 'default_redirection_url:' "$EMPTY"
! grep -q 'ldap:' "$EMPTY"

echo "smoke_authelia_semantics: ok"
