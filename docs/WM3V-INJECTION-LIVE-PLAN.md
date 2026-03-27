# wm3v live validation plan — injection/reinjection architecture

This plan assumes the current package model:
- portal on its own dedicated domain at `/`
- first protected target: `home.wm3v.com`
- protected apps use **managed block injection into existing nginx `location` blocks**
- reinjection occurs after `regen-conf` / app lifecycle events

## Recommended target choices
- **Portal domain:** `auth.wm3v.com`
- **First protected target:** `home.wm3v.com`
- **Expected first target conf:** `/etc/nginx/conf.d/home.wm3v.com.d/homebox.conf`

Why this is the right first proof:
- earlier wm3v read-only validation showed `home.wm3v.com` / Homebox is a simple reverse-proxy app
- its nginx shape is much safer for first injection proof than a Nextcloud-class config
- if this fails, we learn about the injection model without dragging DAV/rewrite/websocket complexity into the first blast radius

## Before touching wm3v
1. Prefer a **Proxmox snapshot** first.
2. If no snapshot restore is being used, perform the cleanup from `docs/2026-03-26-INSTALL-HANDOFF.md`.
3. Confirm installer-facing branch is the intended one on GitHub.
4. Have break-glass steps ready from `docs/EMERGENCY-DISABLE.md`.
5. If the portal domain was recently added and nginx behaves like it has no parent server block for that host, run `yunohost tools regen-conf nginx --force` before chasing sidecar ghosts.

## Install / bootstrap sequence
1. Install MFA Sidecar on **`auth.wm3v.com` at `/`**.
2. Confirm:
   - `/etc/mfa-sidecar/authelia/users.yml` exists
   - `/etc/mfa-sidecar/mfa-sidecar.env` exists
   - `/etc/mfa-sidecar/nginx/portal.conf` exists
3. Use the config panel action to create the **first sidecar user**.
4. Retrieve `MFA_SIDECAR_ADMIN_GATE_SECRET`.
5. Validate:
   - portal loads
   - `/admin` is reachable with the gate secret

## First managed-target validation (`home.wm3v.com`)
1. Add managed target for:
   - host: `home.wm3v.com`
   - path: `/`
   - initial state: protected
2. In `/admin`, verify the discovered or selected **target nginx conf** is:
   - preferably `/etc/nginx/conf.d/home.wm3v.com.d/homebox.conf`
3. If discovery picks something else, **do not trust it blindly**.
   - inspect the actual file
   - set `target_conf` manually if needed

## On-host verification after apply
Inspect the target file and confirm:
- the managed MFA Sidecar block appears inside the intended `location` block
- existing Homebox proxy directives remain intact
- no duplicate managed blocks were added

Then run:
- `nginx -t`
- reload nginx only if config test passes

## Browser behavior checks
Confirm:
1. unauthenticated request to `home.wm3v.com` redirects to `auth.wm3v.com`
2. successful login returns to `home.wm3v.com`
3. Homebox still behaves like Homebox, not like a generic proxy casualty

## Reinjection checks
After the first target works:
1. run `yunohost tools regen-conf nginx`
2. confirm the managed block is restored correctly in the Homebox nginx file
3. confirm no duplicate MFA Sidecar blocks appear
4. if practical, test an app lifecycle event likely to rewrite nginx (upgrade or equivalent safe re-render path)

## Emergency-disable proof
Run emergency disable and verify:
- portal include hook is removed
- managed blocks are removed from the Homebox nginx conf
- `home.wm3v.com` becomes reachable again without sidecar gating
- sidecar artifacts remain on disk for recovery

## If this first proof passes
Then consider the next tier:
- a root-path app on `wm3v.com`
- only after that, a more complex app/path like Nextcloud-related locations

## If it fails
Capture immediately:
- the exact discovered/selected `target_conf`
- the target nginx file before and after apply
- `nginx -t` output
- `journalctl -u mfa-sidecar-admin -u mfa-sidecar-authelia -n 120 --no-pager`
- whether failure was:
  - wrong target file
  - missing location block
  - ambiguous location block
  - nginx syntax failure
  - runtime auth failure
  - reinjection failure

## Success bar
Call the injection/reinjection architecture live-proven on wm3v only if all of these are true:
- target discovery is correct or operator-overridable without drama
- the managed block lands in the right Homebox location block
- nginx remains valid
- auth redirect works
- Homebox still works normally
- regen-conf restores protection without duplication
- emergency disable cleanly restores access
