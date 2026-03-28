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

- [ ] Review whether `show_users_file` should remain exposed in the config panel.
  - It is useful, but potentially sensitive
  - Re-evaluate from a safe-by-default perspective before public listing

## Notes

If the checks above pass, John’s judgment was that public submission would be reasonable.
