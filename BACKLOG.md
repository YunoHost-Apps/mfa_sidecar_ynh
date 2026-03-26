# BACKLOG.md — MFA Sidecar

## Now
- [ ] Consult authoritative YunoHost docs and real package conventions for required package structure and admin-page/admin-UX expectations before the next install attempt (no more donor-only guessing)
- [ ] Reconcile MFA Sidecar package/admin approach against that YunoHost guidance, especially installer-facing repo shape, app icon/admin presentation, and whether `/admin` is the right model
- [ ] Perform first real install on wm3v from a clean host state using the documented procedure
- [ ] Validate real LDAP bind credential setup and first successful auth flow
- [ ] Validate first managed-site target end to end (`home.wm3v.com` first)
- [ ] Validate upgrade/remove/restore behavior on the real host
- [ ] Add emergency global disable / rollback path
- [ ] Decide exact alpha recovery/operator recovery stance
- [ ] Decide whether the current `/admin` shared-secret gate survives alpha or gets replaced immediately after install feedback
- [x] Finalize v1 architecture document
- [x] Validate how Authelia fits YunoHost LDAP in practice (pre-install + wm3v read-only validation)
- [x] Draft alpha runtime scaffolding (systemd/env/nginx templates)
- [x] Add smoke test for config rendering pipeline
- [x] Add runtime staging path for generated alpha assets
- [x] Wire staging/build path into YunoHost package install and upgrade scripts
- [x] Add protected-domain include injection/removal helpers for live YunoHost domains
- [x] Add read-only discovery of domains/apps/root-domain subpaths for admin suggestions
- [x] Simplify discovery to YunoHost-first inventory with nginx sanity check
- [x] Define policy/config schema for managed host/path on/off
- [x] Build initial alpha renderer for Authelia config + nginx snippets from shared policy
- [x] Adapt `redirect_ynh` package/lifecycle patterns into the alpha package skeleton (donor copied into `package-base/`)
- [x] Mutate donor `manifest.toml` and scripts for MFA-sidecar semantics
- [x] Decide initial install/config questions for alpha package
- [x] Replace placeholder portal nginx redirect with real Authelia portal + protected-domain generation path
- [x] Scaffold thin admin/control plane with add/edit/delete/toggle/apply behavior
- [x] Add smoke coverage for admin add/toggle/apply flow
- [x] Wire package draft for `/admin` control plane service + proxy route
- [x] Add alpha install/operator docs

## Next
- [ ] Expand include injection beyond the primary protected app domain into broader multi-domain rollout helpers
- [ ] Define remembered-session policy defaults more explicitly
- [ ] Add default-protect-new-domains behavior
- [ ] Replace draft `/admin` shared-secret gate with a cleaner operator auth model after live validation
- [ ] Reduce root-biased service execution where practical

## Later
- [ ] Evaluate authentik fallback path if Authelia proves too limiting
- [ ] Consider richer policy profiles beyond binary on/off
- [ ] Consider admin-vs-user stricter remembered-session policy
- [ ] Consider recovery-code UX improvements
- [ ] Consider broader app-aware policy only if clearly needed

## Explicitly rejected for v1
- [x] Custom mobile app
- [x] Proprietary push notification dependency
- [x] Patching YunoHost core auth directly
- [x] Keycloak-based first implementation
- [x] Full custom auth core from scratch
