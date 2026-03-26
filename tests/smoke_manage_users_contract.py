#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'package-base/sources/manage_authelia_users.py'
FAKE_AUTHELIA = ROOT / 'tests/out/fake-authelia'


def main() -> None:
    FAKE_AUTHELIA.write_text(
        "#!/usr/bin/env bash\necho '$argon2id$v=19$m=65536,t=3,p=4$testsalt$testhash'\n",
        encoding='utf-8',
    )
    FAKE_AUTHELIA.chmod(0o755)

    with tempfile.TemporaryDirectory() as tmp:
        users = Path(tmp) / 'users.yml'
        subprocess.run([
            'python3', str(SCRIPT), 'ensure-user',
            '--users-file', str(users),
            '--authelia-bin', str(FAKE_AUTHELIA),
            '--username', 'john',
            '--display-name', 'John Watson',
            '--email', 'john@example.com',
            '--password', 'secret-pass',
            '--groups', 'admins',
        ], check=True)
        data = yaml.safe_load(users.read_text(encoding='utf-8'))
        user = data['users']['john']
        assert user['displayname'] == 'John Watson'
        assert user['email'] == 'john@example.com'
        assert user['groups'] == ['admins']
        assert user['password'].startswith('$argon2id$')

    print('smoke_manage_users_contract: ok')


if __name__ == '__main__':
    main()
