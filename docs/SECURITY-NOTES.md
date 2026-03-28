# MFA Sidecar Security / Trust-Boundary Notes

This document records the main trust boundaries and intentionally accepted tradeoffs in the package.

## 1. Localhost admin UI trust boundary

The admin UI binds to:

- `127.0.0.1:9087`

The app itself does not perform a second independent identity check inside `admin_ui_app.py`; it intentionally relies on the nginx/YunoHost fronting layer to enforce operator access before traffic reaches loopback.

That means:

- if YunoHost/nginx permissions are correct, this is acceptable and low exposure
- if the proxy boundary is misconfigured, the UI itself should not be assumed to save you

This is an explicit design assumption and should remain documented.

## 2. Root apply helper trust boundary

The package uses a tightly-scoped sudo/root helper to apply generated runtime state:

- nginx include injection/reinjection
- nginx reload
- sidecar service restarts

The sudo surface is intentionally narrow, but the helper still applies root-owned config changes from app-controlled generated state. That is inherent to the architecture.

Practical implication:

- generated policy/render outputs are part of the trusted configuration path
- the helper should stay easy to review
- the helper should stay tightly scoped

## 3. Local SMTP assumptions

Password reset/recovery mail is configured for local SMTP delivery.

Current behavior intentionally allows localhost SMTP without strict TLS verification.

That is acceptable for local delivery on the same machine, but operators should understand:

- if the local MTA relays outward, reset-token confidentiality depends on that relay path
- this is not the same thing as end-to-end encrypted delivery

## 4. Nginx marker injection as a maintenance surface

MFA Sidecar modifies other apps' nginx location blocks using marker-bounded managed blocks.

This is reversible and testable, but it is still the main maintenance surface in the architecture.

Practical implication:

- reinjection logic must stay well tested
- unusual nginx config structures may still need operator attention
- live-box verification after upgrades is worth the effort

## 5. Why the package prefers human-operable recovery

The package intentionally favors:

- explicit break-glass controls
- obvious file locations
- deterministic render/stage/apply steps
- minimal magical hidden state

This is not just UX preference. It is part of the security model: systems that are easier to recover under stress are less likely to get dangerous ad-hoc fixes.
