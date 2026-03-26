#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ADMIN_APP = ROOT_DIR / "package-base/sources/admin_ui_app.py"
LOGO = ROOT_DIR / "package-base/assets/logo.png"

MIN_POLICY = """version: 1
portal:
  domain: auth.example.tld
  path: /
session:
  remember_me: 24h
access_control:
  default_policy: open
  managed_sites: []
"""


def load_module():
    spec = importlib.util.spec_from_file_location("admin_ui_app", ADMIN_APP)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        policy = tmpdir / "domain-policy.yaml"
        policy.write_text(MIN_POLICY, encoding="utf-8")
        os.environ["MFA_SIDECAR_ADMIN_LOGO_PATH"] = str(LOGO)
        os.environ["MFA_SIDECAR_POLICY_PATH"] = str(policy)
        os.environ["MFA_SIDECAR_DISCOVERY_YUNOHOST_BIN"] = str(ROOT_DIR / 'tests/fake-yunohost')
        os.environ["MFA_SIDECAR_DISCOVERY_NGINX_CONF_DIR"] = str(tmpdir / 'etc/nginx/conf.d')
        mod = load_module()
        assert mod.LOGO_PATH == LOGO
        html = mod.APP.render_index()
        assert "/admin/logo" in html
        assert "MFA Sidecar logo" in html
    print("smoke_admin_logo_contract: ok")


if __name__ == "__main__":
    main()
