# MFA Sidecar Install Guide

This guide is for installing and safely bringing MFA Sidecar online.

## What you are installing

MFA Sidecar is a dedicated authentication/MFA layer that sits in front of selected YunoHost web apps.

It installs:

- a dedicated portal domain, typically something like `auth.example.tld`
- a sidecar-owned authentication + MFA user store
- an operator admin UI at `/admin`
- a YunoHost config panel for high-level settings and operational actions

## Before you install

Understand these rules first:

- the portal domain should be **dedicated** to the sidecar
- the portal path should remain `/`
- you should **not** plan to protect the root domain first
- your first real test target should be a simple non-root app, ideally on a dedicated subdomain

Good first target examples:

- HomeBox on its own subdomain
- another simple app at `/` on a dedicated host

Bad first target examples:

- the root domain
- the sidecar portal domain itself
- the one app you need in order to recover if something breaks

## Install questions and what they mean

### Domain

This is the dedicated sidecar portal domain.

Example:

- `auth.example.tld`

This should not be shared with another app.

### Path

Must remain `/`.

The portal wants a dedicated domain, not a shared path.

### Portal subdomain label

Used for generated examples and future redirects.

### Default policy

This affects the initial posture for newly added targets.

Choices:

- **Public by default / open**
- **Protected by default**

Recommendation: keep the mindset conservative and verify targets intentionally. In practice, operators should still treat unknown/discovered things as **Bypass until tested**.

### Remembered session duration

How long a remembered sidecar session can last.

Shorter = more reauthentication.
Longer = more convenience.

### Default upstream scheme / host / port

These seed initial assumptions for generated target routing.

They are not holy truth.

You may still need to inspect or override per-target behavior if nginx/upstream reality differs.

### First sidecar admin

This is the first operator account for the sidecar itself.

You will provide:

- username
- display name
- email
- password

This user is the initial **Admin** and is what makes the portal immediately usable after install.

## What you should see after install

You should end up with:

- portal reachable at `https://your-portal-domain/`
- admin UI reachable at `https://your-portal-domain/admin`
- users page reachable at `https://your-portal-domain/admin/users`
- YunoHost config panel populated for higher-level controls

## First post-install checks

Do these before protecting anything important.

### 1. Verify the portal loads

Open the portal domain and confirm the sidecar is alive.

### 2. Verify the admin UI loads

Open:

- `/admin`
- `/admin/users`

### 3. Verify the first admin user exists and works

Do not skip this.

### 4. Verify the docs exist on the box

They should install into the package install dir, typically something like:

- `$install_dir/README.md`
- `$install_dir/docs/INSTALL.md`
- `$install_dir/docs/ADMIN.md`
- `$install_dir/docs/USERS.md`
- `$install_dir/docs/TROUBLESHOOTING.md`

## First rollout after install

### Recommended order

1. install sidecar
2. verify portal and admin surfaces
3. confirm first admin works
4. choose one non-root target
5. set it to **Protect**
6. test in a private/incognito window
7. validate redirect → login → MFA → return-to-app
8. expect first-time users to stop at MFA enrollment before the flow is fully smooth
9. after sidecar auth succeeds, confirm the downstream app behaves as expected (it may still present its own login)
10. only then move to more important or broader targets

## Default MFA method

This package currently defaults to **TOTP/authenticator app** enrollment and leaves WebAuthn disabled by default.

That is intentional for now:

- TOTP is easier to explain
- TOTP is easier to recover
- TOTP is less likely to confuse first-time operators and users than passkey/security-key prompts

WebAuthn can return later once the operator and user flows are fully nailed down.

## Things to avoid right after install

Do not do these first:

- protect the root domain
- protect the portal domain
- promote everyone to admin
- assume discovered upstream values are automatically safe
- trust a previously logged-in browser without incognito testing

## Recovery mindset

If something goes wrong, the safest control is usually:

```yaml
access_control:
  enforcement_enabled: false
```

in the package install dir policy file, typically:

- `$install_dir/config/domain-policy.yaml`

Then reload runtime.

That bypasses protection globally without deleting your config.

## Related docs

- Operator workflow: `docs/ADMIN.md`
- End-user experience: `docs/USERS.md`
- Break-glass + debugging: `docs/TROUBLESHOOTING.md`
