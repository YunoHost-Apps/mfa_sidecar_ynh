# Final pre-install status

## Overall read
MFA Sidecar is now in a **credible alpha package state**, but tonight's wm3v attempts proved that a clean host state matters just as much as package quality.

It is not "production-proven" yet, and the next attempt should start from a restored snapshot or an equivalently clean host state. The package is no longer obviously underbaked in the major areas we could validate safely before a live install, but the live installer path itself showed stale-state/cache behavior that must be accounted for.

## Major improvements completed
- product identity settled on **MFA Sidecar**
- dedicated portal domain requirement enforced
- managed host+path policy model implemented
- longest-match-wins override semantics implemented
- vendored Authelia artifact added to package sources
- Authelia install path now checksum-verifies vendored artifact
- LDAP defaults were explored and partially hardened during the earlier design branch, but the architecture is now being corrected toward a separate sidecar-owned auth store
- temporary truthful branding/logo added using official Authelia logo
- local package/admin logo asset is present, but YunoHost app-list icon behavior may still depend on the central app-catalog artwork path rather than the packaged asset alone
- service hardening tightened beyond the original draft units, including app-user execution and stricter systemd filesystem controls in the current package branch
- explicit package-root export script added so release/publish no longer depends on workspace-root sprawl
- repeated smoke runs pass consistently
- live wm3v read-only and constrained root-assisted preflights completed

## Important issue caught late and fixed
A real consistency bug existed where:
- renderer/docs/tests had moved to `managed_sites`
- package install seed logic was still emitting the old domain-centric model

That mismatch has now been corrected and the full smoke suite is green afterward.

## What is now giving real confidence
- shell syntax clean
- Python compile clean
- repeated full smoke suite passes after major refactors
- vendored artifact tamper rejection works
- vendored artifact repeated extraction is consistent
- package-tree dry-run works
- policy model now matches the intended operator UX much more closely

## Remaining live-install unknowns
These are the things that cannot be fully settled without a real install:
1. live YunoHost lifecycle execution on wm3v
2. real first-user bootstrap and first auth test against the sidecar-owned users store
3. real nginx reload/start interaction on the host
4. whether `auth.wm3v.com` has hidden historical cruft beyond what our constrained inspection exposed

## Recommended first real install plan
1. confirm `auth.wm3v.com` as dedicated portal domain
2. snapshot the VM
3. install MFA Sidecar on `auth.wm3v.com` at `/`
4. complete the initial sidecar user in `/etc/mfa-sidecar/authelia/users.yml` with a real email and Argon2 password hash
5. start with `home.wm3v.com` as the first enabled managed site target
6. validate portal reachability, redirect, auth flow, and return path

## Bottom line
At this point I would describe the package as:
- **ready enough for a first real install with a snapshot**
- **much safer than it was earlier today**
- **still deserving of caution, but no longer obviously missing fundamental packaging pieces**
