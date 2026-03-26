#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNS="${1:-3}"

for i in $(seq 1 "$RUNS"); do
  echo "=== repeat smoke run $i/$RUNS ==="
  "$ROOT_DIR/run_all_smoke.sh"
done

echo "repeat_smoke: ok ($RUNS runs)"
