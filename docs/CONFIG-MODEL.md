# Config model (alpha)

## Purpose
One declarative policy file should drive both:
- Authelia configuration
- nginx portal and protected-site snippets

That keeps the sidecar removable and prevents policy drift between the auth engine and the front-door proxy layer.

## Current alpha shape

```yaml
version: 1
portal:
  domain: auth.example.tld
  path: /
  default_redirect_url: https://yunohost.example.tld/
  listen:
    host: 127.0.0.1
    port: 9091
session:
  name: mfa_sidecar_session
  secret_env: AUTHELIA_SESSION_SECRET
  expiration: 24h
  inactivity: 1h
  remember_me: 24h
storage:
  encryption_key_env: AUTHELIA_STORAGE_ENCRYPTION_KEY
identity:
  local: ...
  sync:
    source: yunohost-ldap-readonly
mfa:
  webauthn: ...
  totp: ...
access_control:
  default_policy: bypass
  managed_sites:
    - id: root_site
      host: wm3v.com
      path: /
      enabled: true
      upstream: https://127.0.0.1:443
    - id: nextcloud_exception
      host: wm3v.com
      path: /nextcloud
      enabled: false
      upstream: https://127.0.0.1:443
recovery:
  mode: authelia-reset-password-and-enrollment
alpha:
  generate_nginx_snippets: true
  generate_authelia_config: true
  enforce_tls_upstream_verification: false
```

## Design notes
- `portal.*` defines where the sidecar UI/auth endpoint lives.
- The portal app itself must live on its **own dedicated domain** at `/`; do not co-host it on a shared app domain/path.
- `session.*` drives shared remembered-session behavior across managed sites.
- `identity.local.*` is the sidecar-owned credential/MFA authority.
- `identity.sync.*` is the optional read-only bridge for lightweight username/email discovery and user-lifecycle reconciliation from YunoHost.
- The sidecar should not rely on YunoHost LDAP as its primary password backend if the goal is a genuinely separate outer shell.
- Sync should update identity metadata (username/display/email) and disable vanished upstream users by default, while leaving password and MFA state separate.
- `access_control.managed_sites[*].enabled` is the user-facing binary on/off switch.
- `managed_sites` are explicitly operator-managed entries, not automatic discovery truth.
- A managed site is identified by `host + path` and can represent either a full domain (`/`) or a specific subpath.
- **Longest matching path wins** for a given host. This intentionally allows a deeper path rule to override a broader host/root rule, including creating bypass exceptions inside a generally protected site.
- Duplicate `host + path` entries are rejected by the renderer.

## Alpha renderer outputs
The renderer currently emits:
- `authelia-config.generated.yml`
- `nginx/portal.generated.conf`
- `nginx/<site-id>.generated.conf` for each managed site
- `render-index.json` summary for tooling/tests
- `runtime-metadata.json` summary including managed site states

Generated files under `deploy/generated-alpha/` and `tests/out/` are disposable artifacts and should not be treated as source-of-truth design references.

## Near-term product direction
- operator-facing admin UI should center on **on/off toggles** for managed entries
- adding a custom site/path should create a new managed entry
- refreshing the control view should show the new entry with its toggle
- recommendations/discovery can assist the user, but should not automatically enable protection
