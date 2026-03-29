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

This is an explicit supply-chain and operational reliability tradeoff, not an accidental shortcut.

Why this package currently prefers the vendored model:

- MFA Sidecar is a security perimeter; unexpected upstream fetch failures or release drift can break real login paths for whole YunoHost installs
- the packaged artifact is exactly the one exercised in real-box validation, which reduces "upstream moved and now install/upgrade behavior changed underneath us" risk
- the package still verifies the artifact cryptographically instead of treating the vendored tarball as blind trust

In other words: this package is intentionally optimizing for reproducible installs and upgrades on a security-sensitive integration surface, even though that is somewhat less aligned with generic YunoHost packaging preference.

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

## Release status / remaining checks

`0.3.0` is now justified by real-box validation.

The release-closing work that mattered most was:

- real-box break-glass behavior with `enforcement_enabled: false`
- live proof that missing nginx auth-endpoint bridge includes were fixed
- live proof that subpath-mounted targets work after slash-normalized matcher fixes
- live proof that disable / re-enable no longer strands targets in half-rolled-back nginx state

Still worth validating before wider public submission/catalog expectations:

- one or more multi-domain common setups
- additional real-box uninstall/restore cleanliness checks if practical
- package_check baseline for the release candidate

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
