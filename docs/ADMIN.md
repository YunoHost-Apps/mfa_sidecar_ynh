# MFA Sidecar Admin Guide

This guide is for the operator.

Your job is not just to click **Protect**. Your job is to understand what the sidecar is protecting, how the recovery path works, and how to avoid creating your own outage.

## Admin surfaces

### YunoHost config panel

Use the config panel for:

- high-level settings
- session duration
- default policy
- upstream defaults
- runtime reloads
- coarse recovery/service actions

### Sidecar admin UI

Use the sidecar admin UI for day-to-day control:

- `/admin` → targets and enforcement state
- `/admin/users` → user administration

This is the real operator surface.

## The protection model

Targets are evaluated at the **host + path** level.

Examples:

- `home.example.tld /`
- `example.tld /nextcloud`
- `git.example.tld /gitlab`

Every target is either:

- **Protect** → require sidecar auth/MFA
- **Bypass** → no sidecar enforcement

### Important meaning of Bypass

Bypass is not a failure state.

It is the safe intentional state for anything you have not explicitly validated.

## Global enforcement

The policy file contains:

```yaml
access_control:
  enforcement_enabled: true
```

When this becomes `false`, sidecar protection is bypassed globally while the rest of the configuration stays intact.

That is the main break-glass mechanism.

The admin UI should make this obvious.

## Dangerous targets

These are the highest-risk places to enable protection:

### Portal domain

Example:

- `auth.example.tld /`

If you break this badly enough, you can damage the very surface you need to recover.

### Root domain

Example:

- `example.tld /`

This can affect a lot more services than it first appears to.

### Operator rule

Do not enable protection on a root/portal-style target before you have already proven the flow on a non-root target.

## Recommended rollout

1. start with a dedicated subdomain app
2. use an incognito/private window
3. verify redirect → login → MFA → return-to-app
4. only then widen coverage

## User administration

The sidecar has its own user store.

### Why

Because the sidecar needs its own authentication and MFA recovery model.

### What admins can do

From `/admin/users`:

- view users
- create/update users
- set/reset password
- reset MFA enrollment
- enable/disable users
- set role to **User** or **Admin**

### Role model

- only operators should be **Admin**
- normal people should be **User**

If everyone is admin, the model is lying.

## Default MFA method

This package currently defaults to **TOTP/authenticator app** enrollment and leaves WebAuthn disabled by default.

That is intentional for now:

- TOTP is easier to explain
- TOTP is easier to recover
- TOTP is less likely to confuse first-time operators and users than passkey/security-key prompts

WebAuthn can return later once the operator and user flows are fully nailed down.

## Password resets vs MFA resets

### Password reset

Changes the user’s sidecar password.

### MFA reset

Clears stored MFA enrollment data so the user must enroll again.

Use this for:

- lost device
- authenticator migration
- broken enrollment
- auth recovery

## Clear active sessions

The admin UI offers **Clear active sessions (force re-login)**.

In the current package setup, this restarts Authelia and destroys memory-backed sessions, forcing users to reauthenticate.

It is intentionally blunt.

## Upstream defaults

The config panel lets you save default upstream values.

These are seeds, not sacred truth.

On path-based/root-domain apps especially, verify the real upstream behavior rather than trusting discovery blindly.

## Good operator habits

- start small
- test with clean browser state
- change one target at a time
- keep uncertain targets in Bypass
- know your break-glass path before you need it
- document what changed when something is weird

## Bad operator habits

- protect the root domain first
- treat discovery as infallible
- mass-promote users to admin because it is convenient
- hide or avoid recovery controls because they look scary
- improvise “clever” recovery when a simple documented path exists

## Important paths

- policy: `/opt/yunohost/mfa_sidecar/config/domain-policy.yaml`
- sidecar users: `/etc/mfa-sidecar/authelia/users.yml`
- generated runtime: `/opt/yunohost/mfa_sidecar/deploy/generated-alpha/`
- runtime metadata: `/etc/mfa-sidecar/runtime-metadata.json`
- staged nginx/Authelia files: `/etc/mfa-sidecar/`

## Checklist for a sane deployment

- [ ] portal loads
- [ ] admin UI loads
- [ ] users page loads
- [ ] first admin works
- [ ] non-admin users are actually `users`, not everybody-as-admin nonsense
- [ ] one non-root target protected successfully
- [ ] incognito test passes
- [ ] global enforcement off path understood

## Related docs

- Install and first rollout: `docs/INSTALL.md`
- End-user experience: `docs/USERS.md`
- Troubleshooting/recovery: `docs/TROUBLESHOOTING.md`
