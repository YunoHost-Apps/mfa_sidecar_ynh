# STATUS.md — MFA Sidecar

## Current phase
Production-hardening candidate packaged, but live install flow still needs clean-host validation

## Current recommendation
Use **Authelia** as the sidecar auth engine in front of selected YunoHost-managed domains, with:
- passkeys / WebAuthn primary
- TOTP fallback
- separate sidecar-owned credential + MFA store
- optional read-only YunoHost username/email discovery later if needed
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
The repo is now in a **documented alpha package state with strong local validation**, but tonight's wm3v attempts showed that the live install path can still be derailed by stale YunoHost/systemd host state:
- package lifecycle scripts are in place
- policy seed + renderer + runtime staging are aligned
- bundled admin UI works for add/edit/delete/toggle/apply
- simplified YunoHost-first discovery is implemented and smoke-covered
- wm3v read-only/live inventory validation has been recorded
- full smoke suite currently passes
- installer-facing package branch is `github-package`
- live wm3v retries produced evidence of stale/cached older unit definitions during install transactions

## Immediate next step
Start from a clean host state (preferably snapshot restore), follow `docs/2026-03-26-INSTALL-HANDOFF.md`, and only then perform the next install attempt on the dedicated portal domain.
