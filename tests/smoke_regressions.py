#!/usr/bin/env python3
"""Focused regression smokes for MFA Sidecar.

These tests exist specifically to keep us from refighting the live dragons we
already met on wm3v:
- missing auth-request headers / wrong redirect handoff
- SSOwat hijacking internal auth subrequests
- protected snippet generation missing after upgrade/apply
- WebAuthn default confusion during first-run enrollment
- packaging breakage from missing shipped files/assets/licenses
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "sources"
SCRIPTS = REPO / "scripts"
ASSETS = REPO / "assets"
DOCS = REPO / "docs"
LICENSES = REPO / "licenses"
FIXTURES = REPO / "tests" / "fixtures"


def load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


render = load_module("render_runtime_config", SOURCES / "render_runtime_config.py")
inject = load_module("inject_protected_include", SOURCES / "inject_protected_include.py")
stage_runtime = load_module("stage_runtime", SOURCES / "stage_runtime.py")


def sample_policy() -> dict:
    return {
        "portal": {
            "domain": "auth.domain.tld",
            "path": "/",
            "listen": {"host": "127.0.0.1", "port": 9091},
        },
        "session": {
            "name": "mfa_sidecar_session",
            "secret_file": "/etc/mfa-sidecar/secrets/session_secret",
            "expiration": "1h",
            "inactivity": "5m",
            "remember_me": "24h",
            "cookie_domain": "",
        },
        "storage": {
            "encryption_key_file": "/etc/mfa-sidecar/secrets/storage_encryption_key",
        },
        "identity": {
            "local": {
                "path": "/etc/mfa-sidecar/authelia/users.yml",
                "watch": False,
                "search": {"email": True, "case_insensitive": True},
                "password": {
                    "algorithm": "argon2",
                    "argon2": {
                        "variant": "argon2id",
                        "iterations": 3,
                        "memory": 65536,
                        "parallelism": 4,
                        "key_length": 32,
                        "salt_length": 16,
                    },
                },
            },
            "sync": {"enabled": False, "source": "yunohost-ldap-readonly", "fields": ["username", "email"]},
        },
        "mfa": {
            "issuer": "MFA Sidecar",
            "webauthn": {
                "enabled": False,
                "display_name": "MFA Sidecar",
                "attestation_conveyance_preference": "indirect",
                "user_verification": "preferred",
                "timeout": "60s",
            },
            "totp": {"enabled": True, "issuer": "MFA Sidecar"},
        },
        "access_control": {
            "default_policy": "open",
            "enforcement_enabled": True,
            "managed_sites": [
                {
                    "id": "home-domain-tld",
                    "label": "HomeBox",
                    "host": "home.domain.tld",
                    "path": "/",
                    "enabled": True,
                    "upstream": "http://127.0.0.1:59150",
                    "target_conf": "/etc/nginx/conf.d/home.domain.tld.d/homebox.conf",
                }
            ],
        },
        "recovery": {"mode": "authelia-reset-password-and-enrollment", "disable_reset": False},
        "runtime": {"generate_nginx_snippets": True, "generate_authelia_config": True, "enforce_tls_upstream_verification": False},
    }


class RenderAuthRequestTests(unittest.TestCase):
    def test_auth_endpoint_contains_required_authelia_headers(self):
        conf = render.build_nginx_auth_endpoint_conf(
            sample_policy()["access_control"]["managed_sites"][0],
            "http://127.0.0.1:9091/api/authz/auth-request",
            enforcement_enabled=True,
        )
        self.assertIn('access_by_lua_block { return; }', conf)
        self.assertIn('proxy_set_header Connection "";', conf)
        self.assertIn('proxy_set_header X-Original-Method $request_method;', conf)
        self.assertIn('proxy_set_header X-Forwarded-For $remote_addr;', conf)
        self.assertIn('proxy_set_header X-Forwarded-Host $http_host;', conf)
        self.assertNotIn('proxy_set_header X-Real-IP $remote_addr;', conf)

    def test_webauthn_disabled_renders_to_authelia_disable_true(self):
        values = render.build_authelia_values(sample_policy())
        self.assertTrue(values["webauthn"]["disable"])
        self.assertEqual(values["totp"]["issuer"], "MFA Sidecar")

    def test_runtime_index_splits_enabled_and_disabled(self):
        policy = sample_policy()
        index = render.build_index(policy)
        self.assertTrue(index["enforcement_enabled"])
        self.assertEqual(len(index["enabled"]), 1)
        self.assertEqual(index["enabled"][0]["host"], "home.domain.tld")
        self.assertEqual(index["enabled"][0]["target_conf"], "/etc/nginx/conf.d/home.domain.tld.d/homebox.conf")

    def test_render_writes_protected_snippet_for_enabled_managed_site(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.yaml"
            out_dir = Path(td) / "out"
            policy_path.write_text(yaml.safe_dump(sample_policy(), sort_keys=False), encoding="utf-8")
            render.render(policy_path, out_dir)
            snippet = out_dir / "nginx" / "home-domain-tld.generated.conf"
            self.assertTrue(snippet.exists(), "expected protected nginx auth snippet to be generated")
            text = snippet.read_text(encoding="utf-8")
            self.assertIn('access_by_lua_block { return; }', text)
            self.assertIn('X-Original-Method $request_method', text)

    def test_fixture_existing_policy_with_webauthn_enabled_renders_disable_false(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "out"
            fixture = FIXTURES / "policy_webauthn_enabled.yaml"
            render.render(fixture, out_dir)
            cfg = yaml.safe_load((out_dir / "authelia-config.generated.yml").read_text(encoding="utf-8"))
            self.assertFalse(cfg["webauthn"]["disable"])
            self.assertEqual(cfg["totp"]["issuer"], "MFA Sidecar")


class StageRuntimeTests(unittest.TestCase):
    def test_stage_runtime_copies_render_index_into_live_etc_tree(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            generated = base / 'generated'
            out = base / 'staged'
            (generated / 'nginx').mkdir(parents=True)
            (generated / 'authelia-config.generated.yml').write_text('server: {}\n', encoding='utf-8')
            (generated / 'runtime-metadata.json').write_text('{"enforcement_enabled": true}\n', encoding='utf-8')
            (generated / 'render-index.json').write_text('{"enabled": []}\n', encoding='utf-8')
            (generated / 'nginx' / 'portal.generated.conf').write_text('location / {}\n', encoding='utf-8')
            stage_runtime.main.__globals__['resolve_ids'] = lambda owner, group: (None, None)
            subprocess.run([
                'python3', str(SOURCES / 'stage_runtime.py'), str(generated), str(out)
            ], check=True)
            self.assertTrue((out / 'etc/mfa-sidecar/render-index.json').exists())


class InjectorTests(unittest.TestCase):
    def test_managed_auth_block_uses_authelia_redirect_header(self):
        block = inject.managed_auth_block('/authelia-auth-home-domain-tld', 'auth.domain.tld')
        self.assertIn('auth_request_set $redirection_url $upstream_http_location;', block)
        self.assertIn('error_page 401 =302 $redirection_url;', block)
        self.assertNotIn('https://auth.domain.tld/?rd=', block)

    def test_inject_into_location_adds_managed_auth_block(self):
        with tempfile.TemporaryDirectory() as td:
            conf = Path(td) / 'homebox.conf'
            conf.write_text("location / {\n  proxy_pass http://127.0.0.1:59150/;\n}\n", encoding='utf-8')
            inject.inject_into_location(conf, '/', '/authelia-auth-home-domain-tld', 'auth.domain.tld')
            text = conf.read_text(encoding='utf-8')
            self.assertIn('auth_request /authelia-auth-home-domain-tld;', text)
            self.assertIn('auth_request_set $redirection_url $upstream_http_location;', text)

    def test_reinject_all_applies_enabled_targets_from_render_index(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target_conf = base / 'homebox.conf'
            target_conf.write_text("location / {\n  proxy_pass http://127.0.0.1:59150/;\n}\n", encoding='utf-8')
            render_index = {
                'enabled': [
                    {
                        'id': 'home-domain-tld',
                        'target_conf': str(target_conf),
                        'auth_location': '/authelia-auth-home-domain-tld',
                        'portal_domain': 'auth.domain.tld',
                        'path': '/',
                    }
                ]
            }
            idx = base / 'render-index.json'
            idx.write_text(json.dumps(render_index), encoding='utf-8')
            inject.reinject_all(idx, base)
            text = target_conf.read_text(encoding='utf-8')
            self.assertIn('BEGIN mfa-sidecar managed block', text)
            self.assertIn('auth_request_set $redirection_url $upstream_http_location;', text)

    def test_reinject_all_fails_if_any_managed_target_cannot_be_injected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            render_index = {
                'enabled': [
                    {
                        'id': 'missing-home',
                        'target_conf': str(base / 'missing.conf'),
                        'auth_location': '/authelia-auth-home-domain-tld',
                        'portal_domain': 'auth.domain.tld',
                        'path': '/',
                    }
                ]
            }
            idx = base / 'render-index.json'
            idx.write_text(json.dumps(render_index), encoding='utf-8')
            with self.assertRaises(SystemExit):
                inject.reinject_all(idx, base)


class AdminUiHardeningTests(unittest.TestCase):
    def test_admin_ui_contains_csrf_cookie_and_validation(self):
        text = (SOURCES / 'admin_ui_app.py').read_text(encoding='utf-8')
        self.assertIn('CSRF_COOKIE_NAME = "mfa_sidecar_admin_csrf"', text)
        self.assertIn('Set-Cookie", f"{CSRF_COOKIE_NAME}={APP.csrf_token}; Path=/; HttpOnly; SameSite=Strict"', text)
        self.assertIn('invalid CSRF token', text)

    def test_admin_ui_has_clear_break_glass_warning_and_reenable_path(self):
        text = (SOURCES / 'admin_ui_app.py').read_text(encoding='utf-8')
        self.assertIn('Emergency bypass is ACTIVE.', text)
        self.assertIn('MFA Sidecar enforcement is disabled globally', text)
        self.assertIn('Re-enable global protection now', text)
        self.assertIn('Disable global protection (break-glass)', text)
        self.assertIn("disabled (emergency bypass active)", text)
        self.assertIn("action='/admin/global/enable'", text)

    def test_admin_ui_prefers_live_runtime_state_and_warns_on_mismatch(self):
        text = (SOURCES / 'admin_ui_app.py').read_text(encoding='utf-8')
        self.assertIn('load_live_runtime_metadata', text)
        self.assertIn('Live/runtime mismatch.', text)
        self.assertIn('Live global enforcement:', text)
        self.assertIn('Policy intent:', text)

    def test_admin_ui_logs_subprocess_failures_and_does_not_leak_raw_exception_text(self):
        text = (SOURCES / 'admin_ui_app.py').read_text(encoding='utf-8')
        self.assertIn('capture_output=True, text=True', text)
        self.assertIn('mfa-sidecar admin apply failed stderr:', text)
        self.assertIn('mfa-sidecar admin apply failed stdout:', text)
        self.assertIn('Apply failed. Live enforcement may not match policy intent yet.', text)
        self.assertNotIn("quote_plus(f\"Command ['sudo',", text)
        self.assertNotIn("returned non-zero exit status", text)

    def test_password_hashing_no_longer_uses_password_argv(self):
        text = (SOURCES / 'manage_authelia_users.py').read_text(encoding='utf-8')
        self.assertIn('pty.openpty()', text)
        self.assertNotIn('--password", password', text)


class ApplyRuntimeHookTests(unittest.TestCase):
    def test_apply_runtime_hook_renders_stages_and_uses_staged_render_index(self):
        text = (SOURCES / 'hooks' / 'apply-runtime-as-root').read_text(encoding='utf-8')
        self.assertIn('POLICY_PATH="$INSTALL_DIR/config/domain-policy.yaml"', text)
        self.assertIn('GENERATED_DIR="$INSTALL_DIR/deploy/generated-runtime"', text)
        self.assertIn('python3 "$RENDER_SCRIPT" "$POLICY_PATH" "$GENERATED_DIR"', text)
        self.assertIn('python3 "$STAGE_SCRIPT" "$GENERATED_DIR" / --owner mfa_sidecar --group mfa_sidecar', text)
        self.assertIn('--owner mfa_sidecar', text)
        self.assertIn('--group mfa_sidecar', text)
        self.assertIn('RENDER_INDEX="/etc/mfa-sidecar/render-index.json"', text)
        self.assertIn('staged render index missing', text)
        self.assertNotIn('reinject-all "$RENDER_INDEX" --protected-dir "$PROTECTED_DIR" || true', text)
        self.assertIn('nginx -t', text)
        self.assertIn('systemctl reload nginx', text)

    def test_admin_ui_apply_runtime_uses_single_root_side_apply_by_default(self):
        text = (SOURCES / 'admin_ui_app.py').read_text(encoding='utf-8')
        self.assertIn('if os.environ.get("MFA_SIDECAR_SKIP_ROOT_APPLY") == "1":', text)
        self.assertIn('subprocess.run(["sudo", apply_helper, DEFAULT_INSTALL_DIR], check=True, capture_output=True, text=True)', text)

    def test_admin_service_does_not_hardcode_brittle_mount_namespace_paths(self):
        text = (SOURCES / 'mfa-sidecar-admin.service').read_text(encoding='utf-8')
        self.assertIn('PrivateTmp=true', text)
        self.assertIn('ProtectHome=true', text)
        self.assertNotIn('ProtectSystem=strict', text)
        self.assertNotIn('ReadWritePaths=', text)
        self.assertNotIn('/var/cache/nginx', text)


class PackagingPathTests(unittest.TestCase):
    def _shell_text(self, path: Path) -> str:
        return path.read_text(encoding='utf-8')

    def test_install_upgrade_restore_and_config_use_script_dir_anchored_repo_paths(self):
        for script in (SCRIPTS / 'install', SCRIPTS / 'upgrade', SCRIPTS / 'restore', SCRIPTS / 'config'):
            text = self._shell_text(script)
            self.assertIn('SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"', text)
        common = self._shell_text(SCRIPTS / '_common.sh')
        self.assertIn('_mfa_sidecar_pkg_path', common)
        self.assertIn('BASH_SOURCE[0]', common)
        self.assertNotIn('script_base="${SCRIPT_DIR:-$(pwd)}"', common)
        self.assertNotRegex(common, r'install -D -m \d+ \.\./')

    def test_expected_docs_and_license_files_exist(self):
        expected = [
            REPO / 'README.md',
            REPO / 'LICENSE',
            REPO / 'THIRD_PARTY_NOTICES.md',
            DOCS / 'INSTALL.md',
            DOCS / 'ADMIN.md',
            DOCS / 'USERS.md',
            DOCS / 'TROUBLESHOOTING.md',
            DOCS / 'TESTING.md',
            DOCS / 'LIVE-BOX-VERIFICATION.md',
            DOCS / 'SECURITY-NOTES.md',
            DOCS / 'RESTORE-REMOVE.md',
            DOCS / 'SUBMISSION-NOTES.md',
            DOCS / 'RELEASE-GATES.md',
            LICENSES / 'Authelia-Apache-2.0.txt',
            FIXTURES / 'policy_webauthn_enabled.yaml',
        ]
        for path in expected:
            self.assertTrue(path.exists(), f'missing expected packaged file: {path.relative_to(REPO)}')

    def test_logo_compatibility_asset_exists(self):
        self.assertTrue((ASSETS / 'logo.png').exists() or (ASSETS / 'logo.jpg').exists())


if __name__ == '__main__':
    unittest.main()
