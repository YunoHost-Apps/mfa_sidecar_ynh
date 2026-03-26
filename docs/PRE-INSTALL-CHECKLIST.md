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
5. Be ready to replace the placeholder LDAP bind password in `/etc/mfa-sidecar/secrets/ldap_bind_password` immediately after install
6. After replacing it, rerun `yunohost app upgrade mfa_sidecar --debug` or restart `mfa-sidecar-authelia` + `mfa-sidecar-admin` so `/etc/mfa-sidecar/mfa-sidecar.env` is refreshed from the secret file
7. Be ready to retrieve/use the generated `MFA_SIDECAR_ADMIN_GATE_SECRET` from `/etc/mfa-sidecar/mfa-sidecar.env` for `/admin` access during alpha validation
8. Ensure the sidecar portal is being installed on its own dedicated domain at `/`
9. Treat this as an admin-side/operator tool, not a user dashboard app/tile
10. Use the installer-facing branch only: `https://github.com/wonko6x9/mfa_sidecar_ynh/tree/github-package`
11. Prefer testing first on a disposable YunoHost VM or snapshot

## Expected first-install rough edges still possible
- LDAP filters were corrected after live wm3v inspection, but still deserve one more validation during first install
- service hardening is improved but still conservative/root-biased rather than a finished least-privilege model
- multi-domain rollout beyond the primary domain is not yet fully automated
- package lifecycle has strong dry-run coverage, and the simplified discovery model now has a live wm3v read-only validation, but not yet full live host execution proof

## Recommended first validation sequence
1. snapshot / disposable VM
2. install Authelia binary
3. install package
4. inspect `/etc/mfa-sidecar/`
5. inspect generated nginx include placement
6. reload/test nginx
7. verify portal responds
8. verify protected-domain redirect/auth flow
9. test upgrade path
10. test remove/rollback path
