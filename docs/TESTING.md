# MFA Sidecar Testing Notes

This file records the smoke/regression intent for the project.

## Why this exists

The package has already encountered several live-only failure modes that were too important to leave as folklore:

- auth-request contract drift against Authelia 4.39.x
- YunoHost SSOwat hijacking internal auth subrequests
- missing packaged asset paths breaking upgrade
- protected snippet generation/injection drift after upgrade/apply
- existing-install defaults not changing just because package defaults changed
- first-run MFA enrollment behaving differently from ordinary protected access

The test goal is simple:

> do not fight the same dragons twice.

## Current test layers

### YunoHost app tests

- `tests.toml`

These remain useful for basic package install/curl expectations, but they are not rich enough on their own to catch the integration regressions we hit on wm3v.

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
