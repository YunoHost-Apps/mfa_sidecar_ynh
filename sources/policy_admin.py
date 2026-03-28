#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yaml

HOST_RE = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(\.([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$")
ENTRY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class PolicyError(ValueError):
    pass


def normalize_path(value: str) -> str:
    value = (value or "/").strip()
    if not value:
        return "/"
    if not value.startswith("/"):
        value = "/" + value
    if len(value) > 1 and value.endswith("/"):
        value = value[:-1]
    return value


def validate_host(host: str) -> str:
    host = (host or "").strip().lower()
    if not host or not HOST_RE.match(host):
        raise PolicyError("host must be a valid DNS name")
    return host


def validate_upstream(upstream: str) -> str:
    upstream = (upstream or "").strip()
    parsed = urlparse(upstream)
    if parsed.scheme not in {"http", "https"}:
        raise PolicyError("upstream must start with http:// or https://")
    if not parsed.hostname:
        raise PolicyError("upstream must include a hostname")
    if parsed.path not in {"", "/"}:
        raise PolicyError("upstream must be host+port only for alpha")
    return upstream.rstrip("/")


def validate_entry_id(entry_id: str) -> str:
    entry_id = (entry_id or "").strip()
    if not ENTRY_ID_RE.match(entry_id):
        raise PolicyError("id must match [a-z0-9][a-z0-9_-]{0,63}")
    return entry_id


class PolicyAdmin:
    def __init__(self, policy_path: str | Path):
        self.policy_path = Path(policy_path)

    @staticmethod
    def slugify(value: str) -> str:
        cleaned = []
        value = (value or '').lower().strip()
        prev_dash = False
        for ch in value:
            if ch.isalnum():
                cleaned.append(ch)
                prev_dash = False
            elif ch in {'-', '_', '.', '/', ' '}:
                if not prev_dash:
                    cleaned.append('-')
                    prev_dash = True
        slug = ''.join(cleaned).strip('-')
        return slug[:64] or 'entry'

    def load(self) -> dict:
        with self.policy_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise PolicyError("policy root must be a mapping")
        data.setdefault("access_control", {}).setdefault("managed_sites", [])
        self._validate_uniqueness(data)
        return data

    def list_entries(self) -> list[dict]:
        policy = self.load()
        entries = []
        for entry in policy["access_control"]["managed_sites"]:
            item = dict(entry)
            item["path"] = normalize_path(item.get("path", "/"))
            item.setdefault("label", item["host"])
            item.setdefault("enabled", False)
            item.setdefault("target_conf", "")
            entries.append(item)
        return sorted(entries, key=lambda e: (e["host"], e["path"], e["id"]))

    def portal_summary(self) -> dict:
        policy = self.load()
        access = policy.get("access_control", {})
        return {
            "portal_domain": policy.get("portal", {}).get("domain", ""),
            "portal_path": policy.get("portal", {}).get("path", "/"),
            "remember_me": policy.get("session", {}).get("remember_me", ""),
            "default_policy": access.get("default_policy", "bypass"),
            "enforcement_enabled": bool(access.get("enforcement_enabled", True)),
        }

    def add_entry(self, *, entry_id: str, label: str, host: str, path: str, upstream: str, enabled: bool, target_conf: str = "") -> dict:
        policy = self.load()
        entry = {
            "id": validate_entry_id(entry_id),
            "label": (label or "").strip() or validate_host(host),
            "host": validate_host(host),
            "path": normalize_path(path),
            "enabled": bool(enabled),
            "upstream": validate_upstream(upstream),
            "target_conf": (target_conf or "").strip(),
        }

        entries = copy.deepcopy(policy["access_control"]["managed_sites"])
        if any(existing.get("id") == entry["id"] for existing in entries):
            raise PolicyError("id already exists")
        if any((existing.get("host"), normalize_path(existing.get("path", "/"))) == (entry["host"], entry["path"]) for existing in entries):
            raise PolicyError("host + path entry already exists")
        entries.append(entry)
        policy["access_control"]["managed_sites"] = entries
        self._save(policy)
        return entry

    def toggle_entry(self, entry_id: str) -> dict:
        policy = self.load()
        entries = copy.deepcopy(policy["access_control"]["managed_sites"])
        for entry in entries:
            if entry.get("id") == entry_id:
                entry["enabled"] = not bool(entry.get("enabled", False))
                policy["access_control"]["managed_sites"] = entries
                self._save(policy)
                return entry
        raise PolicyError("entry not found")

    def update_entry(self, entry_id: str, *, label: str, host: str, path: str, upstream: str, enabled: bool, target_conf: str = "") -> dict:
        policy = self.load()
        entries = copy.deepcopy(policy["access_control"]["managed_sites"])
        updated_entry = {
            "id": validate_entry_id(entry_id),
            "label": (label or "").strip() or validate_host(host),
            "host": validate_host(host),
            "path": normalize_path(path),
            "enabled": bool(enabled),
            "upstream": validate_upstream(upstream),
            "target_conf": (target_conf or "").strip(),
        }

        found = False
        for index, entry in enumerate(entries):
            if entry.get("id") == entry_id:
                entries[index] = updated_entry
                found = True
                break
        if not found:
            raise PolicyError("entry not found")

        policy["access_control"]["managed_sites"] = entries
        self._save(policy)
        return updated_entry

    def delete_entry(self, entry_id: str) -> None:
        policy = self.load()
        entries = copy.deepcopy(policy["access_control"]["managed_sites"])
        kept = [entry for entry in entries if entry.get("id") != entry_id]
        if len(kept) == len(entries):
            raise PolicyError("entry not found")
        policy["access_control"]["managed_sites"] = kept
        self._save(policy)

    def set_enforcement_enabled(self, enabled: bool) -> bool:
        policy = self.load()
        policy.setdefault("access_control", {})["enforcement_enabled"] = bool(enabled)
        self._save(policy)
        return bool(policy["access_control"]["enforcement_enabled"])

    def _validate_uniqueness(self, policy: dict) -> None:
        seen_ids = set()
        seen_pairs = set()
        for entry in policy.get("access_control", {}).get("managed_sites", []):
            entry_id = entry.get("id")
            if not entry_id:
                raise PolicyError("managed site missing id")
            if entry_id in seen_ids:
                raise PolicyError(f"duplicate id: {entry_id}")
            seen_ids.add(entry_id)
            pair = (entry.get("host"), normalize_path(entry.get("path", "/")))
            if pair in seen_pairs:
                raise PolicyError(f"duplicate host/path: {pair[0]} {pair[1]}")
            seen_pairs.add(pair)

    def _save(self, policy: dict) -> None:
        self._validate_uniqueness(policy)
        target_dir = self.policy_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target_dir, delete=False) as tmp:
            yaml.safe_dump(policy, tmp, sort_keys=False)
            tmp_path = Path(tmp.name)
        tmp_path.replace(self.policy_path)
