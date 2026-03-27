#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

SERVER_NAME_RE = re.compile(r"\bserver_name\s+([^;]+);")
LOCATION_RE = re.compile(r"^\s*location\s+(?:=|\^~|~\*|~)?\s*([^\s{]+)")
PROXY_PASS_RE = re.compile(r"^\s*proxy_pass\s+([^;]+);")

DEFAULT_NGINX_CONF_DIR = "/etc/nginx/conf.d"
DEFAULT_YUNOHOST_BIN = "/usr/bin/yunohost"
DEFAULT_UPSTREAM_FALLBACK = "https://127.0.0.1:443"


def normalize_path(path: str) -> str:
    path = (path or "/").strip()
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


class Discovery:
    def __init__(self, *, nginx_conf_dir: str | Path = DEFAULT_NGINX_CONF_DIR, yunohost_bin: str = DEFAULT_YUNOHOST_BIN) -> None:
        self.nginx_conf_dir = Path(nginx_conf_dir)
        self.yunohost_bin = yunohost_bin

    def discover(self) -> dict:
        domains = self._discover_domains_via_cli()
        apps = self._discover_apps_via_cli()
        nginx_paths = self._discover_nginx_paths()
        suggestions = self._build_suggestions(domains, apps, nginx_paths)
        return {
            "domains": domains,
            "domain_source": "yunohost-cli",
            "app_source": "yunohost-cli",
            "suggestions": suggestions,
        }

    def _discover_domains_via_cli(self) -> list[str]:
        payload = self._run_json([self.yunohost_bin, "domain", "list", "--output-as", "json"])
        if not isinstance(payload, dict):
            return []
        domains = payload.get("domains") or payload.get("domains_list") or []
        if not isinstance(domains, list):
            return []
        return sorted(str(item).strip() for item in domains if str(item).strip())

    def _discover_apps_via_cli(self) -> list[dict]:
        payload = self._run_json([self.yunohost_bin, "app", "list", "--output-as", "json"])
        if not isinstance(payload, dict):
            return []
        apps = payload.get("apps") or []
        if not isinstance(apps, list):
            return []

        found = []
        for app in apps:
            if not isinstance(app, dict):
                continue
            domain = str(app.get("domain") or "").strip()
            path = str(app.get("path") or "").strip()
            if not domain:
                domain_path = str(app.get("domain_path") or "").strip()
                if "/" in domain_path:
                    domain, path = domain_path.split("/", 1)
                    path = "/" + path
                elif domain_path:
                    domain = domain_path
                    path = "/"
            if not domain:
                continue
            path = normalize_path(path or "/")
            found.append(
                {
                    "id": str(app.get("id") or app.get("name") or "").strip(),
                    "label": str(app.get("label") or app.get("name") or app.get("id") or path.strip('/') or domain),
                    "domain": domain,
                    "path": path,
                }
            )
        return sorted(found, key=lambda item: (item["domain"], item["path"], item["id"]))

    def _discover_nginx_paths(self) -> dict[tuple[str, str], str]:
        found: dict[tuple[str, str], str] = {}
        if not self.nginx_conf_dir.exists():
            return found

        for domain_dir in self.nginx_conf_dir.glob('*.d'):
            if not domain_dir.is_dir() or not domain_dir.name.endswith('.d'):
                continue
            domain = domain_dir.name[:-2]
            for conf in sorted(domain_dir.glob('*.conf')):
                for path in self._paths_from_conf(conf):
                    found.setdefault((domain, path), str(conf))

        for conf in self.nginx_conf_dir.glob('*.conf'):
            domains = self._domains_from_conf(conf)
            paths = self._paths_from_conf(conf)
            for domain in domains:
                for path in paths:
                    found.setdefault((domain, path), str(conf))

        return found

    def _domains_from_conf(self, path: Path) -> list[str]:
        text = self._safe_read(path)
        found = []
        for match in SERVER_NAME_RE.finditer(text):
            for token in match.group(1).split():
                token = token.strip()
                if token and token not in {'_', 'localhost'}:
                    found.append(token)
        return found

    def _paths_from_conf(self, path: Path) -> list[str]:
        text = self._safe_read(path)
        found = []
        for line in text.splitlines():
            match = LOCATION_RE.match(line)
            if not match:
                continue
            loc = normalize_path(match.group(1))
            if loc.startswith('/.well-known'):
                continue
            found.append(loc)
        return found

    def _build_suggestions(self, domains: list[str], apps: list[dict], nginx_paths: dict[tuple[str, str], str]) -> list[dict]:
        suggestions_by_pair: dict[tuple[str, str], dict] = {}

        for domain in domains:
            root_target_conf = nginx_paths.get((domain, "/"), f"/etc/nginx/conf.d/{domain}.d/default.conf")
            suggestions_by_pair[(domain, "/")] = {
                "kind": "domain",
                "label": domain,
                "host": domain,
                "path": "/",
                "nginx_present": (domain, "/") in nginx_paths,
                "target_conf": root_target_conf,
                "suggested_upstream": self._discover_upstream(domain, "/", nginx_paths),
            }

        for app in apps:
            path = app["path"]
            pair = (app["domain"], path)
            candidate = {
                "kind": "app-path",
                "label": app["label"],
                "host": app["domain"],
                "path": path,
                "app_id": app["id"],
                "suggested_upstream": self._discover_upstream(app["domain"], path, nginx_paths),
                "nginx_present": (app["domain"], path) in nginx_paths,
                "target_conf": nginx_paths.get((app["domain"], path), f"/etc/nginx/conf.d/{app['domain']}.d/{app['id']}.conf"),
            }
            existing = suggestions_by_pair.get(pair)
            if existing is None or existing.get("kind") != "app-path":
                suggestions_by_pair[pair] = candidate

        suggestions = list(suggestions_by_pair.values())
        suggestions.sort(key=lambda item: (item["host"], item["path"], item["kind"]))
        return suggestions


    def discover_target_conf(self, host: str, path: str) -> str:
        host = str(host).strip()
        path = normalize_path(path)
        nginx_paths = self._discover_nginx_paths()
        return nginx_paths.get((host, path), f"/etc/nginx/conf.d/{host}.d/default.conf")

    def _discover_upstream(self, host: str, path: str, nginx_paths: dict[tuple[str, str], str] | None = None) -> str:
        host = str(host).strip()
        path = normalize_path(path)
        nginx_paths = nginx_paths or self._discover_nginx_paths()
        conf_path = nginx_paths.get((host, path))
        if not conf_path:
            return DEFAULT_UPSTREAM_FALLBACK
        text = self._safe_read(Path(conf_path))
        if not text:
            return DEFAULT_UPSTREAM_FALLBACK
        current_location = None
        for line in text.splitlines():
            match = LOCATION_RE.match(line)
            if match:
                current_location = normalize_path(match.group(1))
                continue
            proxy_match = PROXY_PASS_RE.match(line)
            if proxy_match and current_location == path:
                return proxy_match.group(1).strip()
        return DEFAULT_UPSTREAM_FALLBACK

    def _run_json(self, command: list[str]) -> dict | list | None:
        if not shutil.which(command[0]):
            return None
        try:
            proc = subprocess.run(["sudo", *command], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, OSError):
            return None
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return None

    def _safe_read(self, path: Path) -> str:
        try:
            return path.read_text(encoding='utf-8')
        except OSError:
            return ''
