# MFA Sidecar Submission / Reviewer Notes

This file is a reviewer-facing summary.

It is intentionally short, opinionated, and focused on what matters for evaluating the package.

## What MFA Sidecar is

MFA Sidecar adds an Authelia-based MFA perimeter in front of selected YunoHost apps and paths.

It exists to cover a real gap: YunoHost's normal SSO path does not provide native MFA for arbitrary downstream apps.

The package provides:

- a dedicated sidecar portal domain
- a sidecar admin UI
- sidecar-owned user management and MFA recovery actions
- generated Authelia config and nginx auth-request snippets
- managed injection into selected app nginx locations
- break-glass controls via explicit policy state

## What makes this package more than a thin wrapper

This is not just “package upstream app X”.

It includes:

- custom policy/render/apply pipeline
- custom admin/user management UI
- YunoHost-aware discovery of domains and apps
- runtime reinjection hooks for nginx regeneration and upgrades
- explicit operator and recovery documentation

## Major design choices

### TOTP first, WebAuthn off by default

The package currently defaults to TOTP enrollment and disables WebAuthn by default.

This is deliberate for now:

- easier to explain
- easier to recover
- less confusing during first-run validation

### Admin UI on localhost only

The admin UI binds to loopback and relies on the YunoHost/nginx fronting layer for operator auth.

This is a documented trust boundary, not an accident.

### Marker-based nginx injection

Managed auth blocks are inserted into target nginx locations with explicit markers so the package can reinject/remove them deterministically.

This is the main maintenance surface and is treated accordingly in tests/docs.

### Vendored Authelia binary

The package ships a pinned Authelia release artifact and verifies it with sha256.

This is an explicit supply-chain tradeoff made for YunoHost packaging practicality.

## What has been validated so far

### Live-box validation

On a real YunoHost box, the following has been demonstrated:

- protected-target auth interception works
- SSOwat bypass in the internal auth subrequest location was required and is implemented
- Authelia 4.39 auth-request header contract was corrected
- TOTP enrollment flow works
- subsequent protected access works
- downstream app handoff can still lead to the app's own login, which is now documented

### Repo-local regression coverage

The repo now includes a smoke/regression suite for the live failures already encountered, including:

- auth-request headers
- redirect handoff
- SSOwat bypass
- protected snippet generation
- reinjection behavior
- packaged-file sanity
- MFA method rendering behavior

## Remaining pre-submission checks

The main remaining release gate for `0.3.0` is:

- real-box break-glass behavior with `enforcement_enabled: false`

Still worth validating before wider public submission/catalog expectations:

- one or more multi-domain common setups
- additional real-box uninstall/restore cleanliness checks if practical

## Security posture summary

The package has had focused review and hardening around:

- shell/script safety
- file permissions
- sudo scope
- password handling in subprocesses
- CSRF on admin POST actions
- route validation
- operator-readable trust boundaries

It is not claiming to be perfect. It is aiming to be explicit, reviewable, and operable under stress.

## Reviewer mindset we recommend

Judge this package less like a toy wrapper and more like an infrastructure integration layer.

The key questions are:

- are the trust boundaries understandable?
- are the lifecycle operations honest and recoverable?
- are the sharp edges documented?
- does the package help an operator succeed under pressure?

That is the standard the project is trying to meet.
