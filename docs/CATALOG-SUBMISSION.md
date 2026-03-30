# MFA Sidecar catalog submission packet

This file is a paste-ready working packet for submitting MFA Sidecar to the YunoHost app catalog.

## Proposed `apps.toml` entry

```toml
[mfa_sidecar]
category = "system_tools"
state = "working"
url = "https://github.com/wonko6x9/mfa_sidecar_ynh"
```

Notes:
- `system_tools` is the better fit for a perimeter/auth integration utility.
- No antifeatures are proposed at submission time.
- Do **not** add `level`; YunoHost CI manages that.

## Files to include in the YunoHost/apps PR

- Add the app block above to `apps.toml` in alphabetical order.
- Add a square logo file to `logos/` named for the app id, typically `mfa_sidecar.png`.
  - Source candidate from this repo: `assets/logo.png`
- The package repo already contains representative screenshots under:
  - `doc/screenshots/admin-targets.jpg`
  - `doc/screenshots/admin-users.jpg`

## Suggested PR title

```text
Add MFA Sidecar to the catalog
```

## Suggested PR body

```markdown
## Problem / rationale

MFA Sidecar adds a browser-first MFA perimeter in front of selected YunoHost apps and paths.

It exists to cover a practical gap: YunoHost's normal SSO path does not provide native MFA for arbitrary downstream apps. MFA Sidecar provides a dedicated portal, operator-managed host/path protection rules, explicit break-glass behavior, and recovery-oriented documentation.

## Package status

Current package version: `0.4.0~ynh1`

This package is not a thin wrapper around Authelia. It includes:

- custom policy/render/apply pipeline
- custom admin UI and sidecar user management
- YunoHost-aware discovery of domains/apps
- managed nginx auth-request injection for selected targets
- explicit break-glass controls
- packaged operator/recovery docs

## Validation summary

Validated on a real YunoHost box:

- fresh install works with install dir under `/var/www/mfa_sidecar`
- services start and run correctly from the `/var/www` install path
- root-mounted protected targets work
- subpath-mounted protected targets work (for example `/webmail`)
- shared sidecar session behavior across multiple protected targets works
- disable / re-enable loops work
- break-glass behavior works

Repo-local smoke/regression tests are also included for the major failures found during real-box validation.

## Notable design choices

### Vendored pinned Authelia artifact

The package currently ships a pinned Authelia release artifact and verifies it with sha256.

This is deliberate: MFA Sidecar sits on the login path for protected apps, so reproducible install/upgrade behavior matters more here than generic preference for live upstream fetches. The packaged artifact is the same one exercised in real-box validation.

### Loopback-bound admin UI

The admin UI binds to localhost and relies on the YunoHost/nginx fronting layer for operator access. This trust boundary is documented explicitly in the package docs.

## Docs and screenshots

Representative admin UI screenshots are included in the package repo under `doc/screenshots/`.

## Reviewer notes

Reviewer-facing notes are included in the package repo here:

- `docs/SUBMISSION-NOTES.md`
- `docs/SECURITY-NOTES.md`
- `docs/LIVE-BOX-VERIFICATION.md`

Happy to adjust the catalog metadata if reviewers think another existing category is a better fit, but `system_tools` seems the most honest current choice.
```

## Maintainer checklist

- [ ] Fork `YunoHost/apps`
- [ ] Add `mfa_sidecar` entry to `apps.toml`
- [ ] Add `logos/mfa_sidecar.png` from this repo's `assets/logo.png`
- [ ] Open PR with the title/body above
- [ ] Be ready to answer reviewer questions about category choice and vendored Authelia rationale
