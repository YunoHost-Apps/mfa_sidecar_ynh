# Admin UI implementation notes (alpha)

## What now exists
A thin admin UI lives under `src/admin-ui/` and is mirrored into `package-base/sources/` for packaging.

### Files
- `src/admin-ui/policy_admin.py`
  - load policy YAML
  - validate host/path/upstream/id
  - reject duplicate `host + path`
  - add managed entry
  - toggle managed entry
  - atomic save
- `src/admin-ui/discovery.py`
  - simple YunoHost-first discovery
  - domains come from YunoHost inventory
  - app subpaths come from YunoHost app inventory
  - nginx is only used as a yes/no sanity check for discovered subpaths
- `src/admin-ui/app.py`
  - simple HTML operator page
  - shows discovered app-path suggestions
  - lists managed entries
  - add-entry form
  - per-entry enable/disable button
  - auto-apply path that reruns render + stage after successful changes

## Why this shape
This keeps the first control plane:
- boring
- inspectable
- tightly bound to the actual policy file
- less overbuilt than the earlier broader discovery direction
- independent of YunoHost admin internals for now

## Remaining work after simplification
- add real operator-auth gating in front of `/admin`
- validate behavior on a real YunoHost host with nginx + Authelia both live
- decide whether domains themselves should also be surfaced directly in the UI as selectable targets, or whether app-path suggestions + manual add are sufficient
- optionally improve the nginx mismatch presentation if real host testing shows it is confusing

## Opinionated route choice
Use **`/admin`** for the control plane behind the portal domain.
Authelia stays at `/`; operator control page lives off the side rather than pretending it is the login UX.
