#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY_PATH="${1:-$ROOT_DIR/configs/domain-policy.example.yaml}"
OUT_DIR="${2:-$ROOT_DIR/deploy/generated-alpha}"

mkdir -p "$OUT_DIR"
python3 "$ROOT_DIR/src/config-render/render_alpha_config.py" "$POLICY_PATH" "$OUT_DIR"

echo "Generated alpha config into: $OUT_DIR"
