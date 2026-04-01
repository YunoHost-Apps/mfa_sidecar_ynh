#!/usr/bin/env python3
from __future__ import annotations

import html
import os
import re
import secrets
import subprocess
import sys
import threading
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

import yaml

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from discovery import Discovery
from policy_admin import PolicyAdmin, PolicyError, normalize_path, validate_upstream, validate_entry_id


def extract_root_domain(host: str) -> str:
    parts = str(host or '').strip('.').split('.')
    if len(parts) <= 2:
        return str(host or '').strip('.')
    return '.'.join(parts[1:])


DEFAULT_POLICY_PATH = os.environ.get("MFA_SIDECAR_POLICY_PATH", "/etc/mfa-sidecar/config/domain-policy.yaml")
DEFAULT_RENDER_SCRIPT = os.environ.get("MFA_SIDECAR_RENDER_SCRIPT", str(BASE_DIR / "render_runtime_config.py"))
DEFAULT_STAGE_SCRIPT = os.environ.get("MFA_SIDECAR_STAGE_SCRIPT", str(BASE_DIR / "stage_runtime.py"))
DEFAULT_GENERATED_DIR = os.environ.get("MFA_SIDECAR_GENERATED_DIR", "/etc/mfa-sidecar/generated-runtime")
DEFAULT_STAGE_ROOT = os.environ.get("MFA_SIDECAR_STAGE_ROOT", "/")
DEFAULT_INSTALL_DIR = os.environ.get("MFA_SIDECAR_INSTALL_DIR", str(BASE_DIR.parent))
DEFAULT_USERS_FILE = os.environ.get("MFA_SIDECAR_USERS_FILE", "/etc/mfa-sidecar/authelia/users.yml")
DEFAULT_AUTHELIA_BIN = os.environ.get("MFA_SIDECAR_AUTHELIA_BIN", str(Path(DEFAULT_INSTALL_DIR) / "bin" / "authelia"))
DEFAULT_MANAGE_USERS_SCRIPT = os.environ.get("MFA_SIDECAR_MANAGE_USERS_SCRIPT", str(BASE_DIR / "manage_authelia_users.py"))
BIND_HOST = os.environ.get("MFA_SIDECAR_ADMIN_BIND", "127.0.0.1")
BIND_PORT = int(os.environ.get("MFA_SIDECAR_ADMIN_PORT", "9087"))
DISCOVERY_NGINX_CONF_DIR = os.environ.get("MFA_SIDECAR_DISCOVERY_NGINX_CONF_DIR", "/etc/nginx/conf.d")
DISCOVERY_YUNOHOST_BIN = os.environ.get("MFA_SIDECAR_DISCOVERY_YUNOHOST_BIN", "/usr/bin/yunohost")
USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$")
CSRF_COOKIE_NAME = "mfa_sidecar_admin_csrf"
RESERVED_USERNAMES = {"admin"}


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


def managed_entry_sort_key(entry: dict) -> tuple[int, str, str]:
    """Sort protected/enabled targets first, then host, then path."""
    enabled_rank = 0 if bool(entry.get("enabled")) else 1
    host = str(entry.get("host", "")).lower()
    path = normalize_path(entry.get("path", "/")).lower()
    return (enabled_rank, host, path)


def validate_username(username: str) -> str:
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        raise PolicyError("username must match [A-Za-z0-9][A-Za-z0-9_.@-]{0,127}")
    if username.lower() in RESERVED_USERNAMES:
        raise PolicyError("username 'admin' is not allowed for MFA Sidecar because it commonly collides with legacy/system/YunoHost identity expectations; choose a distinct operator username such as 'mfaadmin'")
    return username


def load_package_version() -> str:
    candidates = [
        Path(DEFAULT_INSTALL_DIR) / "manifest.toml",
        BASE_DIR.parent / "manifest.toml",
    ]
    for path in candidates:
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("version = "):
                    return line.split("=", 1)[1].strip().strip('"')
        except OSError:
            continue
    return "unknown"


def load_live_runtime_metadata() -> dict:
    path = Path("/etc/mfa-sidecar/runtime-metadata.json")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    return data if isinstance(data, dict) else {}


class AdminApp:
    def __init__(self) -> None:
        self.policy_path = Path(DEFAULT_POLICY_PATH)
        self.generated_dir = Path(DEFAULT_GENERATED_DIR)
        self.users_file = Path(DEFAULT_USERS_FILE)
        self.policy = PolicyAdmin(self.policy_path)
        self.discovery = Discovery(
            nginx_conf_dir=DISCOVERY_NGINX_CONF_DIR,
            yunohost_bin=DISCOVERY_YUNOHOST_BIN,
        )
        self.lock = threading.Lock()
        self.csrf_token = secrets.token_urlsafe(32)

    def apply_runtime(self) -> None:
        if os.environ.get("MFA_SIDECAR_SKIP_ROOT_APPLY") == "1":
            subprocess.run(["python3", DEFAULT_RENDER_SCRIPT, str(self.policy_path), str(self.generated_dir)], check=True)
            subprocess.run(["python3", DEFAULT_STAGE_SCRIPT, str(self.generated_dir), DEFAULT_STAGE_ROOT], check=True)
            return
        apply_helper = str(Path(DEFAULT_INSTALL_DIR) / "bin" / "apply-runtime-as-root")
        subprocess.run(["sudo", apply_helper, DEFAULT_INSTALL_DIR], check=True, capture_output=True, text=True)

    def _run_manage_users(self, *args: str) -> None:
        subprocess.run(["python3", DEFAULT_MANAGE_USERS_SCRIPT, *args], check=True)
        subprocess.run(["sudo", "/usr/bin/systemctl", "restart", "mfa-sidecar-authelia"], check=True)

    def clear_active_sessions(self) -> None:
        with self.lock:
            subprocess.run(["sudo", "/usr/bin/systemctl", "restart", "mfa-sidecar-authelia"], check=True)

    def load_users(self) -> list[dict]:
        if not self.users_file.exists():
            return []
        data = yaml.safe_load(self.users_file.read_text(encoding="utf-8")) or {}
        users = data.get("users", {}) if isinstance(data, dict) else {}
        rows = []
        for username, meta in sorted(users.items()):
            if not isinstance(meta, dict):
                continue
            rows.append(
                {
                    "username": username,
                    "displayname": meta.get("displayname", username),
                    "email": meta.get("email", ""),
                    "groups": meta.get("groups", []) or [],
                    "disabled": bool(meta.get("disabled", False)),
                    "managed": bool(meta.get("managed_by_mfa_sidecar_sync", False)),
                    "has_password": bool(meta.get("password")),
                    "mfa_fields": [
                        key for key in ["totp_secret", "webauthn", "webauthn_credentials", "one_time_password", "mobile_push"]
                        if key in meta
                    ],
                }
            )
        return rows

    def ensure_user(self, *, username: str, display_name: str, email: str, password: str, groups: list[str]) -> None:
        with self.lock:
            self._run_manage_users(
                "ensure-user",
                "--users-file", str(self.users_file),
                "--authelia-bin", DEFAULT_AUTHELIA_BIN,
                "--username", username,
                "--display-name", display_name,
                "--email", email,
                "--password", password,
                "--groups", *groups,
            )

    def set_user_password(self, *, username: str, password: str) -> None:
        with self.lock:
            self._run_manage_users(
                "set-password",
                "--users-file", str(self.users_file),
                "--authelia-bin", DEFAULT_AUTHELIA_BIN,
                "--username", username,
                "--password", password,
            )

    def set_user_disabled(self, *, username: str, disabled: bool) -> None:
        with self.lock:
            self._run_manage_users(
                "set-disabled",
                "--users-file", str(self.users_file),
                "--username", username,
                "--disabled" if disabled else "--enabled",
            )

    def reset_user_mfa(self, *, username: str) -> None:
        with self.lock:
            self._run_manage_users(
                "reset-mfa",
                "--users-file", str(self.users_file),
                "--username", username,
            )

    def set_user_role(self, *, username: str, role: str) -> None:
        groups = [role] if role in {"users", "admins"} else ["users"]
        with self.lock:
            self._run_manage_users(
                "set-groups",
                "--users-file", str(self.users_file),
                "--username", username,
                "--groups", *groups,
            )

    def add_entry_and_apply(self, *, host: str, path: str, label: str, upstream: str, enabled: bool, target_conf: str = "") -> None:
        entry_id = PolicyAdmin.slugify(f"{host}-{path}")
        with self.lock:
            self.policy.add_entry(
                entry_id=entry_id,
                label=label,
                host=host,
                path=path,
                upstream=upstream,
                enabled=enabled,
                target_conf=(target_conf or self.discovery.discover_target_conf(host, path)),
            )
            self.apply_runtime()

    def update_entry_and_apply(self, *, entry_id: str, label: str, host: str, path: str, upstream: str, enabled: bool, target_conf: str = "") -> None:
        with self.lock:
            self.policy.update_entry(
                entry_id=entry_id,
                label=label,
                host=host,
                path=path,
                upstream=upstream,
                enabled=enabled,
                target_conf=(target_conf or self.discovery.discover_target_conf(host, path)),
            )
            self.apply_runtime()

    def toggle_entry_and_apply(self, entry_id: str) -> None:
        with self.lock:
            self.policy.toggle_entry(entry_id)
            self.apply_runtime()

    def delete_entry_and_apply(self, entry_id: str) -> None:
        with self.lock:
            self.policy.delete_entry(entry_id)
            self.apply_runtime()

    def set_enforcement_enabled_and_apply(self, enabled: bool) -> None:
        with self.lock:
            self.policy.set_enforcement_enabled(enabled)
            self.apply_runtime()

    def discovered_targets(self) -> tuple[list[dict], str]:
        try:
            discovered = self.discovery.discover()
            managed_pairs = {(entry['host'], normalize_path(entry.get('path', '/'))) for entry in self.policy.list_entries()}
            suggestions = [
                item for item in discovered.get('suggestions', [])
                if item['kind'] in {'app-path', 'domain'}
                and (item['host'], normalize_path(item.get('path', '/'))) not in managed_pairs
            ]
            return suggestions, ""
        except Exception as exc:
            return [], str(exc)

    def render_users_page(self, error: str = "", notice: str = "", csrf_token: str = "") -> str:
        package_version = load_package_version()
        users = self.load_users()
        csrf_input = f"<input type='hidden' name='csrf_token' value='{h(csrf_token)}' />"
        rows = []
        for user in users:
            groups = ", ".join(user["groups"]) or "(none)"
            state = "Disabled" if user["disabled"] else "Enabled"
            managed = "YunoHost-synced" if user["managed"] else "Sidecar-local"
            mfa_state = ", ".join(user["mfa_fields"]) if user["mfa_fields"] else "none recorded"
            current_role = 'admins' if 'admins' in user['groups'] else 'users'
            rows.append(
                f"<tr>"
                f"<td><code>{h(user['username'])}</code></td>"
                f"<td>{h(user['displayname'])}</td>"
                f"<td>{h(user['email'])}</td>"
                f"<td>{h(groups)}<form method='post' action='/admin/users/{h(user['username'])}/role' style='margin-top:0.4rem;'>{csrf_input}<select name='role'><option value='users' {'selected' if current_role == 'users' else ''}>User</option><option value='admins' {'selected' if current_role == 'admins' else ''}>Admin</option></select> <button type='submit'>Set role</button></form></td>"
                f"<td>{h(state)}<br><span class='muted'>{h(managed)}</span></td>"
                f"<td><span class='muted'>{h(mfa_state)}</span></td>"
                f"<td>"
                f"<form method='post' action='/admin/users/{h(user['username'])}/password' style='display:inline-block; margin:0 0.4rem 0.4rem 0;'>"
                f"{csrf_input}<input type='password' name='password' placeholder='New password' required /> "
                f"<button type='submit' onclick=\"return confirm('Reset password for this user?');\">Set password</button>"
                f"</form>"
                f"<form method='post' action='/admin/users/{h(user['username'])}/mfa-reset' style='display:inline-block; margin:0 0.4rem 0.4rem 0;'>"
                f"{csrf_input}<button type='submit' onclick=\"return confirm('Clear stored MFA enrollment data for this user? They will need to enroll again.');\">Reset MFA</button>"
                f"</form>"
                f"<form method='post' action='/admin/users/{h(user['username'])}/{'enable' if user['disabled'] else 'disable'}' style='display:inline-block; margin:0 0.4rem 0.4rem 0;'>"
                f"{csrf_input}<button type='submit' onclick=\"return confirm('{'Enable' if user['disabled'] else 'Disable'} this user?');\">{'Enable' if user['disabled'] else 'Disable'}</button>"
                f"</form>"
                f"</td>"
                f"</tr>"
            )
        users_html = "\n".join(rows) or "<tr><td colspan='7'><em>No sidecar users found.</em></td></tr>"
        error_html = f"<div class='error'>{h(error)}</div>" if error else ""
        notice_html = f"<div class='notice'>{h(notice)}</div>" if notice else ""
        summary = self.policy.portal_summary()
        enforcement_enabled = bool(summary.get('enforcement_enabled', True))
        disabled_bar = ""
        if not enforcement_enabled:
            disabled_bar = (
                "<div class='error' style='background:#b30000;color:#fff;border-color:#800;padding:1rem 1rem 1.1rem;'>"
                "<strong>Emergency bypass is ACTIVE.</strong> MFA Sidecar enforcement is disabled globally, so protected targets are currently bypassed. "
                "User recovery actions are still available here, but the perimeter is not being enforced right now."
                f"<form method='post' action='/admin/global/enable' style='display:block; margin-top: 0.85rem;'>{csrf_input}"
                "<button type='submit' style='font-weight:700;'>Re-enable global protection now</button>"
                "</form></div>"
            )
        return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>MFA Sidecar users</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.4; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; vertical-align: top; }}
    code {{ white-space: nowrap; }}
    .error {{ background: #fee; color: #900; padding: 0.75rem; margin: 1rem 0; border: 1px solid #d99; }}
    .notice {{ background: #efe; color: #060; padding: 0.75rem; margin: 1rem 0; border: 1px solid #9d9; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(16rem, 1fr)); gap: 0.75rem 1rem; }}
    label span {{ display: block; font-weight: 600; margin-bottom: 0.25rem; }}
    input[type=text], input[type=password], input[type=email] {{ width: 100%; padding: 0.45rem; box-sizing: border-box; }}
    .muted {{ color: #555; font-size: 0.92em; }}
  </style>
</head>
<body>
  <h1>MFA Sidecar users</h1>
  <p class='muted'>Version <code>{h(package_version)}</code> · Admin recovery surface for sidecar users. End users should still manage their own MFA from their normal login flow.</p>
  <p><a href='/admin'>← Back to targets</a></p>
  {disabled_bar}
  {notice_html}
  {error_html}

  <h2>Existing users</h2>
  <p class='muted'>This page is for admin visibility and recovery. Password reset and MFA reset are intentionally explicit because both can ruin somebody's afternoon.</p>
  <table>
    <thead>
      <tr>
        <th>Username</th><th>Display name</th><th>Email</th><th>Groups</th><th>Status</th><th>MFA data</th><th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {users_html}
    </tbody>
  </table>

  <h2>Add or update user</h2>
  <form method='post' action='/admin/users/ensure'>
    {csrf_input}
    <div class='grid'>
      <label><span>Username</span><input type='text' name='username' required /></label>
      <label><span>Display name</span><input type='text' name='display_name' required /></label>
      <label><span>Email</span><input type='email' name='email' required /></label>
      <label><span>Password</span><input type='password' name='password' required /></label>
      <label><span>Role</span>
        <select name='role'>
          <option value='users' selected>User</option>
          <option value='admins'>Admin</option>
        </select>
      </label>
    </div>
    <p class='muted'>Role defaults to <code>users</code>. Use <code>admins</code> only for actual administrators. This action creates the user if missing or updates the record if it already exists.</p>
    <p><button type='submit'>Create or update user</button></p>
  </form>
</body>
</html>
"""

    def render_index(self, error: str = "", notice: str = "", edit_entry_id: str = "", csrf_token: str = "") -> str:
        summary = self.policy.portal_summary()
        live_runtime = load_live_runtime_metadata()
        package_version = load_package_version()
        csrf_input = f"<input type='hidden' name='csrf_token' value='{h(csrf_token)}' />"
        entries = sorted(self.policy.list_entries(), key=managed_entry_sort_key)
        portal_domain = summary.get('portal_domain', '')
        root_domain = extract_root_domain(portal_domain)
        policy_enforcement_enabled = bool(summary.get('enforcement_enabled', True))
        live_enforcement_enabled = bool(live_runtime.get('enforcement_enabled', policy_enforcement_enabled))
        enforcement_enabled = live_enforcement_enabled
        discovered, discovery_error = self.discovered_targets()
        edit_entry = next((entry for entry in entries if entry['id'] == edit_entry_id), None)

        entries_by_pair = {
            (entry['host'], normalize_path(entry.get('path', '/'))): entry
            for entry in entries
        }
        managed_rows = []
        discovered_rows = []

        for item in discovered:
            path_value = normalize_path(item.get('path', '/'))
            pair = (item['host'], path_value)
            if pair in entries_by_pair:
                continue
            upstream_value = item.get('suggested_upstream', 'https://127.0.0.1:443')
            try:
                upstream_value = validate_upstream(upstream_value)
            except PolicyError:
                upstream_value = 'https://127.0.0.1:443'
            nginx_state = 'yes' if item.get('nginx_present') else 'no'
            is_danger_target = item['host'] == portal_domain or (item['host'] == root_domain and path_value == '/')
            confirm_text = ''
            if is_danger_target:
                confirm_text = "return confirm('Dangerous target. Have you tested MFA Sidecar on a non-root domain first? Enabling protection here can lock you out of services or normal admin access.');"
            common_inputs = (
                f"<input type='hidden' name='label' value='{h(item.get('label', ''))}' />"
                f"<input type='hidden' name='host' value='{h(item['host'])}' />"
                f"<input type='hidden' name='path' value='{h(path_value)}' />"
                f"<input type='hidden' name='upstream' value='{h(upstream_value)}' />"
                f"<input type='hidden' name='target_conf' value='{h(item.get('target_conf', ''))}' />"
            )
            warning_html = ""
            if is_danger_target:
                warning_html = "<br><span class='danger-text'>Danger zone: test on a non-root domain first.</span>"
            discovered_rows.append(
                f"<tr>"
                f"<td>{h(item.get('label', ''))}</td>"
                f"<td><code>{h(item['host'])}</code></td>"
                f"<td><code>{h(path_value)}</code></td>"
                f"<td><code>{h(item.get('app_id', ''))}</code><br><span class='muted'>{h(item.get('target_conf', ''))}</span></td>"
                f"<td><code>{h(upstream_value)}</code></td>"
                f"<td><span class='muted'>unmanaged · nginx check: {h(nginx_state)}</span>{warning_html}</td>"
                f"<td>"
                f"<form method='post' action='/admin/discoveries/add' style='display:inline-block;'>"
                f"{csrf_input}{common_inputs}"
                f"<input type='hidden' name='enabled' value='true' />"
                f"<button class='toggle toggle-off' type='submit' onclick=\"{confirm_text}\"><span class='toggle-knob'></span><span class='toggle-label'>Bypass</span></button>"
                f"</form>"
                f"</td>"
                f"</tr>"
            )

        for entry in entries:
            enabled = bool(entry.get("enabled"))
            state = "Protect" if enabled else "Bypass"
            path_value = normalize_path(entry.get('path', '/'))
            is_danger_target = entry['host'] == portal_domain or (entry['host'] == root_domain and path_value == '/')
            toggle_confirm = ''
            if is_danger_target and not enabled:
                toggle_confirm = "return confirm('Dangerous target. Have you tested MFA Sidecar on a non-root domain first? Enabling protection here can lock you out of services or normal admin access.');"
            warning_html = ""
            if is_danger_target:
                warning_html = "<br><span class='danger-text'>Danger zone: test on a non-root domain first.</span>"
            toggle_class = 'toggle-on' if enabled else 'toggle-off'
            managed_rows.append(
                f"<tr>"
                f"<td>{h(entry.get('label', ''))}</td>"
                f"<td><code>{h(entry['host'])}</code></td>"
                f"<td><code>{h(path_value)}</code></td>"
                f"<td><code>{h(entry['id'])}</code><br><span class='muted'>{h(entry.get('target_conf', ''))}</span></td>"
                f"<td><code>{h(entry['upstream'])}</code></td>"
                f"<td>{warning_html}</td>"
                f"<td>"
                f"<form method='post' action='/admin/entries/{h(entry['id'])}/toggle' style='display:inline-block; margin-right: 0.4rem;'>"
                f"{csrf_input}<button class='toggle {toggle_class}' type='submit' onclick=\"{toggle_confirm}\"><span class='toggle-knob'></span><span class='toggle-label'>{h(state)}</span></button>"
                f"</form>"
                f"<form method='get' action='/admin' style='display:inline-block; margin-right: 0.4rem;'>"
                f"<input type='hidden' name='edit' value='{h(entry['id'])}' />"
                f"<button type='submit'>Edit</button>"
                f"</form>"
                f"<form method='post' action='/admin/entries/{h(entry['id'])}/delete' style='display:inline-block;'>"
                f"{csrf_input}<button type='submit' onclick=\"return confirm('Delete this managed entry?');\">Delete</button>"
                f"</form>"
                f"</td>"
                f"</tr>"
            )

        targets_html = "\n".join(managed_rows + discovered_rows) or "<tr><td colspan='7'><em>No discovered or managed app locations yet.</em></td></tr>"

        error_html = f"<div class='error'>{h(error)}</div>" if error else ""
        notice_html = f"<div class='notice'>{h(notice)}</div>" if notice else ""
        discovery_html = f"<div class='error'>Discovery degraded: {h(discovery_error)}</div>" if discovery_error else ""
        state_mismatch_html = ""
        if live_enforcement_enabled != policy_enforcement_enabled:
            state_mismatch_html = (
                "<div class='error'>"
                f"<strong>Live/runtime mismatch.</strong> Policy says global enforcement is <code>{'enabled' if policy_enforcement_enabled else 'disabled'}</code>, "
                f"but the last applied runtime reports <code>{'enabled' if live_enforcement_enabled else 'disabled'}</code>. "
                "The live runtime state is shown below. Re-apply before trusting the toggle state."
                "</div>"
            )
        disabled_bar = ""
        if not enforcement_enabled:
            disabled_bar = (
                "<div class='error' style='background:#b30000;color:#fff;border-color:#800;padding:1rem 1rem 1.1rem;'>"
                "<strong>Emergency bypass is ACTIVE.</strong> MFA Sidecar enforcement is disabled globally, so protected targets are currently bypassed. "
                "Use this only as a break-glass state, then turn protection back on once you have recovered access."
                f"<form method='post' action='/admin/global/enable' style='display:block; margin-top: 0.85rem;'>{csrf_input}"
                "<button type='submit' style='font-weight:700;'>Re-enable global protection now</button>"
                "</form></div>"
            )
        if edit_entry:
            form_title = f"Edit managed entry: {edit_entry['id']}"
            form_action = f"/admin/entries/{edit_entry['id']}/update"
            submit_label = "Update entry and apply"
            form_label = edit_entry.get('label', '')
            form_host = edit_entry['host']
            form_path = normalize_path(edit_entry.get('path', '/'))
            form_upstream = edit_entry['upstream']
            form_enabled = 'true' if edit_entry.get('enabled') else 'false'
            form_target_conf = edit_entry.get('target_conf', '')
            cancel_html = "<p><a href='/admin'>Cancel edit</a></p>"
            advanced_summary = "Editing advanced values is available if auto-detection needs help."
        else:
            form_title = "Add managed entry"
            form_action = "/admin/entries"
            submit_label = "Add entry and apply"
            form_label = ""
            form_host = ""
            form_path = "/"
            form_upstream = ""
            form_enabled = 'false'
            form_target_conf = ''
            cancel_html = ""
            advanced_summary = "Advanced overrides are optional. Leave them hidden unless discovery is wrong or nginx is weird."
        return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>MFA Sidecar admin</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.4; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; vertical-align: top; }}
    code {{ white-space: nowrap; }}
    .error {{ background: #fee; color: #900; padding: 0.75rem; margin: 1rem 0; border: 1px solid #d99; }}
    .notice {{ background: #efe; color: #060; padding: 0.75rem; margin: 1rem 0; border: 1px solid #9d9; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(16rem, 1fr)); gap: 0.75rem 1rem; }}
    label span {{ display: block; font-weight: 600; margin-bottom: 0.25rem; }}
    input[type=text], input[type=password], input[type=email], select {{ width: 100%; padding: 0.45rem; box-sizing: border-box; }}
    .muted {{ color: #555; font-size: 0.92em; }}
    .danger-text {{ color: #900; font-weight: 600; }}
    .state-badge {{ display: inline-block; min-width: 4.75rem; text-align: center; padding: 0.2rem 0.55rem; border-radius: 999px; font-weight: 700; font-size: 0.9rem; }}
    .state-on {{ background: #dff3e3; color: #126a2f; border: 1px solid #8cc79a; }}
    .state-off {{ background: #ececec; color: #555; border: 1px solid #b8b8b8; }}
    .toggle {{ display: inline-flex; align-items: center; gap: 0.55rem; min-width: 8.25rem; padding: 0.32rem 0.75rem 0.32rem 0.4rem; border-radius: 999px; border: 1px solid #999; cursor: pointer; font-weight: 700; }}
    .toggle-knob {{ display: inline-block; width: 1.15rem; height: 1.15rem; border-radius: 50%; background: #fff; border: 1px solid rgba(0,0,0,0.18); box-shadow: 0 1px 2px rgba(0,0,0,0.18); }}
    .toggle-on {{ background: #2f8f4e; border-color: #2b7f45; color: #fff; }}
    .toggle-off {{ background: #d7d7d7; border-color: #a8a8a8; color: #333; }}
    nav {{ margin: 0.75rem 0 1rem; }}
    nav a {{ margin-right: 0.8rem; display: inline-block; padding: 0.5rem 0.8rem; border: 1px solid #888; border-radius: 0.35rem; text-decoration: none; color: #111; background: #f5f5f5; font-weight: 600; }}
    nav a:hover {{ background: #e9e9e9; }}
  </style>
</head>
<body>
  <h1>MFA Sidecar admin</h1>
  <nav>
    <a href='/admin'>Targets</a>
    <a href='/admin/users'>Users</a>
  </nav>
  <p class='muted'>Version <code>{h(package_version)}</code> · Simple operator control plane. Domains come from YunoHost. App subpaths come from YunoHost app inventory. nginx is only a light sanity check for discovered app paths.</p>
  {disabled_bar}
  {state_mismatch_html}
  {notice_html}
  {error_html}
  {discovery_html}

  <h2>Portal summary</h2>
  <ul>
    <li><strong>Portal domain:</strong> <code>{h(summary['portal_domain'])}</code></li>
    <li><strong>Portal path:</strong> <code>{h(summary['portal_path'])}</code></li>
    <li><strong>Remembered session:</strong> <code>{h(summary['remember_me'])}</code></li>
    <li><strong>Default policy:</strong> <code>{h(summary['default_policy'])}</code></li>
    <li><strong>Live global enforcement:</strong> <code>{'enabled' if live_enforcement_enabled else 'disabled (emergency bypass active)'}</code></li>
    <li><strong>Policy intent:</strong> <code>{'enabled' if policy_enforcement_enabled else 'disabled'}</code></li>
  </ul>
  <form method='post' action='/admin/global/{'disable' if enforcement_enabled else 'enable'}' style='margin-bottom: 0.5rem;'>
    {csrf_input}
    <button class='toggle {'toggle-on' if enforcement_enabled else 'toggle-off'}' type='submit'><span class='toggle-knob'></span><span class='toggle-label'>{'Disable global protection (break-glass)' if enforcement_enabled else 'Re-enable global protection'}</span></button>
  </form>
  <form method='post' action='/admin/global/clear-sessions' style='margin-bottom: 1rem;'>
    {csrf_input}
    <button type='submit' onclick="return confirm('Clear all active MFA Sidecar sessions? This restarts Authelia and forces users to log in again on next access.');">Clear active sessions (force re-login)</button>
  </form>

  <h2>Targets</h2>
  <p class='muted'>One table, one control surface. Discovered YunoHost app locations appear here as unmanaged rows with one-click onboarding. Managed rows stay here too, so manual add lands in the same list with the same controls.</p>
  <table>
    <thead>
      <tr>
        <th>Label</th><th>Host</th><th>Path</th><th>ID / source</th><th>Upstream</th><th>Notes</th><th>Action</th>
      </tr>
    </thead>
    <tbody>
      {targets_html}
    </tbody>
  </table>

  <h2>{h(form_title)}</h2>
  <form method='post' action='{h(form_action)}'>
    {csrf_input}
    <div class='grid'>
      <label><span>Label</span><input type='text' name='label' placeholder='Homebox' value='{h(form_label)}' /></label>
      <label><span>Host</span><input type='text' name='host' placeholder='home.wm3v.com' value='{h(form_host)}' required /></label>
      <label><span>Path</span><input type='text' name='path' value='{h(form_path)}' required /></label>
      <label><span>Initial state</span>
        <select name='enabled'>
          <option value='false' {'selected' if form_enabled == 'false' else ''}>Bypass</option>
          <option value='true' {'selected' if form_enabled == 'true' else ''}>Protected</option>
        </select>
      </label>
    </div>
    <details style='margin-top: 1rem;'>
      <summary>{h(advanced_summary)}</summary>
      <div class='grid' style='margin-top: 0.75rem;'>
        <label><span>Upstream override</span><input type='text' name='upstream' placeholder='Auto-detect from nginx when blank' value='{h(form_upstream)}' /></label>
        <label><span>Target nginx conf override</span><input type='text' name='target_conf' value='{h(form_target_conf)}' placeholder='Auto-detect from host/path when blank' /></label>
      </div>
      <p class='muted'>Most installs should leave these blank. Sidecar will infer them from existing YunoHost/nginx state.</p>
    </details>
    <p><button type='submit'>{h(submit_label)}</button></p>
  </form>
  {cancel_html}
</body>
</html>
"""


APP = AdminApp()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if not self._authorized():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path in {"/", "/admin"}:
            edit_entry_id = qs.get("edit", [""])[0]
            body = APP.render_index(error=qs.get("error", [""])[0], notice=qs.get("notice", [""])[0], edit_entry_id=edit_entry_id, csrf_token=APP.csrf_token)
        elif parsed.path == "/admin/users":
            body = APP.render_users_page(error=qs.get("error", [""])[0], notice=qs.get("notice", [""])[0], csrf_token=APP.csrf_token)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        payload = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Set-Cookie", f"{CSRF_COOKIE_NAME}={APP.csrf_token}; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        if not self._authorized():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length).decode("utf-8")
        form = parse_qs(raw)
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        cookie_token = cookie.get(CSRF_COOKIE_NAME).value if cookie.get(CSRF_COOKIE_NAME) else ""
        form_token = form.get("csrf_token", [""])[0]
        if cookie_token != APP.csrf_token or form_token != APP.csrf_token:
            self.send_error(HTTPStatus.FORBIDDEN, "invalid CSRF token")
            return
        try:
            if parsed.path in {"/admin/entries", "/admin/discoveries/add"}:
                host = form.get("host", [""])[0]
                path = form.get("path", ["/"])[0]
                label = form.get("label", [""])[0]
                upstream = form.get("upstream", [""])[0].strip()
                enabled = form.get("enabled", ["false"])[0].lower() == "true"
                target_conf = form.get("target_conf", [""])[0].strip()
                if not upstream:
                    upstream = APP.discovery._discover_upstream(host, path)
                APP.add_entry_and_apply(host=host, path=path, label=label, upstream=upstream, enabled=enabled, target_conf=target_conf)
                self._redirect("/admin?notice=" + quote_plus("Entry added and runtime applied"))
                return
            if parsed.path.startswith("/admin/entries/") and parsed.path.endswith("/toggle"):
                entry_id = validate_entry_id(parsed.path.split("/")[3])
                APP.toggle_entry_and_apply(entry_id)
                self._redirect("/admin?notice=" + quote_plus("Entry toggled and runtime applied"))
                return
            if parsed.path.startswith("/admin/entries/") and parsed.path.endswith("/update"):
                entry_id = validate_entry_id(parsed.path.split("/")[3])
                host = form.get("host", [""])[0]
                path = form.get("path", ["/"])[0]
                label = form.get("label", [""])[0]
                upstream = form.get("upstream", [""])[0].strip()
                enabled = form.get("enabled", ["false"])[0].lower() == "true"
                target_conf = form.get("target_conf", [""])[0].strip()
                if not upstream:
                    upstream = APP.discovery._discover_upstream(host, path)
                APP.update_entry_and_apply(entry_id=entry_id, host=host, path=path, label=label, upstream=upstream, enabled=enabled, target_conf=target_conf)
                self._redirect("/admin?notice=" + quote_plus("Entry updated and runtime applied"))
                return
            if parsed.path.startswith("/admin/entries/") and parsed.path.endswith("/delete"):
                entry_id = validate_entry_id(parsed.path.split("/")[3])
                APP.delete_entry_and_apply(entry_id)
                self._redirect("/admin?notice=" + quote_plus("Entry deleted and runtime applied"))
                return
            if parsed.path == "/admin/global/disable":
                APP.set_enforcement_enabled_and_apply(False)
                self._redirect("/admin?notice=" + quote_plus("MFA Sidecar disabled globally; protection is now bypassed until re-enabled"))
                return
            if parsed.path == "/admin/global/enable":
                APP.set_enforcement_enabled_and_apply(True)
                self._redirect("/admin?notice=" + quote_plus("MFA Sidecar re-enabled globally and runtime applied"))
                return
            if parsed.path == "/admin/global/clear-sessions":
                APP.clear_active_sessions()
                self._redirect("/admin?notice=" + quote_plus("Cleared active sessions by restarting Authelia; users will need to log in again"))
                return
            if parsed.path == "/admin/users/ensure":
                username = validate_username(form.get("username", [""])[0].strip())
                display_name = form.get("display_name", [""])[0].strip()
                email = form.get("email", [""])[0].strip()
                password = form.get("password", [""])[0]
                role = form.get("role", ["users"])[0].strip()
                groups = [role] if role in {"users", "admins"} else ["users"]
                APP.ensure_user(username=username, display_name=display_name, email=email, password=password, groups=groups)
                self._redirect("/admin/users?notice=" + quote_plus(f"User '{username}' created or updated as {groups[0][:-1] if groups[0].endswith('s') else groups[0]}"))
                return
            if parsed.path.startswith("/admin/users/") and parsed.path.endswith("/password"):
                username = validate_username(parsed.path.split("/")[3])
                password = form.get("password", [""])[0]
                APP.set_user_password(username=username, password=password)
                self._redirect("/admin/users?notice=" + quote_plus(f"Password reset for '{username}'"))
                return
            if parsed.path.startswith("/admin/users/") and parsed.path.endswith("/role"):
                username = validate_username(parsed.path.split("/")[3])
                role = form.get("role", ["users"])[0].strip()
                APP.set_user_role(username=username, role=role)
                self._redirect("/admin/users?notice=" + quote_plus(f"Updated role for '{username}' to {role[:-1] if role.endswith('s') else role}"))
                return
            if parsed.path.startswith("/admin/users/") and parsed.path.endswith("/mfa-reset"):
                username = validate_username(parsed.path.split("/")[3])
                APP.reset_user_mfa(username=username)
                self._redirect("/admin/users?notice=" + quote_plus(f"Cleared MFA enrollment fields for '{username}'"))
                return
            if parsed.path.startswith("/admin/users/") and parsed.path.endswith("/disable"):
                username = validate_username(parsed.path.split("/")[3])
                APP.set_user_disabled(username=username, disabled=True)
                self._redirect("/admin/users?notice=" + quote_plus(f"Disabled '{username}'"))
                return
            if parsed.path.startswith("/admin/users/") and parsed.path.endswith("/enable"):
                username = validate_username(parsed.path.split("/")[3])
                APP.set_user_disabled(username=username, disabled=False)
                self._redirect("/admin/users?notice=" + quote_plus(f"Enabled '{username}'"))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except PolicyError as exc:
            target = "/admin/users" if parsed.path.startswith("/admin/users") else "/admin"
            self._redirect(target + "?error=" + quote_plus(str(exc)))
        except subprocess.CalledProcessError as exc:
            target = "/admin/users" if parsed.path.startswith("/admin/users") else "/admin"
            stderr_text = (exc.stderr or "").strip()
            stdout_text = (exc.stdout or "").strip()
            if stderr_text:
                print(f"mfa-sidecar admin apply failed stderr: {stderr_text}", file=sys.stderr)
            if stdout_text:
                print(f"mfa-sidecar admin apply failed stdout: {stdout_text}", file=sys.stderr)
            self._redirect(target + "?error=" + quote_plus("Apply failed. Live enforcement may not match policy intent yet. Check runtime state below and review the admin service journal for details."))

    def log_message(self, format: str, *args) -> None:
        return

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def _authorized(self) -> bool:
        # Intentional trust model: this loopback-only admin UI relies on the
        # YunoHost/nginx fronting layer to enforce operator auth before traffic
        # reaches localhost:9087. This method remains permissive by design, but
        # the boundary should stay documented and reviewed.
        return True


if __name__ == "__main__":
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    print(f"MFA Sidecar admin UI listening on http://{BIND_HOST}:{BIND_PORT}")
    server.serve_forever()
