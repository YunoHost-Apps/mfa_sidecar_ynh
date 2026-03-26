# PLAN.md — MFA Sidecar

## Goal
Build an alpha-capable removable YunoHost companion app that provides a front-door auth layer with:
- passkeys / WebAuthn as primary MFA
- TOTP as fallback
- recovery path
- remembered-device / remembered-session duration
- per-domain binary on/off protection
- default-protect-new-domains option

YunoHost should continue to handle its own normal LDAP/app login/session behavior after the request is allowed through the sidecar.

## Product thesis
This is not a replacement identity platform for YunoHost.
This is a **gatekeeper** that sits in front of selected YunoHost-managed domains and either:
- allows the request through, or
- requires sidecar authentication first.

## V1 scope
- Removable sidecar architecture
- Separate Authelia credential + MFA store (hashed/salted, independent of YunoHost auth)
- Optional read-only YunoHost identity/contact sync for username/email seeding or recovery context
- Sidecar MFA engine: passkeys first, TOTP fallback
- Shared auth session across protected domains
- Public/unprotected domains remain untouched
- Per-domain on/off toggle in admin UI/control plane
- Default protect new domains option
- Reasonable remembered-session duration policy
- Alpha implementation sufficient to validate architecture and user flows

## Non-goals for v1
- Patching YunoHost core auth/login flows
- Building a custom mobile app
- Proprietary push notification ecosystems
- Per-app deep integration with downstream applications
- Full IAM/IdP replacement for YunoHost

## Recommended stack (current)
- Reverse proxy layer: Nginx first choice; Caddy acceptable alternative
- Sidecar auth engine: Authelia
- Sidecar identity store: separate Authelia-managed credential/MFA store
- Optional directory/contact feed: YunoHost LDAP read-only for username/email discovery only
- Storage: PostgreSQL (or Authelia-supported durable store as implementation settles)
- Thin custom control plane for domain toggles + generated config
- TOTP fallback and WebAuthn provided by auth engine where practical

## Milestones
1. Spec and architecture capture
2. Stack finalization
3. Repo scaffold + artifacts
4. Alpha core implementation
5. Verification and blocker assessment

## Alpha success criteria
- A protected domain can be toggled on/off through project config/control plane
- Protected requests are redirected/challenged by sidecar
- Unprotected requests bypass sidecar
- Successful sidecar auth permits access through to YunoHost-managed target
- Shared remembered session works across protected domains
- A documented remove/rollback path exists
