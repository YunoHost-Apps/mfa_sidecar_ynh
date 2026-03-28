# MFA Sidecar Operator Guide

This guide is for the person running the server.

If you are the operator, your job is not just to click **Protect**. Your job is to know **what you are protecting, how to recover, and how to avoid locking yourself out**.

## The big picture

MFA Sidecar sits in front of selected YunoHost web apps and decides whether requests should:

- pass through normally (**Bypass**)
- or be forced through sidecar authentication/MFA (**Protect**)

It does this at the **host + path** level.

Examples:

- `home.example.tld /`
- `example.tld /nextcloud`
- `git.example.tld /gitlab`

That means the operator surface is about **routing and protection policy**, not just “is MFA enabled somewhere.”

## Admin surfaces

### YunoHost config panel

Use the config panel for:

- reviewing high-level runtime state
- adjusting default policy
- adjusting remembered session duration
- saving default upstream values
- reloading runtime
- emergency/break-glass actions
- syncing or seeding users in coarse ways

### Sidecar admin UI

Use the sidecar admin UI for:

- curated target management
- discovery review
- Protect/Bypass toggling
- global enforcement state
- sidecar user administration

Main pages:

- `/admin` → targets and protection policy
- `/admin/users` → sidecar user administration

## Terms that matter

### Protect

A protected target requires sidecar authentication before the downstream app is reached.

### Bypass

A bypassed target remains visible without sidecar enforcement.

Bypass is **not an error state**. It is the normal safe default until you explicitly choose otherwise.

### Global enforcement disabled

When global enforcement is disabled, the package keeps its configuration and target list, but protection is bypassed everywhere.

This is the main break-glass control.

## Safe rollout process

### 1. Start with a dedicated subdomain app

Good first targets:

- HomeBox on its own subdomain
- any simple app living at `/` on a dedicated host

Avoid starting with:

- the root domain
- the sidecar portal domain
- anything you rely on for recovery before you have tested the flow

### 2. Use an incognito/private window

Cached sessions can lie to you.

When testing protection, use a clean browser state so you can see the real redirect/login/MFA behavior.

### 3. Confirm the full loop

For one protected target, validate all of this:

1. anonymous request hits protected target
2. request redirects to sidecar portal
3. login succeeds
4. MFA succeeds
5. browser returns to the original target
6. app loads correctly

If that loop does not work cleanly, do **not** move to more dangerous targets.

## Dangerous targets

These deserve special caution:

### The portal domain

Example:

- `auth.example.tld /`

If you break this badly enough, you can cut off the very surface you need to fix the rest.

### The root domain

Example:

- `example.tld /`

This can affect a wide range of paths and services and is easy to underestimate.

### Why the admin UI warns on these

Because the warning is earned.

The package intentionally asks you to test on a non-root target first before enabling protection on root/portal-style entries.

## Global enforcement switch

The package policy file contains:

```yaml
access_control:
  enforcement_enabled: true
```

If you set this to `false`, then regenerate/reload runtime, sidecar protection is bypassed globally.

This is the preferred recovery model because it is:

- explicit
- documented
- reversible
- less destructive than ripping files out by hand

## User administration

The sidecar has its own user store.

### Why

Because the sidecar needs its own authentication/MFA model and recovery path.

### What admins can do

From `/admin/users`, admins can:

- view users
- create/update users
- set/reset passwords
- reset MFA enrollment
- disable/enable users
- set role to **User** or **Admin**
- clear active sessions globally from the main admin page

### Recommended role model

- only actual operators should be **Admin**
- everyone else should be **User**

If everybody is admin, the page is lying and the model is broken.

## Roles

### User

Normal sidecar user.

### Admin

Operator with access to admin-level UI and recovery actions.

Only give this to people who should be able to change protection state or recover users.

## Password resets vs MFA resets

### Set/reset password

Changes the sidecar password for that user.

### Reset MFA

Clears stored MFA enrollment data so the user must enroll again.

Use this when:

- a device is lost
- enrollment is corrupted
- recovery is needed after an authentication problem

This is intentionally a confirmed action because it affects the next login.

## Clear active sessions

The admin UI exposes **Clear active sessions (force re-login)**.

In the current package setup, this works by restarting Authelia. Because the current session provider is memory-backed by default, active sessions are destroyed and users need to reauthenticate.

This is a blunt instrument. Use it intentionally.

## Upstream defaults

The config panel lets you define default upstream values.

These are seeds, not truth.

They help with initial generated entries, but the operator should still verify real upstream behavior, especially on root-domain/path-based apps.

## Practical operating rules

### Good rules

- start small
- test in private browsing
- promote one target at a time
- leave uncertain targets in **Bypass** until verified
- keep recovery paths simple
- write down what you changed

### Bad rules

- protect the root domain first
- assume discovery is always right
- assume every downstream upstream is safe because nginx found *something*
- silently mass-promote users to admin
- hide recovery controls because they feel ugly

## Suggested first production checklist

- [ ] portal loads cleanly
- [ ] admin UI loads cleanly
- [ ] first admin user works
- [ ] `/admin/users` reflects expected roles
- [ ] one non-root target protected successfully
- [ ] incognito test passes
- [ ] global disable path understood
- [ ] operator knows where `domain-policy.yaml` lives
- [ ] operator knows where `users.yml` lives

## Files worth knowing

- policy: `/opt/yunohost/mfa_sidecar/config/domain-policy.yaml`
- sidecar users: `/etc/mfa-sidecar/authelia/users.yml`
- generated runtime: `/opt/yunohost/mfa_sidecar/deploy/generated-alpha/`
- staged nginx/Authelia files: `/etc/mfa-sidecar/`

## Final operator advice

If you are unsure whether to Protect or Bypass something, the answer is usually **Bypass for now**.

A boring, understandable system beats an impressive lockout.