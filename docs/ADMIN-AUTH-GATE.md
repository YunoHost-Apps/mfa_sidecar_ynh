# Admin auth gate (alpha)

## Current alpha posture
The `/admin` control plane now has a simple interim gate.

### How it works
- install generates `MFA_SIDECAR_ADMIN_GATE_SECRET`
- value is written into `/etc/mfa-sidecar/mfa-sidecar.env`
- nginx only proxies `/admin` if header `X-MFA-Sidecar-Admin-Secret` is present
- admin UI also verifies that header matches the configured secret

## Why this exists
This is not the final admin auth model.
It is an alpha hardening step so `/admin` is not left effectively open while we validate the rest of the package.

## Why it is intentionally simple
- lower risk than leaving `/admin` naked
- much less ceremony than building a second full auth system right now
- easy to replace later with a more native/operator-friendly model

## Limitations
- header-secret UX is clunky
- not a polished operator login experience
- still needs a better long-term admin auth story

## Long-term likely direction
Replace this with a cleaner operator-facing auth model after live package validation, but keep the current gate until something better actually exists.
