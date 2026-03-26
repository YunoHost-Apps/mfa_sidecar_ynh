#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

TEMPLATE = {
    "users": {
        "admin": {
            "disabled": False,
            "displayname": "MFA Sidecar Admin",
            "password": "REPLACE_WITH_ARGON2_HASH",
            "email": "admin@example.invalid",
            "groups": ["admins"],
        }
    }
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    path = Path(args.target)
    if path.exists() and not args.force:
        print(f"Refusing to overwrite existing file without --force: {path}", file=sys.stderr)
        raise SystemExit(1)

    ensure_parent(path)
    path.write_text(yaml.safe_dump(TEMPLATE, sort_keys=False), encoding="utf-8")
    path.chmod(0o600)
    print(f"Wrote bootstrap Authelia users file template to: {path}")


if __name__ == "__main__":
    main()
