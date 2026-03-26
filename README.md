# MFA Sidecar

<img src="https://raw.githubusercontent.com/YunoHost/apps/main/logos/mfa_sidecar.png" width="32px" alt="Logo of MFA Sidecar">

Authelia-based MFA sidecar for selected YunoHost domains and paths.

## Status
This project is at a **production-hardened alpha candidate** checkpoint. Local validation is strong, the auth model has been corrected to a separate sidecar-owned store, operator recovery/break-glass paths exist, and services now run as the package app user rather than root. The remaining gap is clean-host live validation from a restored snapshot or otherwise cleaned target so stale YunoHost/systemd state does not poison the result. The package is intended as a **browser-first perimeter shell** with a user-facing portal and a separate operator/admin control plane, not a normal end-user dashboard tile.

## Branches and install surface
- `main` is the **installer-facing distribution branch** on GitHub and should expose a top-level YunoHost package layout.
- `dev` is the **development branch** for source/docs/tests/project history.
- `dist/package-root/` is a generated local export used to refresh the distribution surface from the dev branch.

If YunoHost is installing from GitHub, use the repo's `main` branch. Do not point it at the dev branch.

## Current design goals
- dedicated portal domain for the sidecar itself
- managed host/path entries with simple on/off control
- longest-match-wins path overrides
- WebAuthn/passkeys primary, TOTP fallback
- separate Authelia credential/MFA store independent from YunoHost auth
- optional read-only YunoHost identity/contact lookup rather than YunoHost-auth coupling
- removable sidecar architecture rather than patching YunoHost core auth

## Current package capabilities
- vendored Authelia artifact with checksum verification
- dedicated portal-domain install model
- managed site policy generation for host/path entries
- portal install no longer seeds itself as a managed target entry
- generated Authelia config and nginx snippets
- runtime staging into `/etc/mfa-sidecar`
- package lifecycle scripts for install/upgrade/backup/restore/remove
- first YunoHost-native config surface via `config_panel.toml` + `scripts/config` for high-level settings and operator actions
- thin bundled admin UI at `/admin` for managed host/path entries
- draft `/admin` auth gate via generated shared secret header
- simple read-only discovery suggestions from YunoHost domains + app subpaths, with nginx used only as a sanity check
- repeated smoke coverage for render, staging, discovery, admin add/edit/delete/toggle/apply flow, vendored binary install, package-tree export, user bootstrap/sync, break-glass disable, least-privilege service posture, and failure contracts
- explicit package-root export script at `scripts/export_package_root.sh`
- sidecar-owned users file bootstrap and managed first-user helper using Authelia-generated Argon2 hashes
- YunoHost-driven user sync that preserves separate password/MFA authority while disabling users removed upstream
- emergency disable path that drops the primary include hook and stops sidecar services without destructive uninstall

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
- morning install handoff: `docs/2026-03-26-INSTALL-HANDOFF.md`

## Branding
- product name: **MFA Sidecar**
- engine: **Authelia**
- temporary logo/icon: official Authelia logo
