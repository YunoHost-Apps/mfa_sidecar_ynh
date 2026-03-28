#!/usr/bin/env python3
from __future__ import annotations

import html
import os
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

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
DEFAULT_RENDER_SCRIPT = os.environ.get("MFA_SIDECAR_RENDER_SCRIPT", str(BASE_DIR / "render_alpha_config.py"))
DEFAULT_STAGE_SCRIPT = os.environ.get("MFA_SIDECAR_STAGE_SCRIPT", str(BASE_DIR / "stage_alpha_runtime.py"))
DEFAULT_GENERATED_DIR = os.environ.get("MFA_SIDECAR_GENERATED_DIR", "/etc/mfa-sidecar/generated-alpha")
DEFAULT_STAGE_ROOT = os.environ.get("MFA_SIDECAR_STAGE_ROOT", "/")
DEFAULT_INSTALL_DIR = os.environ.get("MFA_SIDECAR_INSTALL_DIR", "/opt/yunohost/mfa_sidecar")
BIND_HOST = os.environ.get("MFA_SIDECAR_ADMIN_BIND", "127.0.0.1")
BIND_PORT = int(os.environ.get("MFA_SIDECAR_ADMIN_PORT", "9087"))
DISCOVERY_NGINX_CONF_DIR = os.environ.get("MFA_SIDECAR_DISCOVERY_NGINX_CONF_DIR", "/etc/nginx/conf.d")
DISCOVERY_YUNOHOST_BIN = os.environ.get("MFA_SIDECAR_DISCOVERY_YUNOHOST_BIN", "/usr/bin/yunohost")


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


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


class AdminApp:
    def __init__(self) -> None:
        self.policy_path = Path(DEFAULT_POLICY_PATH)
        self.generated_dir = Path(DEFAULT_GENERATED_DIR)
        self.policy = PolicyAdmin(self.policy_path)
        self.discovery = Discovery(
            nginx_conf_dir=DISCOVERY_NGINX_CONF_DIR,
            yunohost_bin=DISCOVERY_YUNOHOST_BIN,
        )
        self.lock = threading.Lock()

    def apply_runtime(self) -> None:
        subprocess.run(["python3", DEFAULT_RENDER_SCRIPT, str(self.policy_path), str(self.generated_dir)], check=True)
        subprocess.run(["python3", DEFAULT_STAGE_SCRIPT, str(self.generated_dir), DEFAULT_STAGE_ROOT], check=True)
        # Complete the cycle: reinject auth directives, reload nginx, restart Authelia.
        # Runs as root via sudoers since the admin UI service is non-root.
        # Skipped when MFA_SIDECAR_SKIP_ROOT_APPLY=1 (for smoke tests without sudo).
        if os.environ.get("MFA_SIDECAR_SKIP_ROOT_APPLY") == "1":
            return
        apply_helper = str(Path(DEFAULT_INSTALL_DIR) / "bin" / "apply-runtime-as-root")
        subprocess.run(["sudo", apply_helper, DEFAULT_INSTALL_DIR], check=True)

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

    def render_index(self, error: str = "", notice: str = "", edit_entry_id: str = "") -> str:
        summary = self.policy.portal_summary()
        package_version = load_package_version()
        entries = self.policy.list_entries()
        portal_domain = summary.get('portal_domain', '')
        root_domain = extract_root_domain(portal_domain)
        enforcement_enabled = bool(summary.get('enforcement_enabled', True))
        discovered, discovery_error = self.discovered_targets()
        edit_entry = next((entry for entry in entries if entry['id'] == edit_entry_id), None)

        entries_by_pair = {
            (entry['host'], normalize_path(entry.get('path', '/'))): entry
            for entry in entries
        }
        target_rows = []

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
            target_rows.append(
                f"<tr>"
                f"<td>{h(item.get('label', ''))}</td>"
                f"<td><code>{h(item['host'])}</code></td>"
                f"<td><code>{h(path_value)}</code></td>"
                f"<td><code>{h(item.get('app_id', ''))}</code><br><span class='muted'>{h(item.get('target_conf', ''))}</span></td>"
                f"<td><code>{h(upstream_value)}</code></td>"
                f"<td>Bypass (unmanaged)<br><span class='muted'>nginx check: {h(nginx_state)}</span>{warning_html}</td>"
                f"<td>"
                f"<form method='post' action='/admin/discoveries/add' style='display:inline-block;'>"
                f"{common_inputs}"
                f"<input type='hidden' name='enabled' value='true' />"
                f"<button type='submit' onclick=\"{confirm_text}\">Protect</button>"
                f"</form>"
                f"</td>"
                f"</tr>"
            )

        for entry in entries:
            state = "Protect" if entry.get("enabled") else "Bypass"
            action = "Bypass" if entry.get("enabled") else "Protect"
            path_value = normalize_path(entry.get('path', '/'))
            is_danger_target = entry['host'] == portal_domain or (entry['host'] == root_domain and path_value == '/')
            toggle_confirm = ''
            if is_danger_target and not entry.get('enabled'):
                toggle_confirm = "return confirm('Dangerous target. Have you tested MFA Sidecar on a non-root domain first? Enabling protection here can lock you out of services or normal admin access.');"
            warning_html = ""
            if is_danger_target:
                warning_html = "<br><span class='danger-text'>Danger zone: test on a non-root domain first.</span>"
            target_rows.append(
                f"<tr>"
                f"<td>{h(entry.get('label', ''))}</td>"
                f"<td><code>{h(entry['host'])}</code></td>"
                f"<td><code>{h(path_value)}</code></td>"
                f"<td><code>{h(entry['id'])}</code><br><span class='muted'>{h(entry.get('target_conf', ''))}</span></td>"
                f"<td><code>{h(entry['upstream'])}</code></td>"
                f"<td>{h(state)}{warning_html}</td>"
                f"<td>"
                f"<form method='post' action='/admin/entries/{h(entry['id'])}/toggle' style='display:inline-block; margin-right: 0.4rem;'>"
                f"<button type='submit' onclick=\"{toggle_confirm}\">{h(action)}</button>"
                f"</form>"
                f"<form method='get' action='/admin' style='display:inline-block; margin-right: 0.4rem;'>"
                f"<input type='hidden' name='edit' value='{h(entry['id'])}' />"
                f"<button type='submit'>Edit</button>"
                f"</form>"
                f"<form method='post' action='/admin/entries/{h(entry['id'])}/delete' style='display:inline-block;'>"
                f"<button type='submit' onclick=\"return confirm('Delete this managed entry?');\">Delete</button>"
                f"</form>"
                f"</td>"
                f"</tr>"
            )

        targets_html = "\n".join(target_rows) or "<tr><td colspan='7'><em>No discovered or managed app locations yet.</em></td></tr>"

        error_html = f"<div class='error'>{h(error)}</div>" if error else ""
        notice_html = f"<div class='notice'>{h(notice)}</div>" if notice else ""
        discovery_html = f"<div class='error'>Discovery degraded: {h(discovery_error)}</div>" if discovery_error else ""
        disabled_bar = ""
        if not enforcement_enabled:
            disabled_bar = (
                "<div class='error' style='background:#b30000;color:#fff;border-color:#800;'>"
                "<strong>MFA Sidecar is disabled.</strong> Protection is bypassed globally until you re-enable it. "
                "<form method='post' action='/admin/global/enable' style='display:inline-block; margin-left: 0.75rem;'>"
                "<button type='submit' onclick=\"return confirm('Do you really want to re-enable MFA Sidecar enforcement globally? Make sure you have tested on a non-root domain first.');\">Re-enable protection</button>"
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
    input[type=text], select {{ width: 100%; padding: 0.45rem; }}
    .muted {{ color: #555; font-size: 0.92em; }}
    .danger-text {{ color: #900; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>MFA Sidecar admin</h1>
  <p class='muted'>Version <code>{h(package_version)}</code> · Simple operator control plane. Domains come from YunoHost. App subpaths come from YunoHost app inventory. nginx is only a light sanity check for discovered app paths.</p>
  {disabled_bar}
  {notice_html}
  {error_html}
  {discovery_html}

  <h2>Portal summary</h2>
  <ul>
    <li><strong>Portal domain:</strong> <code>{h(summary['portal_domain'])}</code></li>
    <li><strong>Portal path:</strong> <code>{h(summary['portal_path'])}</code></li>
    <li><strong>Remembered session:</strong> <code>{h(summary['remember_me'])}</code></li>
    <li><strong>Default policy:</strong> <code>{h(summary['default_policy'])}</code></li>
    <li><strong>Global enforcement:</strong> <code>{'enabled' if enforcement_enabled else 'disabled'}</code></li>
  </ul>
  <form method='post' action='/admin/global/{'disable' if enforcement_enabled else 'enable'}' style='margin-bottom: 1rem;'>
    <button type='submit' onclick="return confirm('{"Do you really want to disable MFA Sidecar enforcement globally? Existing config will be kept, but all protection will be bypassed until you re-enable it." if enforcement_enabled else "Do you really want to re-enable MFA Sidecar enforcement globally? Make sure you have tested on a non-root domain first."}');">{'Disable sidecar globally' if enforcement_enabled else 'Re-enable sidecar globally'}</button>
  </form>

  <h2>Targets</h2>
  <p class='muted'>One table, one control surface. Discovered YunoHost app locations appear here as unmanaged rows with one-click onboarding. Managed rows stay here too, so manual add lands in the same list with the same controls.</p>
  <table>
    <thead>
      <tr>
        <th>Label</th><th>Host</th><th>Path</th><th>ID / source</th><th>Upstream</th><th>Status</th><th>Action</th>
      </tr>
    </thead>
    <tbody>
      {targets_html}
    </tbody>
  </table>

  <h2>{h(form_title)}</h2>
  <form method='post' action='{h(form_action)}'>
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
        if parsed.path not in {"/", "/admin"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        qs = parse_qs(parsed.query)
        edit_entry_id = qs.get("edit", [""])[0]
        body = APP.render_index(error=qs.get("error", [""])[0], notice=qs.get("notice", [""])[0], edit_entry_id=edit_entry_id)
        payload = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
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
            self.send_error(HTTPStatus.NOT_FOUND)
        except (PolicyError, subprocess.CalledProcessError) as exc:
            self._redirect("/admin?error=" + quote_plus(str(exc)))

    def log_message(self, format: str, *args) -> None:
        return

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def _authorized(self) -> bool:
        return True


if __name__ == "__main__":
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    print(f"MFA Sidecar admin UI listening on http://{BIND_HOST}:{BIND_PORT}")
    server.serve_forever()
