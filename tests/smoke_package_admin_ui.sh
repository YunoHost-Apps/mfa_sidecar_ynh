#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="$ROOT_DIR/package-base/sources/mfa-sidecar-admin.service"
PORTAL_CONF="$ROOT_DIR/package-base/conf/nginx-portal.conf"

python3 -m py_compile \
  "$ROOT_DIR/package-base/sources/policy_admin.py" \
  "$ROOT_DIR/package-base/sources/discovery.py" \
  "$ROOT_DIR/package-base/sources/admin_ui_app.py"

python3 - <<PY
import importlib.util
from pathlib import Path
p = Path(r"$ROOT_DIR/package-base/sources/admin_ui_app.py").resolve()
spec = importlib.util.spec_from_file_location('admin_ui_app', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('packaged_admin_import: ok')
PY

grep -q '^ExecStart=/usr/bin/python3 /opt/yunohost/mfa_sidecar/bin/admin_ui_app.py$' "$SERVICE"
grep -q '^Environment=MFA_SIDECAR_ADMIN_PORT=9087$' "$SERVICE"
grep -q '^location \^~ /admin {$' "$PORTAL_CONF"
grep -q 'X-MFA-Sidecar-Admin-Secret' "$PORTAL_CONF"
grep -q 'proxy_pass http://127.0.0.1:9087;' "$PORTAL_CONF"
grep -q "'/admin/logo'" "$ROOT_DIR/package-base/sources/admin_ui_app.py"
grep -q 'install -D -m 644 ../assets/logo.png "\$install_dir/www/logo.png"' "$ROOT_DIR/package-base/scripts/install"
grep -q 'install -D -m 644 ../assets/logo.png "\$install_dir/www/logo.png"' "$ROOT_DIR/package-base/scripts/upgrade"

echo "smoke_package_admin_ui: ok"
