# MFA Sidecar Release Gates

This document exists to keep version bumps honest.

It is intentionally short.

## 0.3.0 gate status

`0.3.0` has now been earned on a real box.

### Completed for 0.3.0

- [x] Validate `access_control.enforcement_enabled: false` on a real box
- [x] Render / stage / apply runtime
- [x] Restart nginx + sidecar services
- [x] Confirm protected target is bypassed remotely
- [x] Re-enable enforcement
- [x] Confirm protected target requires sidecar auth again
- [x] Validate the auth-request bridge include is actually loaded by nginx
- [x] Validate both a root-mounted target and a subpath-mounted target on a real box
- [x] Validate disable / re-enable loops after the bridge + matcher + rollback fixes

## What was fixed to clear the gate

The live-box work that actually moved the package across the line included:

- restoring the missing nginx bridge include that loads per-target auth endpoint locations
- supporting trailing-slash-equivalent subpath matching (for layouts like `/webmail` vs `/webmail/`)
- fixing disabled-target cleanup so auth blocks and bridge includes are both removed together
- fixing package removal cleanup so bridge includes do not linger after uninstall/remove

## Why this release is honest

The repo and package have now demonstrated, on a real box:

- repeated real upgrades through multiple revisions
- end-to-end protected-target auth flow
- break-glass disable / re-enable
- root-mounted and subpath-mounted target protection
- uninstall/reinstall recovery under stress
- repo-local regression smoke coverage for the major live failures encountered so far

That still does not mean the package is perfect. It means `0.3.0` is an honest milestone rather than wishful numbering.

## What 0.3.0 means

`0.3.0` should mean:

- serious enough to invite broader real-world testing
- not claiming universal proof across every YunoHost layout
- honest about trust boundaries and maintenance surfaces
- operable enough that another admin can understand and recover it
