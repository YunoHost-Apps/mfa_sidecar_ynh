#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_ADMIN = ROOT_DIR / "src/admin-ui"
RENDER_SCRIPT = ROOT_DIR / "src/config-render/render_alpha_config.py"
STAGE_SCRIPT = ROOT_DIR / "scripts/stage_alpha_runtime.py"


def write_policy(path: Path) -> None:
    path.write_text(
        """version: 1
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
    display_name: MFA Sidecar
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
      label: Root site
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
""",
        encoding="utf-8",
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        policy_path = tmpdir / "domain-policy.yaml"
        generated_dir = tmpdir / "generated"
        stage_root = tmpdir / "stage"
        write_policy(policy_path)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_ADMIN)
        env["MFA_SIDECAR_POLICY_PATH"] = str(policy_path)
        env["MFA_SIDECAR_RENDER_SCRIPT"] = str(RENDER_SCRIPT)
        env["MFA_SIDECAR_STAGE_SCRIPT"] = str(STAGE_SCRIPT)
        env["MFA_SIDECAR_GENERATED_DIR"] = str(generated_dir)
        env["MFA_SIDECAR_STAGE_ROOT"] = str(stage_root)
        env["MFA_SIDECAR_DISCOVERY_YUNOHOST_BIN"] = str(ROOT_DIR / 'tests/fake-yunohost')
        env["MFA_SIDECAR_DISCOVERY_NGINX_CONF_DIR"] = str(tmpdir / 'etc/nginx/conf.d')

        (tmpdir / 'etc/nginx/conf.d/wm3v.com.d').mkdir(parents=True, exist_ok=True)
        (tmpdir / 'etc/nginx/conf.d/wm3v.com.d/root.conf').write_text('location /kanboard {\n}\n', encoding='utf-8')

        script = """
from app import AdminApp
app = AdminApp()
discovered, err = app.discovered_targets()
assert not err, err
kanboard = next(item for item in discovered if item['host'] == 'wm3v.com' and item['path'] == '/kanboard')
assert kanboard['nginx_present'] is True
assert kanboard['suggested_upstream'] == 'https://127.0.0.1:443'
app.add_entry_and_apply(host='wm3v.com', path='/kanboard', label='Kanboard', upstream='https://127.0.0.1:443', enabled=False)
app.update_entry_and_apply(entry_id='wm3v-com-kanboard', host='wm3v.com', path='/kanboard', label='Kanboard Admin', upstream='https://127.0.0.1:444', enabled=True)
app.toggle_entry_and_apply('wm3v-com-kanboard')
app.delete_entry_and_apply('wm3v-com-kanboard')
print('ok')
"""
        subprocess.run(["python3", "-c", script], check=True, env=env, cwd=str(SRC_ADMIN))

        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        entries = policy["access_control"]["managed_sites"]
        assert all(entry["id"] != "wm3v-com-kanboard" for entry in entries)

        assert (generated_dir / "authelia-config.generated.yml").exists()
        assert (stage_root / "etc/mfa-sidecar/authelia/configuration.yml").exists()
        assert (stage_root / "etc/mfa-sidecar/nginx/protected/wm3v-com-kanboard.conf").exists()

    print("smoke_admin_ui: ok")


if __name__ == "__main__":
    main()
