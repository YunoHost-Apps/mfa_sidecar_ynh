# MFA Sidecar Testing Notes

This file records the smoke/regression intent for the project.

## Why this exists

The package has already encountered several live-only failure modes that were too important to leave as folklore:

- auth-request contract drift against Authelia 4.39.x
- YunoHost SSOwat hijacking internal auth subrequests
- missing packaged asset paths breaking upgrade
- protected snippet generation/injection drift after upgrade/apply
- missing live nginx bridge includes for auth endpoint locations
- subpath location matching drift such as `/webmail` vs `/webmail/`
- disabled-target cleanup leaving half-rolled-back auth blocks behind
- existing-install defaults not changing just because package defaults changed
- first-run MFA enrollment behaving differently from ordinary protected access

The test goal is simple:

> do not fight the same dragons twice.

## Current test layers

### YunoHost app tests

- `tests.toml`
- `YunoHost/package_check` (external harness; not vendored in this repo)

These are the first-class app contract. `tests.toml` should describe what package_check is actually allowed to do, and package_check should be treated as the boring baseline for install/remove/upgrade/backup/restore behavior.

For MFA Sidecar specifically, `tests.toml` now explicitly declares the required first-admin install args and excludes `install.subdir` because the app is intentionally dedicated-domain root-only.

These YunoHost tests still are not rich enough on their own to catch every custom integration regression we hit on wm3v, but they are the baseline discipline we should satisfy before trusting any repo-local smoke suite.

### Repo-local smoke regressions

- `tests/smoke_regressions.py`

This suite focuses on the integration seams and packaging failures we actually encountered.

## What the local smoke suite covers

- generated auth endpoint snippet contains required Authelia headers
- internal auth location bypasses YunoHost SSOwat with `access_by_lua_block { return; }`
- generated auth block uses Authelia-provided redirect header instead of hardcoded portal redirect
- WebAuthn disabled in policy renders to `webauthn.disable: true`
- enabled managed targets generate protected nginx snippets
- reinjection applies the managed auth block to the target location
- reinjection writes/removes per-target bridge include files for auth endpoint snippets
- trailing-slash-equivalent subpath matching works for injected target locations
- disabled targets remove both managed auth blocks and sibling bridge includes
- install/upgrade scripts do not reference missing packaged files
- required docs/license files are present in the repository
- logo compatibility asset exists so branding changes do not brick upgrades

## Still missing / still worth proving on a real box

Even with the local smoke suite, some things are only trustworthy after live execution:

- upgrade from one or more older package revisions to current
- protected target auth regression on a real app path
- global `enforcement_enabled: false` break-glass behavior
- uninstall/restore cleanliness
- multi-domain common setups
- end-to-end first-run enrollment plus subsequent access flow

## Suggested command

From the repo root:

```bash
python3 tests/smoke_regressions.py
```

If this file grows more complex later, it can be migrated into a richer test harness. For now, the main job is to codify the painful lessons while they are still fresh.
