#!/usr/bin/env python3
"""Install vendored Authelia artifact with sha256 verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_release(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def extract_binary(archive: Path, out_path: Path) -> None:
    with tarfile.open(archive, 'r:gz') as tf:
        members = [m for m in tf.getmembers() if m.isfile() and Path(m.name).name == 'authelia']
        if not members:
            raise SystemExit('authelia binary not found in vendored archive')
        member = members[0]
        with tf.extractfile(member) as src, out_path.open('wb') as dst:
            shutil.copyfileobj(src, dst)
    out_path.chmod(0o755)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('release_json')
    parser.add_argument('vendor_dir')
    parser.add_argument('output_dir')
    args = parser.parse_args()

    release = load_release(Path(args.release_json))
    vendor_dir = Path(args.vendor_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    archive = vendor_dir / release['asset']
    if not archive.exists():
        raise SystemExit(f'vendored archive missing: {archive}')

    actual = sha256_file(archive)
    expected = release['sha256']
    if actual != expected:
        raise SystemExit(f'sha256 mismatch: expected {expected} got {actual}')

    binary = out_dir / 'authelia'
    extract_binary(archive, binary)

    result = {
        'version': release['version'],
        'archive': str(archive),
        'binary': str(binary),
        'sha256': actual,
        'verified': True,
        'source': 'vendor',
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
