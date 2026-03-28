# MFA Sidecar for YunoHost

MFA Sidecar is a browser-first MFA perimeter for selected YunoHost web apps.

It gives you a dedicated authentication portal, a sidecar-owned user store, and an operator control plane for deciding **which host/path combinations are protected** and which are intentionally bypassed.

This package is designed for people who want a practical MFA layer in front of existing YunoHost web apps **without pretending every app natively understands MFA**.

## What this package does

- installs a dedicated **portal** on its own domain, typically something like `auth.example.tld`
- installs a vendored, pinned **Authelia** binary
- keeps a separate **sidecar users file** for authentication and MFA enrollment
- discovers YunoHost app locations and exposes them in an admin UI
- lets operators choose whether each location is:
  - **Protect** — requires sidecar auth/MFA
  - **Bypass** — visible without sidecar enforcement
- supports a global **enforcement_enabled** safety switch so the whole protection layer can be bypassed without destroying config

## What this package does not do

- it does **not** magically make every downstream app MFA-aware
- it does **not** replace YunoHost’s own admin model
- it does **not** assume every root domain should be protected immediately
- it does **not** treat “more secure” and “less likely to lock you out” as the same thing

This package is intentionally operator-biased. It assumes you want safety rails and reversibility.

## Core surfaces

### 1. The portal

Example:

- `https://auth.example.tld/`

This is the sidecar login/MFA portal.

### 2. The admin UI

Example:

- `https://auth.example.tld/admin`
- `https://auth.example.tld/admin/users`

This is the operator control plane.

Use it to:

- review discovered targets
- protect/bypass targets
- manage sidecar users
- reset passwords
- reset MFA enrollment
- clear active sessions
- disable/re-enable enforcement globally

### 3. The YunoHost config panel

Use the YunoHost config panel for:

- high-level settings
- session duration
- default policy
- upstream defaults
- service actions
- operator-safe recovery actions

Use the **admin UI** for detailed day-to-day control.

## Mental model

Think of MFA Sidecar as three layers:

1. **Operator settings**
   - install choices
   - upstream defaults
   - remembered session duration
   - global enforcement state

2. **Protected targets**
   - host/path entries that are either **Protect** or **Bypass**
   - examples:
     - `home.example.tld /`
     - `example.tld /nextcloud`
     - `git.example.tld /gitlab`

3. **Sidecar users**
   - users who authenticate to the sidecar itself
   - separate from app-local users
   - can be synced from YunoHost or managed manually

## Recommended rollout order

Do **not** start with the portal domain or the root domain.

Recommended order:

1. install sidecar on a dedicated portal domain
2. verify the admin UI loads
3. create/verify your first admin user
4. protect **one non-root app first**
   - a good candidate is a dedicated subdomain app like HomeBox
5. validate the full login/MFA/return flow in an incognito window
6. only then consider protecting root-domain paths or more important apps
7. only after that consider protecting especially sensitive/root-level targets

## Safety rules this package intentionally follows

- default mindset: **Bypass unless explicitly enabled**
- unmanaged discoveries should be treated as **not yet protected**
- root domain and portal domain are **danger targets** and deserve extra confirmation
- global disable should be easy
- recovery should be obvious enough for a human under stress

## Documentation map

- **Operator/Admin guide:** `docs/OPERATOR-GUIDE.md`
- **User guide:** `docs/USER-GUIDE.md`
- **Recovery + troubleshooting:** `docs/TROUBLESHOOTING.md`

## Important recovery setting

The package policy file includes:

```yaml
access_control:
  enforcement_enabled: true
```

If you set this to `false` and reload runtime, sidecar protection is globally bypassed while keeping the rest of the config intact.

This is the primary break-glass control.

## Important paths

- install dir: `/opt/yunohost/mfa_sidecar`
- data dir: `/var/lib/mfa_sidecar`
- policy file: `/opt/yunohost/mfa_sidecar/config/domain-policy.yaml`
- Authelia config: `/etc/mfa-sidecar/authelia/configuration.yml`
- sidecar users: `/etc/mfa-sidecar/authelia/users.yml`
- portal/nginx assets: `/etc/mfa-sidecar/nginx/`

## Versioning

This package uses the YunoHost convention:

- `0.1.3` = package/app release line
- `~ynhN` = YunoHost packaging revision

Example:

- `0.1.3~ynh4`

## Status

This package is currently in active operator-hardening. Expect iteration, but the intent is clear:

- fewer surprises
- better recovery
- better admin ergonomics
- documentation that explains the system like the authors actually use it
