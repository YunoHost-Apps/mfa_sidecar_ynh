# Pre-install checklist

Use this before the first real YunoHost install attempt.

## Smoke coverage already passing in-repo
- renderer output smoke test
- runtime staging smoke test
- include injection/removal smoke test
- edge-case policy rendering smoke test
- discovery smoke test
- admin UI smoke test
- admin auth-gate smoke test
- include idempotence smoke test
- failure-contract smoke test for bad Authelia artifact checksum
- package-tree dry-run smoke test
- service contract smoke test
- packaged admin service/proxy contract smoke test
- vendored Authelia install smoke test
- repeated vendored Authelia extraction consistency test
- tampered vendored artifact rejection test
- bash syntax check across package scripts
- Python compile check across renderer/helpers

## Required before real install
1. Confirm the vendored Authelia artifact in package sources matches the version/checksum you intend to ship
2. Confirm the target host has Python 3 + PyYAML available for renderer execution
3. Ensure the target host is clean before install — ideally from a restored snapshot, otherwise explicitly clean stale units/runtime leftovers first
4. If not restoring a snapshot, perform host cleanup before reinstalling:
   - remove any failed `mfa_sidecar` app state if present
   - stop/disable/reset-failed `mfa-sidecar-admin` + `mfa-sidecar-authelia`
   - remove stale `/etc/systemd/system/mfa-sidecar-*.service`
   - remove stale `/etc/mfa-sidecar`, `/opt/yunohost/mfa_sidecar`, `/var/lib/mfa_sidecar`
   - move aside leftover `auth.<domain>` nginx config from failed attempts
   - `systemctl daemon-reload`
   - `nginx -t && systemctl restart nginx`
5. Be ready to retrieve/use the generated `MFA_SIDECAR_ADMIN_GATE_SECRET` from `/etc/mfa-sidecar/mfa-sidecar.env` (or the config-panel action) for `/admin` access during alpha validation
6. Be ready to create the first sidecar user through the YunoHost config panel action; manual editing of `/etc/mfa-sidecar/authelia/users.yml` is now fallback-only
7. Ensure the sidecar portal is being installed on its own dedicated domain at `/`
8. Treat this as a browser-first perimeter shell with a user-facing portal on `/` and a separate admin/operator surface on `/admin`, not a normal dashboard tile
9. Use the installer-facing branch only: `https://github.com/wonko6x9/mfa_sidecar_ynh`
10. Prefer testing first on a disposable YunoHost VM or snapshot

## Expected first-install rough edges still possible
- `/admin` still uses an interim shared-secret gate rather than a polished operator auth flow
- multi-domain rollout beyond the primary domain is not yet fully automated
- package lifecycle has strong dry-run coverage, and the simplified discovery model now has a live wm3v read-only validation, but not yet full live host execution proof
- first real install still needs a deliberate first-user bootstrap and end-to-end auth validation against the sidecar-owned users store

## Recommended first validation sequence
1. snapshot / disposable VM
2. install Authelia binary
3. install package (optionally create the first sidecar admin during install)
4. inspect `/etc/mfa-sidecar/`
5. inspect generated nginx include placement
6. if the portal domain seems to fall through to default/catch-all nginx behavior, run `yunohost tools regen-conf nginx --force` and re-check the parent server block for the portal domain
7. reload/test nginx
8. verify portal responds
9. verify protected-domain redirect/auth flow
10. test upgrade path
11. test remove/rollback path
