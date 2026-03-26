# Architecture draft

## Core boundary
The sidecar is a gatekeeper in front of selected YunoHost-managed domains.
Once access is granted, YunoHost continues normal auth/session behavior.

## Main components
- Reverse proxy layer
- Authelia sidecar auth engine
- Separate Authelia credential + MFA store
- Optional read-only YunoHost identity/contact source for username/email discovery only
- PostgreSQL durable state (or other Authelia-supported durable store as the implementation settles)
- Thin control plane for domain toggles and generated config

## Policy model
Per domain/subdomain:
- enabled: true/false
- upstream target
- future: optional policy profile

Global:
- default protect new domains: true/false
- remembered-session duration

## Session model
- Sidecar session controls access to protected domains
- YunoHost/app session remains separate after pass-through
- The outer gate and the inner system should not share password authority; the point is layered access, not a blended auth plane
