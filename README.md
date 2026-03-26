# MFA Sidecar

Authelia-based MFA sidecar for selected YunoHost domains and paths.

## Status
This project is in active pre-install validation. The package is intended as an **admin-side/operator tool**, not a normal end-user dashboard app.

## Current design goals
- dedicated portal domain for the sidecar itself
- managed host/path entries with simple on/off control
- longest-match-wins path overrides
- WebAuthn/passkeys primary, TOTP fallback
- YunoHost LDAP as the identity source
- removable sidecar architecture rather than patching YunoHost core auth

## Current package capabilities
- vendored Authelia artifact with checksum verification
- dedicated portal-domain install model
- managed site policy generation for host/path entries
- portal install no longer seeds itself as a managed target entry
- generated Authelia config and nginx snippets
- runtime staging into `/etc/mfa-sidecar`
- package lifecycle scripts for install/upgrade/backup/restore/remove
- thin bundled admin UI at `/admin` for managed host/path entries
- draft `/admin` auth gate via generated shared secret header
- simple read-only discovery suggestions from YunoHost domains + app subpaths, with nginx used only as a sanity check
- repeated smoke coverage for render, staging, discovery, admin add/toggle/apply flow, vendored binary install, and failure contracts

## Important constraints
- the sidecar portal must be installed on its own dedicated domain at `/`
- protected targets are managed separately as host/path entries
- nothing should be protected automatically without explicit operator intent

## Key references
- package manifest: `package-base/manifest.toml`
- config model: `docs/CONFIG-MODEL.md`
- policy pivot notes: `docs/POLICY-MODEL-PIVOT.md`
- pre-install checklist: `docs/PRE-INSTALL-CHECKLIST.md`
- final pre-install status: `docs/FINAL-PREINSTALL-STATUS.md`

## Branding
- product name: **MFA Sidecar**
- engine: **Authelia**
- temporary logo/icon: official Authelia logo
