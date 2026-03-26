# BACKLOG.md — MFA Sidecar

## Now
- [ ] Finalize v1 architecture document
- [ ] Decide Nginx vs Caddy for alpha proxy implementation
- [ ] Validate how Authelia fits YunoHost LDAP in practice
- [x] Draft alpha runtime scaffolding (systemd/env/nginx templates)
- [x] Add smoke test for config rendering pipeline
- [x] Add runtime staging path for generated alpha assets
- [x] Wire staging/build path into YunoHost package install and upgrade scripts
- [x] Add protected-domain include injection/removal helpers for live YunoHost domains
- [ ] Expand include injection beyond the primary protected app domain into broader multi-domain rollout helpers
- [x] Add read-only discovery of domains/apps/root-domain subpaths for admin suggestions
- [x] Simplify discovery to YunoHost-first inventory with nginx sanity check
- [x] Define policy/config schema for per-domain on/off
- [x] Build initial alpha renderer for Authelia config + nginx snippets from shared policy
- [ ] Define remembered-session policy defaults
- [ ] Confirm recovery path for alpha (built-in, limited, or custom thin layer)
- [ ] Scaffold alpha repo layout and config generator
- [x] Adapt `redirect_ynh` package/lifecycle patterns into the alpha package skeleton (donor copied into `package-base/`)
- [x] Mutate donor `manifest.toml` and scripts for MFA-sidecar semantics
- [x] Decide initial install/config questions for alpha package
- [x] Replace placeholder portal nginx redirect with real Authelia portal + protected-domain generation path
- [x] Scaffold thin admin/control plane with add/toggle/apply behavior
- [x] Add smoke coverage for admin add/toggle/apply flow
- [x] Wire package draft for `/admin` control plane service + proxy route

## Next
- [ ] Implement thin admin/control plane for domain toggles
- [ ] Generate proxy config from declarative domain policy
- [ ] Wire Authelia config generation from same policy source
- [ ] Add default-protect-new-domains behavior
- [ ] Add emergency disable / rollback path
- [ ] Add alpha install/uninstall docs
- [ ] Replace draft `/admin` shared-secret gate with a cleaner operator auth model after live validation

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
