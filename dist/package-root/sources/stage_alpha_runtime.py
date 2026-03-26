#!/usr/bin/env python3
"""Stage generated alpha runtime files into a target root/prefix."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def set_mode(path: Path, mode: int) -> None:
    path.chmod(mode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("generated_dir")
    parser.add_argument("prefix")
    args = parser.parse_args()

    generated = Path(args.generated_dir)
    prefix = Path(args.prefix)

    authelia_cfg = generated / "authelia-config.generated.yml"
    metadata = generated / "runtime-metadata.json"
    nginx_dir = generated / "nginx"

    authelia_dst = prefix / "etc/mfa-sidecar/authelia/configuration.yml"
    metadata_dst = prefix / "etc/mfa-sidecar/runtime-metadata.json"
    copy_file(authelia_cfg, authelia_dst)
    copy_file(metadata, metadata_dst)
    set_mode(authelia_dst, 0o640)
    set_mode(metadata_dst, 0o644)

    portal_src = nginx_dir / "portal.generated.conf"
    portal_dst = prefix / "etc/mfa-sidecar/nginx/portal.conf"
    copy_file(portal_src, portal_dst)
    set_mode(portal_dst, 0o644)

    protected_out = prefix / "etc/mfa-sidecar/nginx/protected"
    ensure_dir(protected_out)
    for conf in nginx_dir.glob("*.generated.conf"):
        if conf.name == "portal.generated.conf":
            continue
        target = protected_out / conf.name.replace(".generated", "")
        copy_file(conf, target)
        set_mode(target, 0o644)

    print(f"Staged alpha runtime into: {prefix}")


if __name__ == "__main__":
    main()
