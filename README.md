# MFA Sidecar

<img src="https://raw.githubusercontent.com/YunoHost/apps/main/logos/mfa_sidecar.png" width="32px" alt="Logo of MFA Sidecar">

**MFA Sidecar** is an Authelia-backed **browser-first MFA perimeter** for selected YunoHost web apps.

It is meant to sit *in front of* chosen web targets, not replace YunoHost auth globally and not act like a generic protocol firewall. Think: protect a handful of browser-facing apps with an outer auth shell, while leaving YunoHost itself mostly alone.

## What it is

Current shape:
- dedicated **portal domain** for the sidecar itself
- managed **host + path** entries for protected targets
- **Authelia** for login, session, TOTP, and WebAuthn/passkeys
- separate **sidecar-owned credential + MFA store**
- thin **admin/control plane** for managing targets
- explicit **break-glass / emergency disable** path

Current intended scope:
- Homebox
- admin dashboards
- browser-first internal tools
- other simple reverse-proxy-style web apps

Current non-goals for v1:
- global YunoHost auth replacement
- IMAP / SMTP / mail protocol protection
- generic machine/API/firewall behavior
- using Nextcloud-class complexity as the **first** proof target

## How it works now

The architecture pivot that matters most is this:

**Protected targets are no longer implemented as generated replacement `location` blocks.**

Instead, the package now does two things:
1. renders **auth-endpoint-only nginx snippets** (internal sibling locations such as `/authelia-auth-...`)
2. injects a small managed block into the **existing app `location` block**:
   - `auth_request ...`
   - `error_page 401 =302 ...`

That matters because it preserves app-specific nginx behavior instead of shadowing it.

### Reinjection model

YunoHost owns nginx config generation. That means app config can be rewritten during:
- app upgrade
- `yunohost tools regen-conf nginx`
- app URL changes / other lifecycle events

So MFA Sidecar treats reinjection as part of the design, not an accident:
- render index carries `target_conf`, `auth_location`, `portal_domain`, and `injection_mode`
- package hooks re-run injection after regen/app lifecycle events
- admin UI now uses the same effective apply path as the package lifecycle

### Admin apply path

The admin UI runs as the app user, not root.

When an operator changes managed targets in `/admin`, the package now completes the apply cycle by:
- rendering updated config
- staging runtime files
- running reinjection
- validating nginx
- reloading nginx
- restarting Authelia

That last step is done through a **narrow sudo helper**, not broad service-control privileges.

## Current status

This project is at a **production-hardened alpha candidate** checkpoint.

What is already true:
- local validation is strong
- the auth model is sidecar-owned rather than coupled to YunoHost auth
- break-glass behavior exists
- admin target management exists
- injection/reinjection architecture is implemented
- regen hooks exist
- package/dev/publication branches are now aligned deliberately instead of by luck

What is **not** yet true:
- the current architecture is **not** yet live-proven end-to-end on wm3v after the injection pivot
- the package should still be treated as **snapshot-first / rollback-friendly** until that host proof is complete
- discovery/target selection still needs honest live validation on a real target app
- fresh-domain nginx parent server block creation can still depend on `yunohost tools regen-conf nginx --force` if the host/domain state is weird after install

## Recommended first live proof

Use:
- **portal:** `auth.wm3v.com`
- **first target:** `home.wm3v.com`

Why:
- earlier wm3v inspection suggests Homebox is a simple reverse-proxy app
- that makes it a much better first victim than a Nextcloud-class config
- if the injection model breaks there, we learn something cleanly

## Branches and install surface

- **`main`** → installer-facing package branch on GitHub
- **`dev`** → development branch with source, docs, tests, notes
- **`github-package`** → package-root mirror branch used for publication discipline / remote syncing
- **`dist/package-root/`** → generated local export used to refresh installer-facing/package-root surfaces from `dev`

If YunoHost is installing from GitHub, use the repo's **`main`** branch — not `dev`.

## Current package capabilities

- vendored Authelia artifact with checksum verification
- dedicated portal-domain install model
- managed site policy generation for host/path entries
- generated Authelia config + auth-endpoint nginx snippets
- runtime staging into `/etc/mfa-sidecar`
- package lifecycle scripts for install / upgrade / backup / restore / remove
- YunoHost config-panel surface for high-level settings and operator actions
- bundled `/admin` control plane for managed host/path entries
- first-user bootstrap via Authelia-generated Argon2 hashes
- optional YunoHost-driven user sync that preserves sidecar password/MFA authority
- emergency disable that removes the portal include hook, removes protected app-location injections, and stops sidecar services without destructive uninstall
- repeated smoke coverage for renderer, staging, injector behavior, admin flow, vendored binary handling, user bootstrap/sync, break-glass behavior, and package export shape

## Important constraints

- install the sidecar portal on its **own dedicated domain** at `/`
- define protected targets separately as managed **host/path** entries
- do **not** auto-protect things without explicit operator intent
- do **not** treat this as a global MFA layer for all YunoHost traffic

## Operator caveats

A few sharp edges are now explicit instead of hidden:
- the injector is deliberately conservative; ambiguous matches should fail loudly instead of guessing
- missing `target_conf` paths should be treated as operator-fixable discovery issues, not magic-recoverable state
- admin UI uses a narrow sudo-assisted apply helper because full apply requires nginx reload + Authelia restart
- this is a browser-first perimeter shell, not a “protect everything” button

## Key references

Start here if you are actively validating or operating it:
- config model: `docs/CONFIG-MODEL.md`
- policy pivot notes: `docs/POLICY-MODEL-PIVOT.md`
- pre-install checklist: `docs/PRE-INSTALL-CHECKLIST.md`
- emergency disable / break-glass: `docs/EMERGENCY-DISABLE.md`
- operator first boot: `docs/OPERATOR-FIRST-BOOT.md`
- current live validation checklist: `docs/LIVE-VALIDATION-CHECKLIST.md`
- wm3v-specific live plan: `docs/WM3V-INJECTION-LIVE-PLAN.md`
- earlier install-state lessons: `docs/2026-03-26-INSTALL-HANDOFF.md`

## Branding

- product name: **MFA Sidecar**
- engine: **Authelia**
- temporary logo/icon: official Authelia logo
