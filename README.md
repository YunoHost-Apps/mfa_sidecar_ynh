# MFA Sidecar for YunoHost

<p align="center">
  <img src="assets/logo.jpg" alt="MFA Sidecar logo" width="160" />
</p>

MFA Sidecar is a browser-first MFA perimeter for selected YunoHost web apps.

It gives you:

- a dedicated authentication portal
- a sidecar-owned user store
- an operator control plane for deciding which host/path combinations are **Protect** vs **Bypass**
- a break-glass model that is explicit and reversible

This package exists for the very practical problem of putting MFA in front of existing web apps **without pretending every app natively understands MFA**.

## Start here

This package now documents itself around the three surfaces people actually care about:

- **Install** → `docs/INSTALL.md`
- **Admin** → `docs/ADMIN.md`
- **Users** → `docs/USERS.md`

If something is broken or you need a break-glass path:

- **Troubleshooting / Recovery** → `docs/TROUBLESHOOTING.md`
- **Testing / smoke regressions** → `docs/TESTING.md`

## Core idea

MFA Sidecar protects YunoHost web apps at the **host + path** level.

Examples:

- `home.example.tld /`
- `example.tld /nextcloud`
- `git.example.tld /gitlab`

Each target is either:

- **Protect** → require sidecar authentication/MFA before the downstream app
- **Bypass** → allow normal access without sidecar enforcement

Bypass is not failure. It is the intentionally safe default until you explicitly choose otherwise.

## Main surfaces

### Portal

Example:

- `https://auth.example.tld/`

This is where end users authenticate and complete MFA.

### Admin UI

Examples:

- `https://auth.example.tld/admin`
- `https://auth.example.tld/admin/users`

This is where operators manage targets, users, sessions, and enforcement state.

### YunoHost config panel

This is for higher-level configuration and operational actions:

- default policy
- session duration
- upstream defaults
- reload/runtime actions
- recovery-oriented controls

## What this package intentionally does

- installs a dedicated portal on its own domain
- installs a vendored pinned Authelia binary
- keeps a sidecar-specific users file for auth and MFA enrollment
- discovers YunoHost app locations and presents them in an operator UI
- supports a global `enforcement_enabled` safety switch
- aims to be operable by a human under stress

## What it intentionally does not do

- it does not magically make downstream apps MFA-aware
- it does not replace YunoHost’s own admin model
- it does not assume every root-domain target should be protected immediately
- it does not conflate “more secure” with “less likely to lock you out”

## Safety model

This package intentionally leans conservative:

- default mindset: **Bypass unless explicitly enabled**
- root domain and portal domain are danger targets
- global disable is meant to be easy and documented
- recovery should be obvious, not clever

## Important recovery setting

The policy file contains:

```yaml
access_control:
  enforcement_enabled: true
```

If you set this to `false` and reload runtime, sidecar protection is bypassed globally while the rest of the configuration stays intact.

This is the primary break-glass mechanism.

## Important paths

- install dir: `/opt/yunohost/mfa_sidecar`
- data dir: `/var/lib/mfa_sidecar`
- policy file: `/opt/yunohost/mfa_sidecar/config/domain-policy.yaml`
- sidecar users: `/etc/mfa-sidecar/authelia/users.yml`
- Authelia config: `/etc/mfa-sidecar/authelia/configuration.yml`
- portal/nginx assets: `/etc/mfa-sidecar/nginx/`

## Licensing

- MFA Sidecar license: `LICENSE`
- Third-party notices: `THIRD_PARTY_NOTICES.md`
- Vendored Authelia license copy: `licenses/Authelia-Apache-2.0.txt`

## Versioning

This package uses the normal YunoHost versioning convention:

- package/app line: `0.2.0`
- YunoHost revision: `~ynhN`

Example:

- `0.2.0~ynh1`

## Tone / intent

The goal is not to make people say:

> wow, cool program

The goal is to make them say:

> wow, these people actually know how this should be operated

That means the docs are part of the product, not garnish.
