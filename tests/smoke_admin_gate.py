#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_ADMIN = ROOT_DIR / 'src/admin-ui'


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        policy_path = tmpdir / 'domain-policy.yaml'
        policy_path.write_text('access_control:\n  managed_sites: []\nportal:\n  domain: auth.example.tld\n  path: /\nsession:\n  remember_me: 24h\n', encoding='utf-8')

        env = os.environ.copy()
        env['PYTHONPATH'] = str(SRC_ADMIN)
        env['MFA_SIDECAR_POLICY_PATH'] = str(policy_path)
        env['MFA_SIDECAR_ADMIN_GATE_SECRET'] = 'secret123'

        script = """
from app import Handler

class FakeHeaders(dict):
    def get(self, key, default=''):
        return super().get(key, default)

obj = Handler.__new__(Handler)
obj.headers = FakeHeaders({'X-MFA-Sidecar-Admin-Secret': 'secret123'})
assert obj._authorized() is True
obj.headers = FakeHeaders({'X-MFA-Sidecar-Admin-Secret': 'wrong'})
assert obj._authorized() is False
print('ok')
"""
        subprocess.run(['python3', '-c', script], check=True, env=env, cwd=str(SRC_ADMIN))

    print('smoke_admin_gate: ok')


if __name__ == '__main__':
    main()
