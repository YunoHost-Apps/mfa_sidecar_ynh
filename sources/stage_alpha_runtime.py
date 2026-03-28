#!/usr/bin/env python3
"""Stage generated runtime files into a target root/prefix."""

from __future__ import annotations

import argparse
import os
import pwd
import grp
import shutil
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def resolve_ids(owner: str | None, group: str | None) -> tuple[int | None, int | None]:
    uid = pwd.getpwnam(owner).pw_uid if owner else None
    gid = grp.getgrnam(group).gr_gid if group else None
    return uid, gid


def apply_tree_permissions(prefix: Path, owner: str | None, group: str | None) -> None:
    uid, gid = resolve_ids(owner, group)

    directory_modes = {
        prefix / "etc/mfa-sidecar": 0o750,
        prefix / "etc/mfa-sidecar/authelia": 0o750,
        prefix / "etc/mfa-sidecar/nginx": 0o750,
        prefix / "etc/mfa-sidecar/nginx/protected": 0o750,
    }
    file_modes = {
        prefix / "etc/mfa-sidecar/authelia/configuration.yml": 0o640,
        prefix / "etc/mfa-sidecar/runtime-metadata.json": 0o640,
        prefix / "etc/mfa-sidecar/nginx/portal.conf": 0o640,
    }

    for path, mode in directory_modes.items():
        if path.exists():
            path.chmod(mode)
            if uid is not None or gid is not None:
                os.chown(path, -1 if uid is None else uid, -1 if gid is None else gid)

    protected_dir = prefix / "etc/mfa-sidecar/nginx/protected"
    if protected_dir.exists():
        for conf in protected_dir.glob("*.conf"):
            conf.chmod(0o640)
            if uid is not None or gid is not None:
                os.chown(conf, -1 if uid is None else uid, -1 if gid is None else gid)

    for path, mode in file_modes.items():
        if path.exists():
            path.chmod(mode)
            if uid is not None or gid is not None:
                os.chown(path, -1 if uid is None else uid, -1 if gid is None else gid)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("generated_dir")
    parser.add_argument("prefix")
    parser.add_argument("--owner")
    parser.add_argument("--group")
    args = parser.parse_args()

    generated = Path(args.generated_dir)
    prefix = Path(args.prefix)

    authelia_cfg = generated / "authelia-config.generated.yml"
    metadata = generated / "runtime-metadata.json"
    nginx_dir = generated / "nginx"

    copy_file(authelia_cfg, prefix / "etc/mfa-sidecar/authelia/configuration.yml")
    copy_file(metadata, prefix / "etc/mfa-sidecar/runtime-metadata.json")

    portal_src = nginx_dir / "portal.generated.conf"
    copy_file(portal_src, prefix / "etc/mfa-sidecar/nginx/portal.conf")

    protected_out = prefix / "etc/mfa-sidecar/nginx/protected"
    ensure_dir(protected_out)
    for conf in nginx_dir.glob("*.generated.conf"):
        if conf.name == "portal.generated.conf":
            continue
        copy_file(conf, protected_out / conf.name.replace(".generated", ""))

    apply_tree_permissions(prefix, args.owner, args.group)

    print(f"Staged runtime into: {prefix}")


if __name__ == "__main__":
    main()
