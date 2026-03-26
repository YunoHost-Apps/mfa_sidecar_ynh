#!/bin/bash

_mfa_sidecar_resolve_paths() {
    local resolved_install_dir resolved_data_dir

    resolved_install_dir="${install_dir:-}"
    resolved_data_dir="${data_dir:-}"

    if [[ -z "$resolved_install_dir" || "$resolved_install_dir" == *'$app'* || "$resolved_install_dir" == *'__APP__'* ]]; then
        resolved_install_dir="$(ynh_app_setting_get --key=install_dir 2>/dev/null || true)"
    fi
    if [[ -z "$resolved_data_dir" || "$resolved_data_dir" == *'$app'* || "$resolved_data_dir" == *'__APP__'* ]]; then
        resolved_data_dir="$(ynh_app_setting_get --key=data_dir 2>/dev/null || true)"
    fi

    if [[ -z "$resolved_install_dir" || "$resolved_install_dir" == *'$app'* || "$resolved_install_dir" == *'__APP__'* ]]; then
        resolved_install_dir="/opt/yunohost/${app}"
    fi
    if [[ -z "$resolved_data_dir" || "$resolved_data_dir" == *'$app'* || "$resolved_data_dir" == *'__APP__'* ]]; then
        resolved_data_dir="/var/lib/${app}"
    fi

    install_dir="$resolved_install_dir"
    data_dir="$resolved_data_dir"
}

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
        "$install_dir/run" \
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
    admin_gate_secret_file="$(_mfa_sidecar_secret_file admin_gate_secret)"
    _mfa_sidecar_write_secret_if_missing "$admin_gate_secret_file"

    cat > /etc/mfa-sidecar/mfa-sidecar.env <<EOF
AUTHELIA_SESSION_SECRET=$(cat "$(_mfa_sidecar_secret_file session_secret)")
AUTHELIA_STORAGE_ENCRYPTION_KEY=$(cat "$(_mfa_sidecar_secret_file storage_encryption_key)")
AUTHELIA_IDENTITY_VALIDATION_RESET_SECRET=$(cat "$(_mfa_sidecar_secret_file identity_validation_reset_secret)")
MFA_SIDECAR_ADMIN_GATE_SECRET=$(cat "$admin_gate_secret_file")
MFA_SIDECAR_RUNTIME_DIR=$install_dir/run
EOF
    chmod 640 /etc/mfa-sidecar/mfa-sidecar.env
}

_mfa_sidecar_authelia_bin() {
    echo "$install_dir/bin/authelia"
}

_mfa_sidecar_install_authelia_binary() {
    python3 "$install_dir/bin/install_authelia_from_vendor.py" \
        "$install_dir/sources/authelia-release.json" \
        "$install_dir/sources/vendor" \
        "$install_dir/cache/authelia" > "$install_dir/cache/authelia/install-result.json"

    install -D -m 755 "$install_dir/cache/authelia/authelia" "$(_mfa_sidecar_authelia_bin)"
}

_mfa_sidecar_users_file() {
    echo "/etc/mfa-sidecar/authelia/users.yml"
}

_mfa_sidecar_ensure_users_file_template() {
    local users_file
    users_file="$(_mfa_sidecar_users_file)"
    if [[ ! -f "$users_file" ]]; then
        python3 "$install_dir/bin/bootstrap_authelia_users.py" "$users_file"
    fi
}

_mfa_sidecar_write_policy_seed() {
    local remember_me
    local seeded_default_policy

    remember_me="$(_mfa_sidecar_session_remember_me)"
    seeded_default_policy="${default_policy:-open}"

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
  default_policy: ${seeded_default_policy}
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
    local header_name="${4:-}"
    local header_value="${5:-}"
    local i

    for ((i=1; i<=attempts; i++)); do
        if python3 - "$url" "$header_name" "$header_value" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

url = sys.argv[1]
header_name = sys.argv[2]
header_value = sys.argv[3]
request = urllib.request.Request(url)
if header_name and header_value:
    request.add_header(header_name, header_value)
with urllib.request.urlopen(request, timeout=2) as response:
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

_mfa_sidecar_dump_admin_diagnostics() {
    systemctl status mfa-sidecar-admin --no-pager >&2 || true
    journalctl -u mfa-sidecar-admin --since '-2 minutes' --no-pager >&2 || true
    ss -ltnp 2>/dev/null | grep ':9087' >&2 || true
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
    {
        printf '%s\n' 'MFA Sidecar alpha package'
        printf '%s\n' '========================='
        printf '\n'
        printf '%s\n' 'This alpha package seeds a managed-sites policy file, installs a vendored pinned'
        printf '%s\n' 'Authelia release, generates Authelia/nginx runtime artifacts, and stages them'
        printf '%s\n' 'into live runtime paths.'
        printf '\n'
        printf '%s\n' 'Current install choices:'
        printf '%s\n' "- portal domain: ${domain}"
        printf '%s\n' '- portal path: /'
        printf '%s\n' "- default initial rule state: ${default_policy}"
        printf '%s\n' "- remembered session: ${session_duration}"
        printf '%s\n' "- default upstream seed: ${upstream_scheme}://${upstream_host}:${upstream_port}"
        printf '\n'
        printf '%s\n' 'Generated/staged paths:'
        printf '%s\n' "- policy seed: $install_dir/config/domain-policy.yaml"
        printf '%s\n' "- generated artifacts: $install_dir/deploy/generated-alpha/"
        printf '%s\n' '- authelia config: /etc/mfa-sidecar/authelia/configuration.yml'
        printf '%s\n' '- nginx portal include: /etc/mfa-sidecar/nginx/portal.conf'
        printf '%s\n' '- nginx protected includes: /etc/mfa-sidecar/nginx/protected/*.conf'
        printf '%s\n' '- env file: /etc/mfa-sidecar/mfa-sidecar.env'
        printf '%s\n' "- vendored authelia source: $install_dir/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz"
        printf '%s\n' "- installed authelia binary: $install_dir/bin/authelia"
        printf '\n'
        printf '%s\n' 'Current beta-shaped improvements:'
        printf '%s\n' '- dedicated portal domain enforced'
        printf '%s\n' '- managed host+path entries with longest-match-wins semantics'
        printf '%s\n' '- vendored pinned Authelia artifact with sha256 verification'
        printf '%s\n' '- separate sidecar-owned credential/MFA store with file-backed Authelia auth model'
        printf '\n'
        printf '%s\n' 'Remaining operator tasks:'
        printf '%s\n' '- bootstrap or import the initial sidecar users file at /etc/mfa-sidecar/authelia/users.yml with hashed passwords before real auth validation'
        printf '%s\n' '- use the YunoHost config panel first for high-level settings, service actions, and admin-gate introspection'
        printf '%s\n' '- retrieve the generated MFA_SIDECAR_ADMIN_GATE_SECRET from /etc/mfa-sidecar/mfa-sidecar.env or the config-panel action when you need `/admin` access during alpha validation'
        printf '%s\n' '- validate live auth flow after install'
        printf '%s\n' '- add and tune managed site entries from the admin control plane (`/admin`) until more of that surface is moved into YunoHost-native controls'
    } > "$install_dir/README.alpha"
}
