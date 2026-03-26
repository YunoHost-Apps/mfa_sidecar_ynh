# YunoHost conformance review — 2026-03-26

This review compares MFA Sidecar against current YunoHost packaging v2 docs/schema/helpers semantics and the broader expectations of apps living sanely inside the YunoHost ecosystem.

## Sources consulted
- YunoHost doc mirror checked locally under `/tmp/ynhdocs`
- YunoHost app schemas checked locally under `/tmp/ynhapps`
- Specifically reviewed:
  - manifest/resources/tests docs
  - helpers v2.1 docs
  - config panel docs
  - hooks / permissions docs
  - tests.toml schema

## Overall conclusion
The package is **closer to install-safe than before**, but it still behaves more like a **system-management sidecar appliance** than a conventional YunoHost app. That is not inherently invalid, but it means YunoHost-fit problems matter more because the package mutates nginx behavior and runs root-owned services.

## Hard defects found

### 1. Missing declared apt dependencies
Severity: **must fix**

The package executes / depends on:
- `python3`
- `python3-yaml` (`import yaml` in runtime tools)
- `openssl` (secret generation in shell helpers)

Yet no `[resources.apt]` block was declared.

This is a real YunoHost packaging defect because the package relied on ambient host state instead of declaring its dependencies.

**Status:** fixed in review by adding:
```toml
[resources.apt]
packages = ["python3", "python3-yaml", "openssl"]
```

### 2. tests.toml excluded backup/restore
Severity: **must fix**

YunoHost’s quality model explicitly treats backup/restore as a major quality threshold. Excluding it is understandable during bring-up but not acceptable if we are trying to minimize install risk on a real host.

**Status:** fixed in review by removing `backup_restore` from the excluded tests.

## Significant conformance gaps still present

### 3. Admin access model lives mostly outside YunoHost permission semantics
Severity: **should fix soon / maybe must-fix before broader release**

Before this review, the package only modeled `main` permission while `/admin` access was effectively enforced by a custom header secret.

That is operationally workable, but in YunoHost terms it is odd because `/admin` is a first-class path and YunoHost expects permission modeling when meaningful.

**Status:** partially improved in review by adding a declared `admin` permission:
```toml
admin.url = "/admin"
admin.allowed = "admins"
admin.show_tile = false
admin.auth_header = false
admin.protected = true
```

**Remaining concern:** the custom admin gate header is still the real access control plane. The YunoHost permission is now more honest, but the model is still layered/unusual.

### 4. No YunoHost config panel
Severity: **should fix**

For a system-style admin app with no native polished app management integration into YunoHost, a `config_panel.toml` + optional `scripts/config` would be the idiomatic way to expose core settings and actions.

Missing a config panel does not block install, but it makes the package feel foreign to YunoHost and forces the admin to rely on the custom admin UI plus filesystem state.

### 5. change_url support is conceptually dishonest
Severity: **should fix**

The package docs/state repeatedly assert this app belongs on a dedicated domain rooted at `/`. Keeping a `change_url` script implies support for lifecycle operations that the package conceptually does not want to support.

This is not necessarily an immediate install blocker, but it is misleading surface area.

### 6. Direct mutation of nginx configs belonging to other app/domain surfaces
Severity: **high-risk design issue**

The package intentionally injects includes into nginx confs outside its own dedicated app nginx file. That is core to the sidecar concept, but it is also not “normal YunoHost app behavior.”

This means:
- rollback/cleanup correctness matters a lot
- change collisions with YunoHost-managed config regeneration matter
- backup/restore and upgrade semantics must be watched closely

This is probably unavoidable for the current product shape, but it should be treated as architectural risk, not normalized away.

### 7. Root-owned services + root-level filesystem writes
Severity: **high-risk design issue**

Both Authelia and the admin service run as `root`, while the package writes into:
- `/etc/mfa-sidecar`
- `/etc/nginx/...`
- `/usr/local/bin/authelia`

Again: not automatically invalid, but it raises the burden of correctness, cleanup, and privilege minimization.

## Other observations

- Using install/data/system_user resources is good.
- Using a password install question for LDAP bind password is appropriate and aligns with YunoHost forms semantics.
- `init_main_permission` usage is valid.
- Declaring `main.auth_header = false` is coherent for this app.
- The package remains intentionally single-instance; that is consistent with the product shape.

## Recommended next steps

### Before the next real install attempt
1. Keep the new apt resource.
2. Keep backup/restore enabled in tests.
3. Keep the newly declared `admin` permission.
4. Re-run smoke tests after export/publication refresh.
5. If time permits before install, remove or explicitly neuter `change_url` support.

### Before calling this truly YunoHost-native / catalog-worthy
1. Add a real `config_panel.toml`.
2. Reassess whether `/admin` should be governed more directly by YunoHost permission semantics.
3. Minimize root where possible.
4. Consider whether nginx mutation of other app/domain configs can be made more bounded / auditable.
5. Run actual package_check / linter in a clean YunoHost test environment.

## Bottom line
The package can probably be made safe enough for the next snapshot-backed install attempt on wm3v.

But if the question is “does this already behave like a normal well-integrated YunoHost app?” the honest answer is **no, not yet**. It behaves like a specialized sidecar appliance wearing a YunoHost package wrapper. That can still be valid — it just needs stricter discipline.
