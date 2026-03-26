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

    print(f"Staged alpha runtime into: {prefix}")


if __name__ == "__main__":
    main()
