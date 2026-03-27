#!/usr/bin/env python3
"""Render alpha Authelia + nginx config from a policy YAML file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent

import yaml


def load_policy(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise SystemExit("policy root must be a mapping")
    return data


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def rule_sort_key(rule: dict) -> tuple[int, int, str, str]:
    host = rule["host"]
    path = normalize_path(rule.get("path", "/"))
    return (0 if rule.get("enabled", False) else 1, -len(path), host, path)


def get_storage_key_expression(storage_cfg: dict) -> str:
    if storage_cfg.get("encryption_key_file"):
        return f"{{{{ secret {storage_cfg['encryption_key_file']} }}}}"
    return "${%s}" % storage_cfg["encryption_key_env"]


def get_session_secret_expression(session_cfg: dict) -> str:
    if session_cfg.get("secret_file"):
        return f"{{{{ secret {session_cfg['secret_file']} }}}}"
    return "${%s}" % session_cfg["secret_env"]


def managed_sites(policy: dict) -> list[dict]:
    return sorted(policy["access_control"].get("managed_sites", []), key=rule_sort_key)


def extract_cookie_domain(fqdn: str) -> str:
    parts = fqdn.strip(".").split(".")
    if len(parts) <= 2:
        return fqdn.strip(".")
    return ".".join(parts[1:])


def collect_cookie_domains(policy: dict) -> list[dict]:
    portal = policy["portal"]
    session = policy["session"]
    explicit = str(session.get("cookie_domain", "")).strip().strip(".")
    portal_cookie_domain = explicit or extract_cookie_domain(portal["domain"])

    cookies_by_domain: dict[str, dict] = {
        portal_cookie_domain: {
            "domain": portal_cookie_domain,
            "authelia_url": f"https://{portal['domain']}{portal['path']}",
        }
    }
    for site in policy["access_control"].get("managed_sites", []):
        site_cookie_domain = extract_cookie_domain(site["host"])
        if site_cookie_domain not in cookies_by_domain:
            cookies_by_domain[site_cookie_domain] = {
                "domain": site_cookie_domain,
                "authelia_url": f"https://{portal['domain']}{portal['path']}",
            }
    return list(cookies_by_domain.values())


def map_default_policy(policy_name: str) -> str:
    mapping = {
        "open": "bypass",
        "protected": "two_factor",
        "bypass": "bypass",
        "one_factor": "one_factor",
        "two_factor": "two_factor",
        "deny": "deny",
    }
    return mapping.get(policy_name, "deny")


def build_authentication_backend(policy: dict) -> dict:
    identity = policy["identity"]
    local = identity["local"]
    search = local.get("search", {})
    backend = {
        "file": {
            "path": local["path"],
            "watch": bool(local.get("watch", False)),
            "search": {
                "email": bool(search.get("email", False)),
                "case_insensitive": bool(search.get("case_insensitive", False)),
            },
        }
    }
    if local.get("password"):
        backend["file"]["password"] = local["password"]
    return backend


def build_authelia_values(policy: dict) -> dict:
    portal = policy["portal"]
    session = policy["session"]
    mfa = policy["mfa"]
    access = policy["access_control"]
    storage = policy["storage"]
    recovery = policy.get("recovery", {})

    rules = []
    for site in managed_sites(policy):
        host = site["host"]
        path = normalize_path(site.get("path", "/"))
        enabled = bool(site.get("enabled", False))
        policy_name = "two_factor" if enabled else "bypass"
        rule = {"domain": host, "policy": policy_name}
        if path != "/":
            rule["resources"] = [f"^{path}([/?].*)?$"]
        rules.append(rule)

    rendered_default_policy = map_default_policy(access.get("default_policy", "deny"))
    if not rules and rendered_default_policy in {"bypass", "deny"}:
        rendered_default_policy = "one_factor"

    authelia = {
        "theme": "auto",
        "server": {"address": f"tcp://{portal['listen']['host']}:{portal['listen']['port']}"},
        "log": {"level": "info"},
        "identity_validation": {
            "reset_password": {"jwt_secret": "${AUTHELIA_IDENTITY_VALIDATION_RESET_SECRET}"}
        },
        "authentication_backend": build_authentication_backend(policy),
        "access_control": {
            "default_policy": rendered_default_policy,
            "rules": rules,
        },
        "session": {
            "name": session["name"],
            "secret": get_session_secret_expression(session),
            "expiration": session["expiration"],
            "inactivity": session["inactivity"],
            "remember_me": session["remember_me"],
            "cookies": collect_cookie_domains(policy),
        },
        "storage": {
            "encryption_key": get_storage_key_expression(storage),
            "local": {"path": "/var/lib/mfa_sidecar/db.sqlite3"},
        },
        "notifier": {"filesystem": {"filename": "/var/lib/mfa_sidecar/notification.txt"}},
        "totp": {"issuer": mfa["totp"]["issuer"]},
        "webauthn": {
            "disable": not bool(mfa["webauthn"].get("enabled", True)),
            "display_name": mfa["webauthn"]["display_name"],
            "attestation_conveyance_preference": mfa["webauthn"].get("attestation_conveyance_preference", "indirect"),
            "user_verification": mfa["webauthn"].get("user_verification", "preferred"),
            "timeout": mfa["webauthn"].get("timeout", "60s"),
        },
    }

    if recovery.get("disable_reset"):
        authelia["identity_validation"]["reset_password"]["disable"] = True

    return authelia


def build_nginx_portal_conf(policy: dict) -> str:
    portal = policy["portal"]
    return dedent(
        f"""
        location {portal['path']} {{
          proxy_pass http://{portal['listen']['host']}:{portal['listen']['port']};
          proxy_set_header Host $host;
          proxy_set_header X-Original-URL $scheme://$http_host$request_uri;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header X-Forwarded-Host $host;
          proxy_set_header X-Forwarded-URI $request_uri;
          proxy_set_header X-Forwarded-For $remote_addr;
          proxy_set_header X-Real-IP $remote_addr;
        }}

        location ^~ /admin {{
          if ($http_x_mfa_sidecar_admin_secret = "") {{ return 403; }}
          proxy_set_header X-MFA-Sidecar-Admin-Secret $http_x_mfa_sidecar_admin_secret;
          proxy_pass http://127.0.0.1:9087;
          proxy_set_header Host $host;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header X-Forwarded-Host $host;
          proxy_set_header X-Forwarded-URI $request_uri;
          proxy_set_header X-Forwarded-For $remote_addr;
          proxy_set_header X-Real-IP $remote_addr;
        }}
        """
    ).strip() + "\n"


def build_nginx_protected_conf(site: dict, portal_domain: str, authz_endpoint: str) -> str:
    upstream = site["upstream"]
    host = site["host"]
    path = normalize_path(site.get("path", "/"))
    location_modifier = "" if path == "/" else "^~"
    location_path = "/" if path == "/" else path
    auth_location = f"/authelia-auth-{site['id']}"
    location_directive = f"location {location_modifier} {location_path}".replace("  ", " ")

    return dedent(
        f"""
        {location_directive} {{
          auth_request {auth_location};
          error_page 401 =302 https://{portal_domain}/?rd=$scheme://$http_host$request_uri;

          proxy_pass {upstream};
          proxy_set_header Host $host;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Host $server_name;
          proxy_set_header X-Forwarded-Uri $request_uri;
          proxy_set_header X-Real-IP $remote_addr;
        }}

        location = {auth_location} {{
          internal;
          proxy_pass {authz_endpoint};
          proxy_pass_request_body off;
          proxy_set_header Content-Length "";
          proxy_set_header X-Original-URL $scheme://$http_host$request_uri;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header X-Forwarded-Host $host;
          proxy_set_header X-Forwarded-URI $request_uri;
          proxy_set_header X-Real-IP $remote_addr;
        }}

        # id: {site['id']}
        # host: {host}
        # path: {path}
        # enabled: {str(site.get('enabled', False)).lower()}
        """
    ).strip() + "\n"


def build_index(policy: dict) -> dict:
    enabled = []
    disabled = []
    for site in managed_sites(policy):
        target = enabled if site.get("enabled", False) else disabled
        target.append(
            {
                "id": site["id"],
                "host": site["host"],
                "path": normalize_path(site.get("path", "/")),
                "upstream": site["upstream"],
                "label": site.get("label", site["host"]),
            }
        )
    return {
        "portal_domain": policy["portal"]["domain"],
        "enabled": enabled,
        "disabled": disabled,
    }


def build_runtime_metadata(policy: dict) -> dict:
    local = policy["identity"]["local"]
    sync = policy["identity"].get("sync", {})
    return {
        "portal_domain": policy["portal"]["domain"],
        "portal_listen": policy["portal"]["listen"],
        "identity": {
            "backend": "file",
            "user_database_path": local["path"],
            "watch": bool(local.get("watch", False)),
            "password_algorithm": local.get("password", {}).get("algorithm", "argon2"),
            "sync_enabled": bool(sync.get("enabled", False)),
            "sync_source": sync.get("source", "none"),
        },
        "secrets": {
            "session": "file" if policy["session"].get("secret_file") else "env",
            "storage_encryption": "file" if policy["storage"].get("encryption_key_file") else "env",
        },
        "managed_sites": [
            {
                "id": site["id"],
                "host": site["host"],
                "path": normalize_path(site.get("path", "/")),
                "enabled": bool(site.get("enabled", False)),
            }
            for site in managed_sites(policy)
        ],
    }


def validate_managed_sites(policy: dict) -> list[dict]:
    seen = set()
    normalized = []
    for index, site in enumerate(policy["access_control"].get("managed_sites", []), start=1):
        site = dict(site)
        site.setdefault("id", f"site_{index}")
        site["path"] = normalize_path(site.get("path", "/"))
        key = (site["host"], site["path"])
        if key in seen:
            raise SystemExit(f"duplicate managed site rule for host/path: {site['host']} {site['path']}")
        seen.add(key)
        normalized.append(site)
    policy["access_control"]["managed_sites"] = normalized
    return normalized


def render(policy_path: Path, out_dir: Path) -> None:
    policy = load_policy(policy_path)
    validate_managed_sites(policy)
    ensure_dir(out_dir)
    nginx_dir = out_dir / "nginx"
    ensure_dir(nginx_dir)

    authelia_values = build_authelia_values(policy)
    (out_dir / "authelia-config.generated.yml").write_text(
        yaml.safe_dump(authelia_values, sort_keys=False), encoding="utf-8"
    )
    (nginx_dir / "portal.generated.conf").write_text(build_nginx_portal_conf(policy), encoding="utf-8")

    authz_endpoint = f"http://{policy['portal']['listen']['host']}:{policy['portal']['listen']['port']}/api/authz/auth-request"
    portal_domain = policy["portal"]["domain"]
    for site in managed_sites(policy):
        target_file = nginx_dir / f"{site['id']}.generated.conf"
        target_file.write_text(build_nginx_protected_conf(site, portal_domain, authz_endpoint), encoding="utf-8")

    (out_dir / "render-index.json").write_text(json.dumps(build_index(policy), indent=2) + "\n", encoding="utf-8")
    (out_dir / "runtime-metadata.json").write_text(json.dumps(build_runtime_metadata(policy), indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("policy")
    parser.add_argument("out_dir")
    args = parser.parse_args()
    render(Path(args.policy), Path(args.out_dir))


if __name__ == "__main__":
    main()
