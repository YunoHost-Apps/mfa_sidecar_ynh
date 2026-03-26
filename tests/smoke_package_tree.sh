#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tests/out/package-tree"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/install_dir/bin" "$OUT_DIR/install_dir/config" "$OUT_DIR/install_dir/deploy/generated-alpha"
mkdir -p "$OUT_DIR/etc/mfa-sidecar/authelia" "$OUT_DIR/etc/mfa-sidecar/nginx/protected" "$OUT_DIR/etc/mfa-sidecar/secrets"

cp "$ROOT_DIR/package-base/sources/render_alpha_config.py" "$OUT_DIR/install_dir/bin/render_alpha_config.py"
cp "$ROOT_DIR/package-base/sources/stage_alpha_runtime.py" "$OUT_DIR/install_dir/bin/stage_alpha_runtime.py"
cp "$ROOT_DIR/package-base/sources/inject_protected_include.py" "$OUT_DIR/install_dir/bin/inject_protected_include.py"
cp "$ROOT_DIR/package-base/sources/install_authelia_from_vendor.py" "$OUT_DIR/install_dir/bin/install_authelia_from_vendor.py"
cp "$ROOT_DIR/package-base/sources/admin_ui_app.py" "$OUT_DIR/install_dir/bin/admin_ui_app.py"
cp "$ROOT_DIR/package-base/sources/policy_admin.py" "$OUT_DIR/install_dir/bin/policy_admin.py"
cp "$ROOT_DIR/package-base/sources/discovery.py" "$OUT_DIR/install_dir/bin/discovery.py"
cp "$ROOT_DIR/package-base/sources/authelia-release.json" "$OUT_DIR/install_dir/authelia-release.json"
mkdir -p "$OUT_DIR/install_dir/vendor"
cp "$ROOT_DIR/package-base/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz" "$OUT_DIR/install_dir/vendor/"

cat > "$OUT_DIR/install_dir/config/domain-policy.yaml" <<'EOF'
version: 1
portal:
  domain: auth.example.tld
  path: /
  default_redirect_url: https://yunohost.example.tld/
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
  display_name: YunoHost LDAP
  ldap:
    address: ldap://127.0.0.1:389
    implementation: custom
    start_tls: false
    permit_referrals: false
    permit_unauthenticated_bind: false
    base_dn: dc=yunohost,dc=org
    additional_users_dn: ou=users
    additional_groups_dn: ou=groups
    users_filter: (&({username_attribute}={input})(objectClass=inetOrgPerson))
    groups_filter: (&(member={dn})(objectClass=groupOfNamesYnh))
    group_search_mode: filter
    username_attribute: uid
    display_name_attribute: cn
    mail_attribute: mail
    user: uid=authelia,ou=users,dc=yunohost,dc=org
    password_env: AUTHELIA_LDAP_PASSWORD
mfa:
  issuer: MFA Sidecar
  webauthn:
    enabled: true
    display_name: YunoHost MFA
    attestation_conveyance_preference: indirect
    user_verification: preferred
    timeout: 60s
  totp:
    enabled: true
    issuer: MFA Sidecar
access_control:
  default_policy: bypass
  managed_sites:
    - id: root_site
      host: wm3v.com
      path: /
      enabled: true
      upstream: https://127.0.0.1:8443
    - id: nextcloud_exception
      host: wm3v.com
      path: /nextcloud
      enabled: false
      upstream: https://127.0.0.1:8443
recovery:
  mode: authelia-reset-password-and-enrollment
  disable_reset: false
alpha:
  generate_nginx_snippets: true
  generate_authelia_config: true
  enforce_tls_upstream_verification: false
EOF

python3 "$OUT_DIR/install_dir/bin/render_alpha_config.py" \
  "$OUT_DIR/install_dir/config/domain-policy.yaml" \
  "$OUT_DIR/install_dir/deploy/generated-alpha"
python3 "$OUT_DIR/install_dir/bin/stage_alpha_runtime.py" \
  "$OUT_DIR/install_dir/deploy/generated-alpha" \
  "$OUT_DIR"

test -f "$OUT_DIR/install_dir/bin/admin_ui_app.py"
test -f "$OUT_DIR/install_dir/bin/policy_admin.py"
test -f "$OUT_DIR/install_dir/bin/discovery.py"
test -f "$OUT_DIR/etc/mfa-sidecar/authelia/configuration.yml"
test -f "$OUT_DIR/etc/mfa-sidecar/nginx/portal.conf"
test -f "$OUT_DIR/etc/mfa-sidecar/nginx/protected/root_site.conf"
test -f "$OUT_DIR/etc/mfa-sidecar/nginx/protected/nextcloud_exception.conf"

echo "smoke_package_tree: ok"
