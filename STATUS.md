# STATUS.md — MFA Sidecar

## Current phase
Production hardening / live-validation gap closure

## Current recommendation
Use **Authelia** as the sidecar auth engine in front of selected YunoHost-managed domains, with:
- passkeys / WebAuthn primary
- TOTP fallback
- YunoHost LDAP as first-factor identity source
- PostgreSQL for durable state
- thin custom control plane for per-domain on/off and generated config

## Why this path currently leads
- cleanest fit to the gatekeeper model
- removable without invading YunoHost internals
- supports the desired passkeys-first posture
- lighter and more sidecar-shaped than a full IdP platform

## Current open questions
- Nginx vs Caddy as proxy layer for alpha
- exact recovery-code strategy for v1/alpha
- whether Authelia is sufficient alone or needs a thin add-on for admin/policy ergonomics

## Immediate next step
Run the next live target validation pass against wm3v with the now-hardened `/admin` control plane (add/edit/delete/toggle), confirm the managed-site workflow on real host/path entries, and close the remaining production blockers: root-run services, placeholder LDAP bind secret, and any lifecycle/rollback surprises that only show up on the real box.
