#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_GROUPS = ["admins"]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_users(path: Path) -> dict:
    if not path.exists():
        return {"users": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid users file root in {path}")
    data.setdefault("users", {})
    if not isinstance(data["users"], dict):
        raise SystemExit(f"Invalid users map in {path}")
    return data


def save_users(path: Path, data: dict) -> None:
    ensure_parent(path)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    path.chmod(0o600)


def hash_password(authelia_bin: str, password: str) -> str:
    proc = subprocess.run(
        [authelia_bin, "crypto", "hash", "generate", "argon2", "--password", password, "--no-confirm"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise SystemExit("Authelia hash command returned no output")
    return lines[-1]


def command_ensure(args: argparse.Namespace) -> int:
    path = Path(args.users_file)
    data = load_users(path)
    users = data["users"]

    changed = False
    user = users.get(args.username)
    if user is None:
        user = {}
        users[args.username] = user
        changed = True

    password_hash = hash_password(args.authelia_bin, args.password)
    desired = {
        "disabled": False,
        "displayname": args.display_name,
        "password": password_hash,
        "email": args.email,
        "groups": args.groups,
    }
    for key, value in desired.items():
        if user.get(key) != value:
            user[key] = value
            changed = True

    if changed:
        save_users(path, data)
        print(f"Updated user '{args.username}' in {path}")
    else:
        print(f"User '{args.username}' already up to date in {path}")
    return 0


def command_list(args: argparse.Namespace) -> int:
    path = Path(args.users_file)
    data = load_users(path)
    for username, meta in sorted(data["users"].items()):
        email = meta.get("email", "")
        groups = ",".join(meta.get("groups", []))
        disabled = str(bool(meta.get("disabled", False))).lower()
        print(f"{username}\temail={email}\tdisabled={disabled}\tgroups={groups}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    ensure = sub.add_parser("ensure-user")
    ensure.add_argument("--users-file", required=True)
    ensure.add_argument("--authelia-bin", default="/usr/local/bin/authelia")
    ensure.add_argument("--username", required=True)
    ensure.add_argument("--display-name", required=True)
    ensure.add_argument("--email", required=True)
    ensure.add_argument("--password", required=True)
    ensure.add_argument("--groups", nargs="+", default=DEFAULT_GROUPS)
    ensure.set_defaults(func=command_ensure)

    list_cmd = sub.add_parser("list-users")
    list_cmd.add_argument("--users-file", required=True)
    list_cmd.set_defaults(func=command_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
