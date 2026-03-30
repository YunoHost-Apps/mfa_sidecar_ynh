# MFA Sidecar Backlog

## Near-term release gate (0.3.0)

- [ ] Validate emergency recovery on a real box.
  - Test `access_control.enforcement_enabled: false`
  - Reload/runtime apply
  - Restart relevant services
  - Confirm protected target bypasses remotely
  - Re-enable and confirm auth returns

See also: `docs/RELEASE-GATES.md`

## Before wider public submission / catalog review

High-value checklist from live operator validation:

- [ ] Confirm app quality criteria for catalog expectations.
  - Permissions/groups are minimal
  - No broken behavior with multi-domain common setups
  - `tests.toml` reflects current install arguments and package reality

- [x] Realistic upgrade path exercised repeatedly on a real box.
  - Multiple real upgrades were performed during hardening, including failure discovery/fix cycles.

- [x] Uninstall/reinstall recovery exercised under stress.
  - Not elegant, but real.

- [x] Review whether `show_users_file` should remain exposed in the config panel.
  - Removed from the normal config-panel surface; raw users-file inspection is now treated as recovery/debug territory rather than a routine UI action.

- [ ] Expand smoke/regression coverage so we do not refight the same dragons.
  - `enforcement_enabled: false` break-glass behavior
  - Additional upgrade-style fixtures where helpful
  - Any remaining live-only failures worth encoding once observed

## v2 / post-MVP backlog

These are intentionally not release-gating for the current line.

- [ ] Better identity model.
  - Cleaner YunoHost identity sync
  - Better role/group mapping
  - Less awkward drift between sidecar-local users and platform identity

- [ ] Richer policy model.
  - Per-target auth/session policy
  - Group-based access rules
  - More expressive protection rules than simple host/path protect-or-bypass

- [ ] Better onboarding and MFA enrollment UX.
  - Clearer first-run flow
  - Cleaner method choice and messaging
  - Less confusing first-time enrollment behavior

- [ ] Safer/smarter target management UX.
  - Better details/expanders
  - Smarter preview/confidence around discovered targets
  - Better handling of root/path conflicts and operator decisions

- [ ] Audit trail / event log.
  - Track important admin actions like protect/bypass, password reset, MFA reset, global disable/enable, clear sessions

- [ ] Better break-glass and recovery ergonomics.
  - Safer recovery dashboard/UX
  - Better recovery verification helpers
  - More obvious explanations of what recovery actions actually do

- [ ] Optional deeper downstream app integrations / real SSO where practical.
  - Trusted-header / OIDC / app-specific integrations where it actually helps

- [ ] Better multi-host / multi-operator thinking.
  - More explicit assumptions and defaults for broader/shared deployments

- [ ] Admin and users page polish.
  - Current pages are useful and usable, but still visually cold/spartan
  - Improve warmth/readability without compromising clarity
  - Treat outside contributions/integration code here as welcome if they fit the architecture

## Notes

If the checks above pass, John’s judgment was that public submission would be reasonable.

## Security review notes

Minor notes from live review (none considered critical blockers at this time):

- Admin UI runs unauthenticated on localhost:9087; protection relies on the nginx/YunoHost proxy boundary being correct.
- Policy injection modifies other apps' nginx configs with reversible marker blocks; any bug in marker logic could leave stale includes.
- Vendored Authelia binary is an explicit pinned trust decision and should remain easy to review and bump.

Positive review outcome:

- No obvious shell injection issues found
- No world-writable file mistakes found
- No hardcoded secrets found
- No obviously over-permissive sudo surface found
- Overall human-operable-under-stress direction was judged strong

## Follow-up from external code review (Claude Opus 4.6)

- [x] Remove plaintext password exposure via CLI arguments in `manage_authelia_users.py` / admin UI subprocesses.
  - Current fix uses a pseudo-TTY to drive Authelia's interactive hash prompt instead of passing `--password` on argv.

- [x] Document the localhost admin trust boundary explicitly.
  - `admin_ui_app._authorized()` currently returns `True` and depends entirely on loopback bind + nginx/YunoHost auth.
  - Add comments/docs so this is clearly intentional if retained.

- [x] Add CSRF protection for admin UI POST actions.
  - Added a lightweight per-process token mirrored in a Strict cookie + hidden form fields for admin POST actions.

- [x] Tighten username/path validation for admin UI user-action routes.
  - Current routing accepts usernames from path segments without an explicit validation helper.

- [x] Reduce lifecycle-script drift.
  - Shared packaged-file install logic now lives in `_common.sh` and is reused by install/upgrade/restore.

- [x] Consider documenting the root apply helper trust boundary more explicitly.
  - Covered in `docs/SECURITY-NOTES.md`.

- [x] Revisit localhost SMTP assumptions in submission notes.
  - Covered in `docs/SECURITY-NOTES.md` and `docs/SUBMISSION-NOTES.md`.
