#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / 'src/admin-ui'))

from discovery import Discovery


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nginx_dir = root / 'etc/nginx/conf.d'

        write(nginx_dir / 'wm3v.com.d' / 'apps.conf', 'location /nextcloud {\n}\nlocation /kanboard {\n}\n')
        write(nginx_dir / 'home.wm3v.com.d' / 'homebox.conf', 'location / {\n}\n')

        fake_bin = ROOT_DIR / 'tests/fake-yunohost'
        fake_bin.chmod(0o755)

        discovery = Discovery(
            nginx_conf_dir=nginx_dir,
            yunohost_bin=str(fake_bin),
        )
        result = discovery.discover()
        suggestions = result['suggestions']
        by_key = {(item['host'], item['path'], item['kind']): item for item in suggestions}

        assert result['domain_source'] == 'yunohost-cli'
        assert result['app_source'] == 'yunohost-cli'
        assert ('wm3v.com', '/', 'domain') in by_key
        assert ('home.wm3v.com', '/', 'domain') in by_key
        assert ('wm3v.com', '/nextcloud', 'app-path') in by_key
        assert ('wm3v.com', '/kanboard', 'app-path') in by_key
        assert ('home.wm3v.com', '/', 'app-path') not in by_key
        assert by_key[('wm3v.com', '/nextcloud', 'app-path')]['nginx_present'] is True
        assert by_key[('wm3v.com', '/kanboard', 'app-path')]['nginx_present'] is True
        assert by_key[('wm3v.com', '/nextcloud', 'app-path')]['suggested_upstream'] == 'https://127.0.0.1:443'

    print('smoke_discovery: ok')


if __name__ == '__main__':
    main()
