# 2026-03-26 — simplified discovery pivot

- John explicitly pushed back that discovery was becoming overbuilt.
- Product direction simplified to:
  - domains come from YunoHost
  - app folders/subpaths come from YunoHost app inventory
  - nginx is only a yes/no sanity check
  - manual add handles custom nginx-only oddities
- Removed the heavier confidence/degraded-mode framing from the active discovery/UI path.
- Updated admin UI and tests to match the simpler model.
- Full smoke suite remained green after simplification.
