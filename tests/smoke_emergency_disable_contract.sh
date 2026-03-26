#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PANEL="$ROOT_DIR/package-base/config_panel.toml"
CONFIG_SCRIPT="$ROOT_DIR/package-base/scripts/config"

# Config surface should expose break-glass disable.
grep -q '\[main.operations.emergency_disable\]' "$CONFIG_PANEL"
grep -q '^run__emergency_disable() {' "$CONFIG_SCRIPT"
grep -q 'inject_protected_include.py" remove' "$CONFIG_SCRIPT"
grep -q 'Emergency disable complete' "$CONFIG_SCRIPT"
grep -q 'mfa-sidecar-authelia --action=stop' "$CONFIG_SCRIPT"
grep -q 'mfa-sidecar-admin --action=stop' "$CONFIG_SCRIPT"

echo "smoke_emergency_disable_contract: ok"
