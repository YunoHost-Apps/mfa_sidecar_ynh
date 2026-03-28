# MFA Sidecar Release Gates

This document exists to keep version bumps honest.

It is intentionally short.

## Proposed gate for 0.3.0

The repo and package are already substantially hardened. For `0.3.0`, the remaining meaningful gate is **real-box break-glass validation**.

### Required before calling it 0.3.0

- [ ] Validate `access_control.enforcement_enabled: false` on a real box
- [ ] Render / stage / apply runtime
- [ ] Restart nginx + sidecar services
- [ ] Confirm protected target is bypassed remotely
- [ ] Re-enable enforcement
- [ ] Confirm protected target requires sidecar auth again

## Why this is the remaining gate

The following are already considered substantially demonstrated:

- repeated real upgrades through multiple revisions
- end-to-end protected-target auth flow on a real box
- uninstall/reinstall recovery under stress
- repo-local regression smoke coverage for the major live failures encountered so far

That does not mean the package is perfect. It means the most meaningful remaining pre-`0.3.0` proof is the break-glass path.

## What 0.3.0 means

`0.3.0` should mean:

- serious enough to invite broader real-world testing
- not claiming universal proof across every YunoHost layout
- honest about trust boundaries and maintenance surfaces
- operable enough that another admin can understand and recover it
