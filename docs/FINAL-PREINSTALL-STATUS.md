# Final pre-install status

## Overall read
MFA Sidecar is now in a **credible snapshot-backed first-install state**.

It is not "production-proven" yet, but the package is no longer obviously underbaked in the major areas we could validate safely before a live install.

## Major improvements completed
- product identity settled on **MFA Sidecar**
- dedicated portal domain requirement enforced
- managed host+path policy model implemented
- longest-match-wins override semantics implemented
- vendored Authelia artifact added to package sources
- Authelia install path now checksum-verifies vendored artifact
- LDAP defaults corrected from live wm3v inspection
- temporary truthful branding/logo added using official Authelia logo
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
2. real LDAP bind credential setup and first auth test
3. real nginx reload/start interaction on the host
4. whether `auth.wm3v.com` has hidden historical cruft beyond what our constrained inspection exposed

## Recommended first real install plan
1. confirm `auth.wm3v.com` as dedicated portal domain
2. snapshot the VM
3. install MFA Sidecar on `auth.wm3v.com` at `/`
4. set real LDAP bind password immediately after install
5. start with `home.wm3v.com` as the first enabled managed site target
6. validate portal reachability, redirect, auth flow, and return path

## Bottom line
At this point I would describe the package as:
- **ready enough for a first real install with a snapshot**
- **much safer than it was earlier today**
- **still deserving of caution, but no longer obviously missing fundamental packaging pieces**
