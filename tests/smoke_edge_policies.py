#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / 'src' / 'config-render' / 'render_alpha_config.py'
OUT = ROOT / 'tests' / 'out' / 'edge-policies'

BASE_POLICY = {
    'version': 1,
    'portal': {
        'domain': 'auth.example.tld',
        'path': '/',
        'default_redirect_url': 'https://yunohost.example.tld/',
        'listen': {'host': '127.0.0.1', 'port': 9091},
    },
    'session': {
        'name': 'mfa_sidecar_session',
        'secret_file': '/etc/mfa-sidecar/secrets/session_secret',
        'expiration': '24h',
        'inactivity': '1h',
        'remember_me': '24h',
    },
    'storage': {'encryption_key_file': '/etc/mfa-sidecar/secrets/storage_encryption_key'},
    'identity': {
        'display_name': 'MFA Sidecar',
        'local': {
            'path': '/etc/mfa-sidecar/authelia/users.yml',
            'watch': False,
            'search': {'email': True, 'case_insensitive': True},
            'password': {
                'algorithm': 'argon2',
                'argon2': {
                    'variant': 'argon2id',
                    'iterations': 3,
                    'memory': 65536,
                    'parallelism': 4,
                    'key_length': 32,
                    'salt_length': 16,
                },
            },
        },
        'sync': {
            'enabled': False,
            'source': 'yunohost-ldap-readonly',
            'fields': ['username', 'email'],
        },
    },
    'mfa': {
        'issuer': 'MFA Sidecar',
        'webauthn': {
            'enabled': True,
            'display_name': 'YunoHost MFA',
            'attestation_conveyance_preference': 'indirect',
            'user_verification': 'preferred',
            'timeout': '60s',
        },
        'totp': {'enabled': True, 'issuer': 'MFA Sidecar'},
    },
    'access_control': {
        'default_policy': 'bypass',
        'managed_sites': [
            {'id': 'root_site', 'host': 'wm3v.com', 'path': '/', 'enabled': True, 'upstream': 'https://127.0.0.1:8443'},
            {'id': 'nextcloud_exception', 'host': 'wm3v.com', 'path': '/nextcloud', 'enabled': False, 'upstream': 'https://127.0.0.1:8443'},
            {'id': 'homebox', 'host': 'home.example.tld', 'path': '/', 'enabled': False, 'upstream': 'http://127.0.0.1:3000'},
        ],
    },
    'recovery': {'mode': 'authelia-reset-password-and-enrollment', 'disable_reset': False},
    'alpha': {'generate_nginx_snippets': True, 'generate_authelia_config': True, 'enforce_tls_upstream_verification': False},
}

CASES = {
    'env-secrets': BASE_POLICY,
    'nested-overrides': {
        **BASE_POLICY,
        'access_control': {
            'default_policy': 'bypass',
            'managed_sites': [
                {'id': 'root_site', 'host': 'wm3v.com', 'path': '/', 'enabled': True, 'upstream': 'https://127.0.0.1:8443'},
                {'id': 'nextcloud_exception', 'host': 'wm3v.com', 'path': '/nextcloud', 'enabled': False, 'upstream': 'https://127.0.0.1:8443'},
                {'id': 'deeper_override', 'host': 'wm3v.com', 'path': '/nextcloud/apps/files/morestuff', 'enabled': True, 'upstream': 'https://127.0.0.1:8443'},
            ],
        },
    },
    'reset-disabled': {
        **BASE_POLICY,
        'recovery': {'mode': 'manual-admin-reset', 'disable_reset': True},
    },
}


def run_case(name: str, policy: dict) -> None:
    case_dir = OUT / name
    case_dir.mkdir(parents=True, exist_ok=True)
    policy_path = case_dir / 'policy.yaml'
    policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding='utf-8')
    subprocess.run(['python3', str(RENDER), str(policy_path), str(case_dir / 'rendered')], check=True)

    rendered = case_dir / 'rendered'
    authelia = yaml.safe_load((rendered / 'authelia-config.generated.yml').read_text(encoding='utf-8'))
    metadata = json.loads((rendered / 'runtime-metadata.json').read_text(encoding='utf-8'))

    assert (rendered / 'nginx' / 'portal.generated.conf').exists()
    assert authelia['server']['address'].startswith('tcp://127.0.0.1:')
    assert metadata['portal_domain'].endswith('.tld')
    assert metadata['identity']['backend'] == 'file'
    assert metadata['identity']['user_database_path'] == '/etc/mfa-sidecar/authelia/users.yml'

    if name == 'reset-disabled':
        assert authelia['identity_validation']['reset_password']['disable'] is True
    if name == 'nested-overrides':
        rules = authelia['access_control']['rules']
        assert len(rules) == 3
        deeper = next(rule for rule in rules if rule.get('resources') == ['^/nextcloud/apps/files/morestuff([/?].*)?$'])
        exception = next(rule for rule in rules if rule.get('resources') == ['^/nextcloud([/?].*)?$'])
        root = next(rule for rule in rules if rule.get('domain') == 'wm3v.com' and 'resources' not in rule)
        assert deeper['policy'] == 'two_factor'
        assert exception['policy'] == 'bypass'
        assert root['policy'] == 'two_factor'
        assert (rendered / 'nginx' / 'deeper_override.generated.conf').exists()


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, policy in CASES.items():
        run_case(name, policy)
    print('smoke_edge_policies: ok')


if __name__ == '__main__':
    main()
