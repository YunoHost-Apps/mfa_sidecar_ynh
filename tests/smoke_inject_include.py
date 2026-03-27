#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'scripts' / 'inject_protected_include.py'
spec = importlib.util.spec_from_file_location('injector', SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding='utf-8')


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        brace_next = root / 'brace-next.conf'
        write(brace_next, '''server {
  location ^~ /nextcloud
  {
    proxy_pass http://127.0.0.1:3000;
  }
}
''')
        module.inject_into_location(brace_next, '/nextcloud', '/authelia-auth-nextcloud', 'auth.example.tld')
        text = read(brace_next)
        assert 'auth_request /authelia-auth-nextcloud;' in text
        assert 'proxy_pass http://127.0.0.1:3000;' in text

        quoted = root / 'quoted.conf'
        write(quoted, '''server {
  location ^~ "/nc" {
    proxy_pass http://127.0.0.1:3001;
  }
}
''')
        module.inject_into_location(quoted, '/nc', '/authelia-auth-nc', 'auth.example.tld')
        text = read(quoted)
        assert 'auth_request /authelia-auth-nc;' in text
        assert 'proxy_pass http://127.0.0.1:3001;' in text

        ambiguous = root / 'ambiguous.conf'
        write(ambiguous, '''server {
  location /same {
    proxy_pass http://127.0.0.1:3000;
  }
  location ^~ /same {
    proxy_pass http://127.0.0.1:3001;
  }
}
''')
        try:
            module.inject_into_location(ambiguous, '/same', '/authelia-auth-same', 'auth.example.tld')
        except module.InjectionError as exc:
            assert 'ambiguous' in str(exc)
        else:
            raise AssertionError('Expected ambiguous match failure')

        missing = root / 'missing.conf'
        write(missing, 'server {\n  location /else { return 200; }\n}\n')
        try:
            module.inject_into_location(missing, '/nope', '/authelia-auth-nope', 'auth.example.tld')
        except module.InjectionError as exc:
            assert 'no matching location block' in str(exc)
        else:
            raise AssertionError('Expected missing location failure')

    print('smoke_inject_include.py: ok')


if __name__ == '__main__':
    main()
