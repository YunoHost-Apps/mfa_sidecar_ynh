#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$ROOT_DIR/smoke_render.sh"
"$ROOT_DIR/smoke_stage_runtime.sh"
"$ROOT_DIR/smoke_inject_include.sh"
python3 "$ROOT_DIR/smoke_edge_policies.py"
"$ROOT_DIR/smoke_policy_seed.sh"
python3 "$ROOT_DIR/smoke_discovery.py"
python3 "$ROOT_DIR/smoke_admin_ui.py"
python3 "$ROOT_DIR/smoke_admin_gate.py"
"$ROOT_DIR/smoke_include_idempotence.sh"
"$ROOT_DIR/smoke_failure_contracts.sh"
"$ROOT_DIR/smoke_fetch_contract.sh"
"$ROOT_DIR/smoke_path_resolution.sh"
"$ROOT_DIR/smoke_ldap_secret_handling.sh"
"$ROOT_DIR/smoke_package_tree.sh"
"$ROOT_DIR/smoke_publication_shape.sh"
"$ROOT_DIR/smoke_service_contract.sh"
"$ROOT_DIR/smoke_restore_contract.sh"
"$ROOT_DIR/smoke_install_runtime_guards.sh"
"$ROOT_DIR/smoke_package_admin_ui.sh"
"$ROOT_DIR/smoke_vendor_authelia.sh"
"$ROOT_DIR/smoke_vendor_repeat.sh"
"$ROOT_DIR/smoke_tampered_vendor.sh"

echo "all_smoke: ok"
