# DECISIONS.md — MFA Sidecar

## D-001: Sidecar over core patching
**Decision:** Build a removable front-door sidecar/gate rather than patching YunoHost core auth.

**Why:**
- cleaner install/remove story
- lower upgrade fragility
- smaller blast radius
- preserves YunoHost's own session/login behavior after access is granted

## D-002: Passkeys first, TOTP fallback
**Decision:** Primary MFA method is passkeys/WebAuthn. Fallback is TOTP.

**Why:**
- modern UX
- open standards
- no custom mobile app required
- TOTP remains universal fallback when passkeys are unavailable or awkward

## D-003: Binary per-domain policy for v1
**Decision:** v1 policy model is simple on/off per domain/subdomain.

**Why:**
- lower cognitive load
- easier admin UX
- less policy-engine sprawl
- matches the user's explicit preference

## D-004: Shared auth across protected domains
**Decision:** Once authenticated to the sidecar, the user should be treated as authenticated across protected domains for the configured remembered-session period.

**Why:**
- better UX
- fits the desired front-door gate model
- avoids repeated MFA challenge on every protected subdomain

## D-005: Fully open-source-friendly direction
**Decision:** Avoid proprietary mobile dependencies, commercial-gated core features, and half-open ecosystems in the main design.

**Why:**
- practical fit for YunoHost acceptance norms
- avoids dependency on vendor push infrastructure
- preserves removability and maintainability

## D-006: Initial engine preference = Authelia
**Decision:** Use Authelia as the first-choice sidecar engine unless implementation evidence forces reconsideration.

**Why:**
- strongest fit for reverse-proxy gate model
- lighter than full identity platforms
- supports separate credential/MFA state, WebAuthn, TOTP, and remembered sessions

## D-008: Keep sidecar auth state separate from YunoHost auth state
**Decision:** Authelia should maintain its **own** hashed/salted credential and MFA store rather than authenticating directly against YunoHost LDAP.

**Why:**
- preserves the shell/gate model John wants
- creates a real trust-boundary separation between the outer gate and the inside system
- compromise of one store should not automatically collapse the other
- avoids accidental drift into pseudo-SSO when the product goal is removable perimeter protection

**Implementation note:**
- YunoHost LDAP may still be used read-only for lightweight user/contact discovery or reconciliation
- YunoHost LDAP should not be treated as the primary password authority for the sidecar

## D-007: Use `redirect_ynh` as packaging/proxy scaffold donor
**Decision:** Use `YunoHost-Apps/redirect_ynh` as a donor scaffold for YunoHost package structure and reverse-proxy lifecycle patterns.

**Why:**
- already solves non-trivial redirect/proxy packaging pieces
- has the right manifest/scripts/nginx template shape for a removable proxy-style app
- lowers churn on boring package glue while keeping auth logic separate
- should be treated as chassis/lifecycle scaffolding, not as an auth engine

**Implementation note:**
- donor package copied locally into `shared/yunohost-mfa-sidecar/package-base/` for mutation into the MFA-sidecar package skeleton
- first alpha mutation now replaces redirect/proxy questions with sidecar-centric install inputs: portal domain/path, portal subdomain label, default policy for new domains, remembered-session duration, and default upstream seed target
