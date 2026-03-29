# MFA Sidecar Release Gates

This document exists to keep version bumps honest.

It is intentionally short.

## 0.4.0 gate status

`0.4.0` has now been earned on a real box.

### Completed for 0.4.0

- [x] Fresh install succeeds with install dir under `/var/www/$app`
- [x] Sidecar services start cleanly from `/var/www/mfa_sidecar`
- [x] HomeBox/root-mounted protection works on the real box
- [x] Roundcube `/webmail` subpath protection works on the real box
- [x] Shared sidecar session behavior works across protected targets as intended
- [x] Disable / re-enable still behaves correctly after the packaging changes
- [x] Reserved username `admin` is now blocked for fresh install / new-user flows
- [x] Reload churn was reduced after discovering nginx+nchan fragility under clustered reloads on wm3v
- [x] Authorization-header contamination was fixed for auth subrequests (Roundcube/webmail loop case)

## What was fixed to clear the gate

The live-box work that actually moved the package across the line included:

- migrating package defaults toward YunoHost install-dir conventions (`/var/www/$app`) without regressing the live box
- reducing hard-coded install-dir coupling in services, hooks, runtime helpers, and docs
- fixing upgrade validation so historical installs are not blocked by the new reserved-username rule
- fixing restore package-root lookup in YunoHost temp/restore layouts
- reducing redundant nginx reloads during lifecycle operations after real nginx+nchan churn failures were observed
- stripping `Authorization` / `Proxy-Authorization` headers from auth subrequests so downstream app auth does not poison the sidecar auth check
- documenting and enforcing the `admin` username footgun discovered on the real box

## Why this release is honest

The repo and package have now demonstrated, on a real box:

- fresh install on the new `/var/www` default
- clean service startup from the new install dir
- end-to-end protected-target auth flow on both root-mounted and subpath targets
- break-glass / disable / re-enable behavior
- real operator-footgun handling (`admin` username)
- repo-local regression smoke coverage for the major live failures encountered so far

That still does not mean the package is perfect. It means `0.4.0` is an honest packaging + lifecycle hardening milestone rather than wishful numbering.

## What 0.4.0 means

`0.4.0` should mean:

- serious enough to submit and invite broader real-world testing
- not claiming universal proof across every YunoHost layout
- honest about trust boundaries, packaging tradeoffs, and maintenance surfaces
- operable enough that another admin can understand and recover it
