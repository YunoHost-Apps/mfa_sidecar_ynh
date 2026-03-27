# BACKLOG.md — MFA Sidecar

## Now
- [ ] Make first-run operator UX obvious: after install, the user must be able to discover how to create the first sidecar user, retrieve the admin gate secret, and define protected targets without spelunking through repo docs
- [ ] Validate first-user bootstrap end to end on a real host so the config-panel-driven operator path is proven, not just locally smoke-tested
- [ ] Validate runtime ownership/permission behavior on a real host after the stager-side hardening so generated live assets stay readable by the service user across install/upgrade/restore
- [ ] Validate publish/installer-branch discipline on a fresh install path so dev/package drift prevention is proven operationally, not just by local smoke coverage
- [ ] Reconcile MFA Sidecar package/admin approach against YunoHost guidance, especially installer-facing repo shape, app icon/admin presentation, and whether `/admin` is the right model
- [ ] Execute `docs/WM3V-INJECTION-LIVE-PLAN.md` against `home.wm3v.com`, including: correct `target_conf` discovery, clean location injection, `nginx -t`, auth redirect behavior, emergency disable recovery, and reinjection survival after `yunohost tools regen-conf nginx`
- [ ] Validate upgrade/remove/restore behavior on the real host
- [x] Add emergency global disable / rollback path
- [ ] Decide exact production recovery/operator recovery stance
- [ ] Decide whether the current `/admin` shared-secret gate survives first production-hardened install or gets replaced immediately after install feedback
- [ ] Decide whether this project should be considered complete at “production-hardened alpha pending clean-host live validation” or kept open until that live validation is executed
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
- [x] Reduce root-biased service execution where practical
- [ ] Validate the new app-user/systemd sandbox posture on a real host

## Later
- [ ] Evaluate authentik fallback path if Authelia proves too limiting
- [ ] Consider richer policy profiles beyond binary on/off
- [ ] Consider admin-vs-user stricter remembered-session policy
- [ ] Consider recovery-code UX improvements
- [ ] Consider broader app-aware policy only if clearly needed
- [ ] Consider protocol-aware / second-firewall behavior only as v1.5/v2 work; keep v1 browser-first and selective

## Explicitly rejected for v1
- [x] Custom mobile app
- [x] Proprietary push notification dependency
- [x] Patching YunoHost core auth directly
- [x] Keycloak-based first implementation
- [x] Full custom auth core from scratch
