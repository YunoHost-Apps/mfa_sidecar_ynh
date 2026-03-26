# STATUS.md — MFA Sidecar

## Current phase
Browser-first v1 perimeter shell confirmed; operator bootstrap/config UX and live package footguns still need cleanup

## Current recommendation
Use **Authelia** as the sidecar auth engine for a **browser-first perimeter shell** in front of selected YunoHost-managed web apps, with:
- passkeys / WebAuthn primary
- TOTP fallback
- separate sidecar-owned credential + MFA store
- thin custom control plane for managed host/path entries and generated config
- remembered-device/session behavior to reduce repeat prompts
- explicit non-goal for v1: mail protocols, sync/mobile-client-first apps, and generic protocol-wide firewall behavior

## Why this path currently leads
- cleanest fit to the gatekeeper model
- removable without invading YunoHost internals
- supports the desired passkeys-first posture
- lighter and more sidecar-shaped than a full IdP platform

## Current open questions
- exact recovery-code/operator recovery strategy for first live install
- whether the temporary `/admin` shared-secret gate is acceptable for first live install or needs one more UX pass afterward
- whether YunoHost-driven user sync should eventually become automatic/scheduled rather than operator-triggered only
- how the operator bootstrap/config story should look so a fresh install does not strand the user at a login page with no obvious way to create users or define protected targets

## Current checkpoint
The repo is now in a **documented alpha package state with strong local validation**, and wm3v live proof established several truths:
- package lifecycle scripts are in place
- policy seed + renderer + runtime staging are aligned
- bundled admin UI works for add/edit/delete/toggle/apply
- direct Authelia portal is live and reachable once bootstrap/user and permission bugs are corrected
- GitHub `main` is the installer-facing package branch, while GitLab mirrors that package view on `github-package`
- browser-first perimeter-shell framing is the right v1 scope; protocol-wide/firewall-like behavior is out of scope for now
- current install still has operator-footgun bugs: stale publish drift was possible, generated runtime file permissions were wrong, and first-user bootstrap is too manual/fragile
- first-run UX is still poor: the operator can land on a login page without a clear obvious path to create users or define what gets protected

## Immediate next step
Fix the operator/bootstrap UX and remaining package footguns, then re-validate the intended v1 flow on a compatible browser-first target app.
