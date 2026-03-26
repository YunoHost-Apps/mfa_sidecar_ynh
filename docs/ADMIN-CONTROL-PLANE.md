# Admin control plane (alpha)

## Purpose
Provide a thin operator-facing admin page for **MFA Sidecar** that manages the declarative policy file and regenerates runtime artifacts.

This is **not** a user dashboard. It is an admin/operator tool for editing which host/path entries are protected.

## Core UI
The first usable admin page should have exactly three jobs:

1. **Show current managed entries**
   - host
   - path
   - label
   - enabled/disabled state
   - upstream target

2. **Toggle an entry on/off**
   - simple binary control
   - no hidden policy complexity in the main view

3. **Add a new managed host/path entry**
   - label
   - host
   - path
   - upstream
   - initial enabled state

## Required behavior
- source of truth remains the policy YAML
- every write should:
  1. validate updated policy
  2. write policy atomically
  3. rerender Authelia/nginx output
  4. restage runtime files
- duplicate `host + path` entries must be rejected
- path normalization must match renderer semantics
- UI should explain that **longest matching path wins**
- UI should clearly distinguish:
  - the **portal domain** (where MFA Sidecar itself lives)
  - the **managed target entries** (what gets protected or bypassed)

## Alpha implementation choice
For alpha, the admin page should be a **small local web app** bundled with the package rather than trying to wedge everything into native YunoHost admin integration immediately.

### Why
- faster iteration
- lower coupling to YunoHost internals
- easier to validate the policy model and operator UX
- keeps the sidecar removable

## Suggested alpha routes
- `GET /` → overview page with managed entries table
- `POST /entries` → add entry
- `POST /entries/<id>/toggle` → flip enabled state
- `POST /entries/<id>/delete` → optional for alpha if needed
- `POST /apply` → optional explicit apply/reload if we decide not to auto-apply per change

## Initial UX opinion
Auto-apply on each successful change is the right alpha default.
The operator goal is simple state changes, not staged drafts with a whole second workflow layer.

## Data model expectations
Each managed entry should expose:
- `id`
- `label`
- `host`
- `path`
- `enabled`
- `upstream`

Global settings shown read-only at first:
- portal domain
- remembered session duration
- default policy = bypass

## Non-goals for first admin page
- fancy JS SPA
- full RBAC
- user self-service
- analytics
- discovery automation that silently enables anything
- deep YunoHost admin-panel embedding

## Thin architecture
Recommended alpha stack:
- Python 3 stdlib HTTP server or small Flask app
- read/write policy YAML
- call existing renderer + stager scripts
- bind to localhost behind generated nginx portal route

## Security expectations
- admin page should only be reachable by authenticated admins/operators
- do not expose raw secret material in the UI
- do not expose LDAP bind password in the UI
- reject malformed host/path/upstream input early
- keep writes serialized to avoid concurrent policy corruption

## Concrete next build steps
1. add a small `src/admin-ui/` app
2. add policy helper library for load/validate/save/toggle/add
3. render simple HTML table + add-entry form
4. wire package service/unit for admin UI
5. proxy admin UI behind portal domain
6. add smoke tests for add/toggle flows
