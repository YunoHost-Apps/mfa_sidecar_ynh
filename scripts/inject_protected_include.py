#!/usr/bin/env python3
"""Inject or remove MFA sidecar include lines in nginx conf files."""

from __future__ import annotations

import argparse
from pathlib import Path

MARK_START = "# BEGIN mfa-sidecar managed block"
MARK_END = "# END mfa-sidecar managed block"


def managed_block(include_path: str) -> str:
    return (
        f"{MARK_START}\n"
        f"include {include_path};\n"
        f"{MARK_END}\n"
    )


def inject(conf_path: Path, include_path: str) -> None:
    text = conf_path.read_text(encoding="utf-8")
    block = managed_block(include_path)
    if MARK_START in text and MARK_END in text:
        start = text.index(MARK_START)
        end = text.index(MARK_END) + len(MARK_END)
        text = text[:start] + block.rstrip("\n") + text[end:]
    else:
        stripped = text.rstrip() + "\n\n" + block
        text = stripped
    conf_path.write_text(text, encoding="utf-8")


def remove(conf_path: Path) -> None:
    text = conf_path.read_text(encoding="utf-8")
    if MARK_START not in text or MARK_END not in text:
        return
    start = text.index(MARK_START)
    end = text.index(MARK_END) + len(MARK_END)
    if end < len(text) and text[end:end+1] == "\n":
        end += 1
    text = (text[:start] + text[end:]).rstrip() + "\n"
    conf_path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inject = sub.add_parser("inject")
    p_inject.add_argument("conf")
    p_inject.add_argument("include_path")

    p_remove = sub.add_parser("remove")
    p_remove.add_argument("conf")

    args = parser.parse_args()
    conf = Path(args.conf)

    if args.cmd == "inject":
        inject(conf, args.include_path)
    else:
        remove(conf)


if __name__ == "__main__":
    main()
