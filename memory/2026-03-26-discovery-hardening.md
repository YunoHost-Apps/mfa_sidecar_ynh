# 2026-03-26 — discovery hardening

- John explicitly asked for better robustness before another install, including discovery of available domains and root-domain subfolder apps.
- Discovery layer was upgraded from file/nginx-only to a merged model:
  - prefer YunoHost CLI JSON inventory when available
  - fall back to YunoHost-style metadata/domain files
  - still inspect nginx per-domain `location` blocks for root-domain subpath apps and reality-check coverage
- Admin UI now surfaces discovered targets as suggestions only; no silent auto-protection.
- Added/updated smoke coverage for:
  - fake `yunohost` CLI inventory
  - root-domain subpath discovery
  - package-tree presence of discovery/admin helpers
- Full smoke suite green after the hardening pass.
