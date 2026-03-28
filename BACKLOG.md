# MFA Sidecar Backlog

## Before public submission / catalog review

High-value checklist from live operator validation:

- [ ] Run realistic upgrade tests from at least one prior package revision to current.
  - Verify no auth regression on protected targets.
  - Prove the upgrade path instead of assuming it.

- [ ] Validate emergency recovery on a real box.
  - Test `access_control.enforcement_enabled: false`
  - Reload runtime
  - Restart relevant services
  - Document exact timings and expected outcomes in submission notes

- [ ] Confirm app quality criteria for catalog expectations.
  - Install/uninstall leaves the system clean enough
  - Permissions/groups are minimal
  - No broken behavior with multi-domain common setups
  - `tests.toml` reflects current install arguments and package reality

- [x] Review whether `show_users_file` should remain exposed in the config panel.
  - Removed from the normal config-panel surface; raw users-file inspection is now treated as recovery/debug territory rather than a routine UI action.

- [ ] Expand smoke/regression coverage so we do not refight the same dragons.
  - Upgrade from at least one older revision to current
  - Protected target auth regression on a real protected app path
  - SSOwat bypass behavior for internal auth subrequest locations
  - Existing-install config/default migration behavior (especially MFA method defaults)
  - `enforcement_enabled: false` break-glass behavior
  - Render/stage/apply reinjection after upgrade
  - Presence of required packaged assets/docs so install/upgrade cannot fail on missing files

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
