# Alpha candidate status

## What now exists
This project now contains a coherent late-alpha / production-hardening candidate with these pieces wired together:

1. **Package skeleton**
   - `package-base/manifest.toml`
   - YunoHost lifecycle scripts for install / upgrade / backup / restore / remove

2. **Policy-driven config model**
   - `configs/domain-policy.example.yaml`
   - package install now seeds a real policy file rather than a toy redirect target

3. **Renderer**
   - `src/config-render/render_alpha_config.py`
   - package-local copy in `package-base/sources/render_alpha_config.py`
   - generates Authelia config, portal nginx include, protected-domain nginx includes, and runtime metadata

4. **Runtime staging**
   - `scripts/stage_alpha_runtime.py`
   - package-local copy in `package-base/sources/stage_alpha_runtime.py`
   - stages generated output into `/etc/mfa-sidecar/...`

5. **Runtime assets**
   - systemd unit draft for Authelia
   - env file generation
   - secret file generation
   - staged nginx include layout

6. **Admin/control surface**
   - thin bundled admin UI at `/admin`
   - managed entry add / edit / delete / toggle workflow
   - YunoHost-first discovery of app-path candidates with nginx sanity check

7. **Tests**
   - renderer smoke test
   - staging smoke test
   - discovery smoke test
   - admin UI smoke test
   - admin gate smoke test
   - failure-contract / vendor / repeatability smoke coverage

## What the package lifecycle does now
### Install
- validates install inputs
- creates package + runtime layout
- copies renderer/stager helper programs into app install dir
- installs systemd unit draft
- generates alpha secrets if missing
- writes `/etc/mfa-sidecar/mfa-sidecar.env`
- writes seeded `domain-policy.yaml`
- renders generated alpha output
- stages rendered output into `/etc/mfa-sidecar/...`
- points package nginx config at generated portal config
- enables the draft sidecar service

### Upgrade
- preserves existing policy/env where present
- re-copies helper programs and systemd unit
- ensures missing secrets exist
- re-renders and re-stages runtime output
- refreshes nginx config
- attempts sidecar service restart

### Backup / Restore
- backs up nginx config, policy seed, readme, and `/etc/mfa-sidecar`
- restores those paths and reloads services

### Remove
- removes nginx config
- stops/disables sidecar service
- removes `/etc/mfa-sidecar`
- removes `/var/lib/mfa_sidecar`
- removes the owned install dir `/opt/yunohost/mfa_sidecar`

## Honest alpha limitations
This is a **fully developed alpha candidate**, not a production-ready package.

Still missing or intentionally rough:
- real live-host validation is still the biggest remaining truth test; green smoke coverage is necessary but not sufficient
- managed include injection/removal needs broader live validation across more YunoHost app/domain layouts, not just the current known-good path
- the sidecar-owned users database path still needs real operator validation under first login / enrollment flows on target
- first-user creation now has a real config-panel-driven path and helper tooling, but it still needs end-to-end live-host proof that a fresh operator will discover and complete it cleanly
- runtime ownership/permission handling has been hardened in-repo, including staging-time mode enforcement, but it still needs live-host proof across install/upgrade/restore on target
- `/admin` is operator-usable now, but its auth gate is still a pragmatic shared-secret header design rather than a polished long-term operator auth model
- first-run UX is still poor: a fresh operator can land on a login page without obvious guidance on how to create the first user or define what gets protected
- v1 scope is intentionally narrow: browser-first compatible web apps only, not a general protocol-aware second firewall

## Why this still counts as alpha candidate
Because the core architecture loop is now closed:
- inputs exist
- package lifecycle exists
- config generation exists
- runtime staging exists
- service/runtime shape exists
- tests exist
- remaining gaps are mostly integration hardening and operator ergonomics, not missing architectural core

## Recommended next post-alpha tasks
1. real host validation on a YunoHost VM
2. confirm LDAP filters and bind-account model
3. add binary provisioning/install strategy for Authelia
4. implement generated protected-domain include injection/removal helpers
5. harden service user / file ownership / permissions
6. harden the current `/admin` control plane auth/UX and validate it on the live target
