#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'package-base/sources/manage_authelia_users.py'
FAKE_YUNOHOST = ROOT / 'tests/out/fake-yunohost-users'

FAKE_OUTPUT = """#!/usr/bin/env bash
if [[ \"$1 $2\" == \"user list\" ]]; then
  cat <<'EOF'
{"users":{"john":{"fullname":"John Watson","mail":"john@example.com"},"alice":{"fullname":"Alice Example","mail":"alice@example.com"}}}
EOF
  exit 0
fi
exit 1
"""


def main() -> None:
    FAKE_YUNOHOST.write_text(FAKE_OUTPUT, encoding='utf-8')
    FAKE_YUNOHOST.chmod(0o755)

    with tempfile.TemporaryDirectory() as tmp:
        users = Path(tmp) / 'users.yml'
        users.write_text(
            yaml.safe_dump(
                {
                    'users': {
                        'john': {
                            'disabled': True,
                            'displayname': 'Old John',
                            'password': '$argon2id$existing',
                            'email': 'old@example.com',
                            'groups': ['admins'],
                            'managed_by_mfa_sidecar_sync': True,
                        },
                        'orphan': {
                            'disabled': False,
                            'displayname': 'Orphan User',
                            'password': '$argon2id$orphan',
                            'email': 'orphan@example.com',
                            'groups': ['admins'],
                            'managed_by_mfa_sidecar_sync': True,
                        },
                        'manual': {
                            'disabled': False,
                            'displayname': 'Manual User',
                            'password': '$argon2id$manual',
                            'email': 'manual@example.com',
                            'groups': ['admins'],
                        },
                    }
                },
                sort_keys=False,
            ),
            encoding='utf-8',
        )

        subprocess.run([
            'python3', str(SCRIPT), 'sync-from-yunohost',
            '--users-file', str(users),
            '--yunohost-bin', str(FAKE_YUNOHOST),
            '--default-groups', 'admins',
        ], check=True)

        data = yaml.safe_load(users.read_text(encoding='utf-8'))
        john = data['users']['john']
        alice = data['users']['alice']
        orphan = data['users']['orphan']
        manual = data['users']['manual']

        assert john['disabled'] is False
        assert john['displayname'] == 'John Watson'
        assert john['email'] == 'john@example.com'
        assert john['password'] == '$argon2id$existing'

        assert alice['disabled'] is False
        assert alice['displayname'] == 'Alice Example'
        assert alice['email'] == 'alice@example.com'
        assert alice['password'] == 'REPLACE_WITH_ARGON2_HASH'
        assert alice['managed_by_mfa_sidecar_sync'] is True

        assert orphan['disabled'] is True
        assert manual['disabled'] is False

    print('smoke_sync_users_contract: ok')


if __name__ == '__main__':
    main()
