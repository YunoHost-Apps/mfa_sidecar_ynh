#!/bin/bash

_mfa_sidecar_validate_inputs() {
    if [[ "$path" != "/" ]]; then
        ynh_die "Portal app must be installed at '/' on its own dedicated domain."
    fi

    if [[ ! "$portal_subdomain" =~ ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$ ]]; then
        ynh_die "portal_subdomain must be a simple DNS label (letters, numbers, dashes)."
    fi

    if [[ ! "$default_policy" =~ ^(open|protected)$ ]]; then
        ynh_die "default_policy must be 'open' or 'protected'."
    fi

    if [[ ! "$session_duration" =~ ^(8h|24h|168h|336h|720h)$ ]]; then
        ynh_die "session_duration must be one of: 8h, 24h, 168h, 336h, 720h."
    fi

    if [[ ! "$upstream_scheme" =~ ^(http|https)$ ]]; then
        ynh_die "upstream_scheme must be http or https."
    fi

    if [[ -z "$upstream_host" ]]; then
        ynh_die "upstream_host cannot be empty."
    fi

    if ! [[ "$upstream_port" =~ ^[0-9]+$ ]] || (( upstream_port < 1 || upstream_port > 65535 )); then
        ynh_die "upstream_port must be a valid TCP port."
    fi
}

_mfa_sidecar_session_remember_me() {
    case "$session_duration" in
        8h) echo "8h" ;;
        24h) echo "24h" ;;
        168h) echo "168h" ;;
        336h) echo "336h" ;;
        720h) echo "720h" ;;
        *) ynh_die "unsupported session_duration: $session_duration" ;;
    esac
}

_mfa_sidecar_install_layout() {
    mkdir -p \
        "$install_dir/config" \
        "$install_dir/bin" \
        "$install_dir/deploy/generated-alpha" \
        "$install_dir/cache/authelia" \
        "$install_dir/sources/vendor" \
        "$data_dir" \
        "/etc/mfa-sidecar/authelia" \
        "/etc/mfa-sidecar/nginx/protected" \
        "/etc/mfa-sidecar/secrets"
}

_mfa_sidecar_secret_file() {
    local name="$1"
    echo "/etc/mfa-sidecar/secrets/${name}"
}

_mfa_sidecar_write_secret_if_missing() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        umask 077
        openssl rand -hex 32 > "$path"
    fi
}

_mfa_sidecar_write_env_file() {
    local admin_gate_secret_file
    local ldap_password_file
    admin_gate_secret_file="$(_mfa_sidecar_secret_file admin_gate_secret)"
    ldap_password_file="$(_mfa_sidecar_secret_file ldap_bind_password)"
    _mfa_sidecar_write_secret_if_missing "$admin_gate_secret_file"

    if [[ ! -f "$ldap_password_file" ]]; then
        umask 077
        printf '%s\n' 'CHANGEME_LDAP_BIND_PASSWORD' > "$ldap_password_file"
    fi

    cat > /etc/mfa-sidecar/mfa-sidecar.env <<EOF
AUTHELIA_SESSION_SECRET=$(cat "$(_mfa_sidecar_secret_file session_secret)")
AUTHELIA_STORAGE_ENCRYPTION_KEY=$(cat "$(_mfa_sidecar_secret_file storage_encryption_key)")
AUTHELIA_IDENTITY_VALIDATION_RESET_SECRET=$(cat "$(_mfa_sidecar_secret_file identity_validation_reset_secret)")
AUTHELIA_LDAP_PASSWORD=$(cat "$ldap_password_file")
MFA_SIDECAR_ADMIN_GATE_SECRET=$(cat "$admin_gate_secret_file")
EOF
    chmod 600 /etc/mfa-sidecar/mfa-sidecar.env
}

_mfa_sidecar_ldap_password_is_placeholder() {
    [[ "$(cat "$(_mfa_sidecar_secret_file ldap_bind_password)" 2>/dev/null || true)" == 'CHANGEME_LDAP_BIND_PASSWORD' ]]
}

_mfa_sidecar_install_authelia_binary() {
    python3 "$install_dir/bin/install_authelia_from_vendor.py" \
        "$install_dir/sources/authelia-release.json" \
        "$install_dir/sources/vendor" \
        "$install_dir/cache/authelia" > "$install_dir/cache/authelia/install-result.json"

    install -D -m 755 "$install_dir/cache/authelia/authelia" /usr/local/bin/authelia
}

_mfa_sidecar_write_policy_seed() {
    local remember_me
    remember_me="$(_mfa_sidecar_session_remember_me)"

    cat > "$install_dir/config/domain-policy.yaml" <<EOF
version: 1
portal:
  domain: ${domain}
  path: /
  default_redirect_url: https://${domain}/
  listen:
    host: 127.0.0.1
    port: 9091
session:
  name: mfa_sidecar_session
  secret_file: $(_mfa_sidecar_secret_file session_secret)
  expiration: ${remember_me}
  inactivity: 1h
  remember_me: ${remember_me}
storage:
  encryption_key_file: $(_mfa_sidecar_secret_file storage_encryption_key)
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
    display_name: MFA Sidecar
    attestation_conveyance_preference: indirect
    user_verification: preferred
    timeout: 60s
  totp:
    enabled: true
    issuer: MFA Sidecar
access_control:
  default_policy: bypass
  managed_sites: []
recovery:
  mode: authelia-reset-password-and-enrollment
  disable_reset: false
alpha:
  generate_nginx_snippets: true
  generate_authelia_config: true
  enforce_tls_upstream_verification: false
EOF
}

_mfa_sidecar_sync_runtime_assets() {
    python3 "$install_dir/bin/render_alpha_config.py" \
        "$install_dir/config/domain-policy.yaml" \
        "$install_dir/deploy/generated-alpha"

    python3 "$install_dir/bin/stage_alpha_runtime.py" \
        "$install_dir/deploy/generated-alpha" /
}

_mfa_sidecar_wait_for_local_http() {
    local url="$1"
    local attempts="${2:-20}"
    local sleep_seconds="${3:-1}"
    local i

    for ((i=1; i<=attempts; i++)); do
        if python3 - "$url" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=2) as response:
    if response.status < 500:
        raise SystemExit(0)
raise SystemExit(1)
PY
        then
            return 0
        fi
        sleep "$sleep_seconds"
    done
    return 1
}

_mfa_sidecar_assert_service_active() {
    local service="$1"
    if ! systemctl is-active --quiet "$service"; then
        journalctl -u "$service" -n 80 --no-pager >&2 || true
        ynh_die "Service failed to start: $service"
    fi
}

_mfa_sidecar_inject_primary_domain_include() {
    local target_conf="/etc/nginx/conf.d/${domain}.d/${app}.conf"
    local include_path="/etc/mfa-sidecar/nginx/protected/portal_root_seed.conf"

    if [[ -f "$target_conf" && -f "$include_path" ]]; then
        python3 "$install_dir/bin/inject_protected_include.py" inject "$target_conf" "$include_path"
    fi
}

_mfa_sidecar_remove_primary_domain_include() {
    local target_conf="/etc/nginx/conf.d/${domain}.d/${app}.conf"
    if [[ -f "$target_conf" ]]; then
        python3 "$install_dir/bin/inject_protected_include.py" remove "$target_conf"
    fi
}

_mfa_sidecar_write_alpha_notes() {
    cat > "$install_dir/README.alpha" <<EOF
MFA Sidecar alpha package
=========================

This alpha package seeds a managed-sites policy file, installs a vendored pinned
Authelia release, generates Authelia/nginx runtime artifacts, and stages them
into live runtime paths.

Current install choices:
- portal domain: ${domain}
- portal path: /
- default initial rule state: ${default_policy}
- remembered session: ${session_duration}
- default upstream seed: ${upstream_scheme}://${upstream_host}:${upstream_port}

Generated/staged paths:
- policy seed: $install_dir/config/domain-policy.yaml
- generated artifacts: $install_dir/deploy/generated-alpha/
- authelia config: /etc/mfa-sidecar/authelia/configuration.yml
- nginx portal include: /etc/mfa-sidecar/nginx/portal.conf
- nginx protected includes: /etc/mfa-sidecar/nginx/protected/*.conf
- env file: /etc/mfa-sidecar/mfa-sidecar.env
- vendored authelia source: $install_dir/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz
- installed authelia binary: /usr/local/bin/authelia

Current beta-shaped improvements:
- dedicated portal domain enforced
- managed host+path entries with longest-match-wins semantics
- vendored pinned Authelia artifact with sha256 verification
- host-aligned LDAP defaults for wm3v-style YunoHost LDAP

Remaining operator tasks:
- replace the placeholder LDAP bind password in /etc/mfa-sidecar/secrets/ldap_bind_password, then rerun `yunohost app upgrade mfa_sidecar --debug` or restart sidecar services
- retrieve the generated MFA_SIDECAR_ADMIN_GATE_SECRET from /etc/mfa-sidecar/mfa-sidecar.env to access /admin during alpha validation
- validate live auth flow after install
- add and tune managed site entries from the admin control plane
EOF
}
