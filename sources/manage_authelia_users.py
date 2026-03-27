#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_GROUPS = ["admins"]
MANAGED_MARKER = "managed_by_mfa_sidecar_sync"
DEFAULT_PLACEHOLDER_HASH = "$argon2id$v=19$m=65536,t=3,p=4$YWFhYWFhYWFhYWFhYWFhYQ$2M9QGyGynl3CE4Yd7sQ0Jd0N1k1fA0sQO9L5H5lYv3o"


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
    for line in reversed(lines):
        if line.startswith("Digest: "):
            return line.split("Digest: ", 1)[1].strip()
        if line.startswith("$"):
            return line
    raise SystemExit(f"Authelia hash command returned unexpected output: {lines[-1]}")


def run_json(command: list[str]) -> dict | list:
    if not shutil.which(command[0]):
        raise SystemExit(f"Command not found: {command[0]}")
    proc = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(proc.stdout)


def get_yunohost_users(yunohost_bin: str) -> dict[str, dict[str, str]]:
    payload = run_json([yunohost_bin, "user", "list", "--output-as", "json"])
    users = payload.get("users", {}) if isinstance(payload, dict) else {}
    found: dict[str, dict[str, str]] = {}
    for username, meta in users.items():
        if not isinstance(meta, dict):
            continue
        found[str(username)] = {
            "displayname": str(meta.get("fullname") or username),
            "email": str(meta.get("mail") or ""),
        }
    return found


def ensure_user_record(users: dict, username: str) -> tuple[dict, bool]:
    user = users.get(username)
    if user is None:
        user = {}
        users[username] = user
        return user, True
    return user, False


def command_ensure(args: argparse.Namespace) -> int:
    path = Path(args.users_file)
    data = load_users(path)
    users = data["users"]

    changed = False
    user, created = ensure_user_record(users, args.username)
    changed = changed or created

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


def command_sync_from_yunohost(args: argparse.Namespace) -> int:
    path = Path(args.users_file)
    data = load_users(path)
    users = data["users"]
    upstream = get_yunohost_users(args.yunohost_bin)

    added = 0
    updated = 0
    disabled = 0
    changed = False

    for username, meta in upstream.items():
        user, created = ensure_user_record(users, username)
        if created:
            user.update(
                {
                    "disabled": False,
                    "displayname": meta["displayname"],
                    "password": user.get("password") or DEFAULT_PLACEHOLDER_HASH,
                    "email": meta["email"],
                    "groups": user.get("groups") or args.default_groups,
                    MANAGED_MARKER: True,
                }
            )
            added += 1
            changed = True
            continue

        desired_fields = {
            "displayname": meta["displayname"],
            "email": meta["email"],
            MANAGED_MARKER: True,
        }
        if user.get("disabled") is True:
            user["disabled"] = False
            desired_fields["disabled"] = False
        for key, value in desired_fields.items():
            if user.get(key) != value:
                user[key] = value
                changed = True
        if created is False:
            updated += 1
        if "password" not in user:
            user["password"] = DEFAULT_PLACEHOLDER_HASH
            changed = True
        if "groups" not in user:
            user["groups"] = args.default_groups
            changed = True

    for username, user in users.items():
        if not user.get(MANAGED_MARKER):
            continue
        if username in upstream:
            continue
        if not bool(user.get("disabled", False)):
            user["disabled"] = True
            disabled += 1
            changed = True

    if changed:
        save_users(path, data)

    print(
        f"Synced users from YunoHost into {path}: added={added} updated={updated} disabled={disabled} changed={str(changed).lower()}"
    )
    return 0


def command_list(args: argparse.Namespace) -> int:
    path = Path(args.users_file)
    data = load_users(path)
    for username, meta in sorted(data["users"].items()):
        email = meta.get("email", "")
        groups = ",".join(meta.get("groups", []))
        disabled = str(bool(meta.get("disabled", False))).lower()
        managed = str(bool(meta.get(MANAGED_MARKER, False))).lower()
        print(f"{username}\temail={email}\tdisabled={disabled}\tmanaged={managed}\tgroups={groups}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    ensure = sub.add_parser("ensure-user")
    ensure.add_argument("--users-file", required=True)
    ensure.add_argument("--authelia-bin", default="/opt/yunohost/mfa_sidecar/bin/authelia")
    ensure.add_argument("--username", required=True)
    ensure.add_argument("--display-name", required=True)
    ensure.add_argument("--email", required=True)
    ensure.add_argument("--password", required=True)
    ensure.add_argument("--groups", nargs="+", default=DEFAULT_GROUPS)
    ensure.set_defaults(func=command_ensure)

    sync_cmd = sub.add_parser("sync-from-yunohost")
    sync_cmd.add_argument("--users-file", required=True)
    sync_cmd.add_argument("--yunohost-bin", default="yunohost")
    sync_cmd.add_argument("--default-groups", nargs="+", default=DEFAULT_GROUPS)
    sync_cmd.set_defaults(func=command_sync_from_yunohost)

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
