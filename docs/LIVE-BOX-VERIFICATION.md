# MFA Sidecar Live-Box Verification

This checklist is for real-box validation after upgrades, break-glass changes, or before public submission.

## Quick command

Run:

```bash
sudo "${MFA_SIDECAR_INSTALL_DIR:-/var/www/mfa_sidecar}"/bin/verify_live_box.sh
```

The package ships a copy of `scripts/verify_live_box.sh` into the current install dir during install/upgrade.

## What to verify manually

### 1. Services are healthy

- nginx
- mfa-sidecar-admin
- mfa-sidecar-authelia

### 2. Policy matches intent

Check whether:

- `access_control.enforcement_enabled` is the expected value
- protected targets are actually marked `enabled: true`

### 3. Generated/staged protected snippets exist

Make sure the protected auth snippets are present in both:

- generated output
- `/etc/mfa-sidecar/nginx/protected/`

### 4. Auth-request snippet sanity

The protected snippet should include the known-required pieces:

- `access_by_lua_block { return; }` (SSOwat bypass)
- `X-Original-Method`
- `X-Forwarded-For`
- `X-Forwarded-Host $http_host`

### 5. MFA method state matches the intended rollout

For the current rollout we expect:

- TOTP enabled
- WebAuthn disabled by default unless explicitly re-enabled later

### 6. Manual browser test

Use a fresh incognito/private window and verify one protected app:

1. request protected target
2. sidecar intercepts correctly
3. if first run, enrollment flow is understandable
4. subsequent access authenticates cleanly
5. downstream app handoff behaves as expected

## Break-glass verification

For a true break-glass check, validate on a real box:

1. set `access_control.enforcement_enabled: false`
2. render/stage/apply runtime
3. restart nginx + sidecar services
4. confirm protected target is bypassed again
5. set it back to `true` and confirm normal auth resumes

## Why this exists

Some of the most important MFA Sidecar failures are only trustworthy when validated on a live box:

- upgrade/regeneration drift
- nginx snippet presence
- SSOwat interaction
- first-run MFA enrollment behavior
- downstream app handoff behavior

This checklist keeps those checks explicit instead of relying on memory.
