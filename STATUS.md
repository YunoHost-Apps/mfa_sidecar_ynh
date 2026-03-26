# STATUS.md — MFA Sidecar

## Current phase
Alpha candidate packaged and pre-install validated

## Current recommendation
Use **Authelia** as the sidecar auth engine in front of selected YunoHost-managed domains, with:
- passkeys / WebAuthn primary
- TOTP fallback
- YunoHost LDAP as first-factor identity source
- PostgreSQL for durable state
- thin custom control plane for managed host/path entries and generated config

## Why this path currently leads
- cleanest fit to the gatekeeper model
- removable without invading YunoHost internals
- supports the desired passkeys-first posture
- lighter and more sidecar-shaped than a full IdP platform

## Current open questions
- exact recovery-code/operator recovery strategy for v1/alpha
- whether the temporary `/admin` shared-secret gate is acceptable for first live install or needs one more UX pass afterward
- when to reduce root-biased service execution toward a cleaner least-privilege model

## Current checkpoint
The repo is now in a **snapshot-first installable alpha state**:
- package lifecycle scripts are in place
- policy seed + renderer + runtime staging are aligned
- bundled admin UI works for add/edit/delete/toggle/apply
- simplified YunoHost-first discovery is implemented and smoke-covered
- wm3v read-only/live inventory validation has been recorded
- full smoke suite currently passes

## Immediate next step
Take a VM snapshot, perform the first real install on the dedicated portal domain, set the real LDAP bind password, and validate the first managed-site flow end to end on wm3v.
