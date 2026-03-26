#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FETCHER="$ROOT_DIR/package-base/sources/install_authelia_from_vendor.py"
OUT_DIR="$ROOT_DIR/tests/out/failure-contracts"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/vendor"

cp "$ROOT_DIR/package-base/sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz" "$OUT_DIR/vendor/"

cat > "$OUT_DIR/bad-release.json" <<'EOF'
{
  "version": "4.39.16",
  "tag": "v4.39.16",
  "asset": "authelia-v4.39.16-linux-amd64.tar.gz",
  "sha256": "deadbeef",
  "source": "test",
  "fetched_at": "2026-03-25T22:24:53Z"
}
EOF

if python3 "$FETCHER" "$OUT_DIR/bad-release.json" "$OUT_DIR/vendor" "$OUT_DIR/fetch" > "$OUT_DIR/output.txt" 2>&1; then
  echo "expected failure but got success" >&2
  exit 1
fi

grep -q 'sha256 mismatch:' "$OUT_DIR/output.txt"

echo "smoke_failure_contracts: ok"
