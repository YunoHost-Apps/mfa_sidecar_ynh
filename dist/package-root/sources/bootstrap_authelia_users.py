#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

TEMPLATE = {
    "users": {
        "admin-bootstrap": {
            "disabled": True,
            "displayname": "MFA Sidecar Bootstrap Placeholder",
            "password": "$argon2id$v=19$m=65536,t=3,p=4$YWFhYWFhYWFhYWFhYWFhYQ$2M9QGyGynl3CE4Yd7sQ0Jd0N1k1fA0sQO9L5H5lYv3o",
            "email": "admin@example.invalid",
            "groups": ["admins"],
            "note": "Replace this disabled bootstrap placeholder with a real first user via the YunoHost config panel before meaningful auth use.",
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
