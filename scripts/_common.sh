#!/bin/bash

_mfa_sidecar_package_root() {
    local common_path common_dir
    common_path="${BASH_SOURCE[0]}"
    common_dir="$(cd -- "$(dirname -- "$common_path")" >/dev/null 2>&1 && pwd)"
    cd -- "$common_dir/.." >/dev/null 2>&1 && pwd
}

_mfa_sidecar_pkg_path() {
    local rel="$1"
    printf '%s/%s\n' "$(_mfa_sidecar_package_root)" "$rel"
}

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
        "$install_dir/deploy/generated-runtime" \
        "$install_dir/cache/authelia" \
        "$install_dir/sources/vendor" \
        "$install_dir/run" \
        "$install_dir/docs" \
        "$install_dir/licenses" \
        "$install_dir/www" \
        "$data_dir" \
        "/etc/mfa-sidecar/authelia" \
        "/etc/mfa-sidecar/nginx/protected" \
        "/etc/mfa-sidecar/secrets"
}

_mfa_sidecar_install_packaged_files() {
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/render_runtime_config.py)" "$install_dir/bin/render_runtime_config.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/stage_runtime.py)" "$install_dir/bin/stage_runtime.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/inject_protected_include.py)" "$install_dir/bin/inject_protected_include.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/install_authelia_from_vendor.py)" "$install_dir/bin/install_authelia_from_vendor.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/bootstrap_authelia_users.py)" "$install_dir/bin/bootstrap_authelia_users.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/manage_authelia_users.py)" "$install_dir/bin/manage_authelia_users.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/admin_ui_app.py)" "$install_dir/bin/admin_ui_app.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/policy_admin.py)" "$install_dir/bin/policy_admin.py"
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/discovery.py)" "$install_dir/bin/discovery.py"
    install -D -m 644 "$(_mfa_sidecar_pkg_path sources/authelia.service)" /etc/systemd/system/mfa-sidecar-authelia.service
    install -D -m 644 "$(_mfa_sidecar_pkg_path sources/mfa-sidecar-admin.service)" /etc/systemd/system/mfa-sidecar-admin.service
    install -D -m 644 "$(_mfa_sidecar_pkg_path sources/authelia-release.json)" "$install_dir/sources/authelia-release.json"
    install -D -m 644 "$(_mfa_sidecar_pkg_path sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz)" "$install_dir/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz"
    if [[ -f "$(_mfa_sidecar_pkg_path assets/logo.png)" ]]; then
        install -D -m 644 "$(_mfa_sidecar_pkg_path assets/logo.png)" "$install_dir/www/logo.png"
    elif [[ -f "$(_mfa_sidecar_pkg_path assets/logo.jpg)" ]]; then
        install -D -m 644 "$(_mfa_sidecar_pkg_path assets/logo.jpg)" "$install_dir/www/logo.jpg"
    fi
    install -D -m 644 "$(_mfa_sidecar_pkg_path manifest.toml)" "$install_dir/manifest.toml"
    install -D -m 644 "$(_mfa_sidecar_pkg_path README.md)" "$install_dir/README.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path LICENSE)" "$install_dir/LICENSE"
    install -D -m 644 "$(_mfa_sidecar_pkg_path THIRD_PARTY_NOTICES.md)" "$install_dir/THIRD_PARTY_NOTICES.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path licenses/Authelia-Apache-2.0.txt)" "$install_dir/licenses/Authelia-Apache-2.0.txt"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/INSTALL.md)" "$install_dir/docs/INSTALL.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/ADMIN.md)" "$install_dir/docs/ADMIN.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/USERS.md)" "$install_dir/docs/USERS.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/TROUBLESHOOTING.md)" "$install_dir/docs/TROUBLESHOOTING.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/TESTING.md)" "$install_dir/docs/TESTING.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/LIVE-BOX-VERIFICATION.md)" "$install_dir/docs/LIVE-BOX-VERIFICATION.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/SECURITY-NOTES.md)" "$install_dir/docs/SECURITY-NOTES.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/RESTORE-REMOVE.md)" "$install_dir/docs/RESTORE-REMOVE.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/SUBMISSION-NOTES.md)" "$install_dir/docs/SUBMISSION-NOTES.md"
    install -D -m 644 "$(_mfa_sidecar_pkg_path docs/RELEASE-GATES.md)" "$install_dir/docs/RELEASE-GATES.md"
    install -D -m 755 "$(_mfa_sidecar_pkg_path scripts/verify_live_box.sh)" "$install_dir/bin/verify_live_box.sh"
}


_mfa_sidecar_secret_file() {
    local name="$1"
    echo "/etc/mfa-sidecar/secrets/${name}"
}

_mfa_sidecar_write_secret_if_missing() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        umask 077
        ynh_string_random --length=64 > "$path"
    fi
}

_mfa_sidecar_write_env_file() {
    cat > /etc/mfa-sidecar/mfa-sidecar.env <<EOF
AUTHELIA_SESSION_SECRET=$(cat "$(_mfa_sidecar_secret_file session_secret)")
AUTHELIA_STORAGE_ENCRYPTION_KEY=$(cat "$(_mfa_sidecar_secret_file storage_encryption_key)")
AUTHELIA_IDENTITY_VALIDATION_RESET_PASSWORD_JWT_SECRET=$(cat "$(_mfa_sidecar_secret_file identity_validation_reset_secret)")
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
  cookie_domain: ""
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
    enabled: false
    display_name: MFA Sidecar
    attestation_conveyance_preference: indirect
    user_verification: preferred
    timeout: 60s
  totp:
    enabled: true
    issuer: MFA Sidecar
access_control:
  default_policy: ${seeded_default_policy}
  enforcement_enabled: true
  managed_sites: []
recovery:
  mode: authelia-reset-password-and-enrollment
  disable_reset: false
runtime:
  generate_nginx_snippets: true
  generate_authelia_config: true
  enforce_tls_upstream_verification: false
EOF
}

_mfa_sidecar_sync_runtime_assets() {
    python3 "$install_dir/bin/render_runtime_config.py" \
        "$install_dir/config/domain-policy.yaml" \
        "$install_dir/deploy/generated-runtime"

    python3 "$install_dir/bin/stage_runtime.py" \
        "$install_dir/deploy/generated-runtime" / \
        --owner "$app" \
        --group "$app"
}

_mfa_sidecar_wait_for_local_http() {
    local url="$1"
    local attempts="${2:-20}"
    local sleep_seconds="${3:-1}"
    local header_name="${4:-}"
    local header_value="${5:-}"
    local expected_status="${6:-200}"
    local i

    for ((i=1; i<=attempts; i++)); do
        if python3 - "$url" "$header_name" "$header_value" "$expected_status" <<'PY' >/dev/null 2>&1
import sys
import urllib.request
import urllib.error

url = sys.argv[1]
header_name = sys.argv[2]
header_value = sys.argv[3]
expected_status = int(sys.argv[4])
request = urllib.request.Request(url)
if header_name and header_value:
    request.add_header(header_name, header_value)
try:
    with urllib.request.urlopen(request, timeout=2) as response:
        raise SystemExit(0 if response.status == expected_status else 1)
except urllib.error.HTTPError as exc:
    raise SystemExit(0 if exc.code == expected_status else 1)
except Exception:
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

_mfa_sidecar_sync_protected_domain_includes() {
    local render_index="$install_dir/deploy/generated-runtime/render-index.json"
    if [[ ! -f "$render_index" ]]; then
        return 0
    fi

    python3 "$install_dir/bin/inject_protected_include.py" reinject-all "$render_index"
}

_mfa_sidecar_remove_protected_domain_includes() {
    local render_index="$install_dir/deploy/generated-runtime/render-index.json"
    if [[ ! -f "$render_index" ]]; then
        find /etc/nginx/conf.d -name '*.conf' -print0 2>/dev/null | while IFS= read -r -d '' conf; do
            python3 "$install_dir/bin/inject_protected_include.py" remove "$conf" || true
        done
        return 0
    fi

    python3 - "$render_index" "$install_dir/bin/inject_protected_include.py" <<'PYEOF'
import json
import subprocess
import sys
from pathlib import Path

render_index = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
injector = sys.argv[2]
seen_targets = set()

for bucket in ('enabled', 'disabled'):
    for entry in render_index.get(bucket, []):
        target = entry.get('target_conf')
        target_id = entry.get('id')

        if target and target not in seen_targets:
            seen_targets.add(target)
            subprocess.run(['python3', injector, 'remove', target], check=False)

        if target and target_id:
            bridge = Path(target).parent / f"mfa-sidecar-{target_id}.conf"
            try:
                bridge.unlink(missing_ok=True)
            except Exception:
                pass
PYEOF
}

_mfa_sidecar_install_reinject_hooks() {
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/hooks/post_app_upgrade-reinject)" /etc/yunohost/hooks.d/post_app_upgrade/50-mfa-sidecar-reinject
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/hooks/conf_regen-reinject)" /etc/yunohost/hooks.d/conf_regen/98-mfa-sidecar
    install -D -m 755 "$(_mfa_sidecar_pkg_path sources/hooks/apply-runtime-as-root)" "$install_dir/bin/apply-runtime-as-root"
}

_mfa_sidecar_remove_reinject_hooks() {
    rm -f /etc/yunohost/hooks.d/post_app_upgrade/50-mfa-sidecar-reinject
    rm -f /etc/yunohost/hooks.d/conf_regen/98-mfa-sidecar
}

_mfa_sidecar_write_sudoers() {
    cat > /etc/sudoers.d/mfa-sidecar <<SUDOEOF
# MFA Sidecar: allow admin UI to complete the apply cycle
${app} ALL=(root) NOPASSWD: $install_dir/bin/apply-runtime-as-root $install_dir
# MFA Sidecar: allow admin UI to discover YunoHost domains and apps
${app} ALL=(root) NOPASSWD: /usr/bin/yunohost domain list --output-as json
${app} ALL=(root) NOPASSWD: /usr/bin/yunohost app list --output-as json
# MFA Sidecar: allow admin UI to restart Authelia after user-management changes
${app} ALL=(root) NOPASSWD: /usr/bin/systemctl restart mfa-sidecar-authelia
SUDOEOF
    chmod 0440 /etc/sudoers.d/mfa-sidecar
}

_mfa_sidecar_remove_sudoers() {
    rm -f /etc/sudoers.d/mfa-sidecar
}

_mfa_sidecar_write_runtime_notes() {
    {
        printf '%s\n' 'MFA Sidecar package'
        printf '%s\n' '==================='
        printf '\n'
        printf '%s\n' 'This package seeds a managed-sites policy file, installs a vendored pinned'
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
        printf '%s\n' "- generated artifacts: $install_dir/deploy/generated-runtime/"
        printf '%s\n' '- authelia config: /etc/mfa-sidecar/authelia/configuration.yml'
        printf '%s\n' '- nginx portal include: /etc/mfa-sidecar/nginx/portal.conf'
        printf '%s\n' '- nginx protected includes: /etc/mfa-sidecar/nginx/protected/*.conf'
        printf '%s\n' '- env file: /etc/mfa-sidecar/mfa-sidecar.env'
        printf '%s\n' "- vendored authelia source: $install_dir/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz"
        printf '%s\n' "- installed authelia binary: $install_dir/bin/authelia"
        printf '\n'
        printf '%s\n' 'Current improvements:'
        printf '%s\n' '- dedicated portal domain enforced'
        printf '%s\n' '- managed host+path entries with longest-match-wins semantics'
        printf '%s\n' '- vendored pinned Authelia artifact with sha256 verification'
        printf '%s\n' '- separate sidecar-owned credential/MFA store with file-backed Authelia auth model'
        printf '\n'
        printf '%s\n' 'Remaining operator tasks:'
        printf '%s\n' '- if you did not create the first sidecar admin during install, do it immediately from the config panel before real auth validation'
        printf '%s\n' '- use the YunoHost config panel first for high-level settings, service actions, and admin-gate introspection'
        printf '%s\n' '- use YunoHost operator/admin auth to reach `/admin`; the admin UI is no longer intended to depend on a custom sidecar header secret'
        printf '%s\n' '- validate live auth flow after install'
        printf '%s\n' '- add and tune managed site entries from the admin control plane (`/admin`) until more of that surface is moved into YunoHost-native controls'
        printf '\n'
        printf '%s\n' 'Documentation shipped with this package:'
        printf '%s\n' "- top-level README: $install_dir/README.md"
        printf '%s\n' "- install guide: $install_dir/docs/INSTALL.md"
        printf '%s\n' "- admin guide: $install_dir/docs/ADMIN.md"
        printf '%s\n' "- users guide: $install_dir/docs/USERS.md"
        printf '%s\n' "- troubleshooting/recovery: $install_dir/docs/TROUBLESHOOTING.md"
    } > "$install_dir/README.package"
}
