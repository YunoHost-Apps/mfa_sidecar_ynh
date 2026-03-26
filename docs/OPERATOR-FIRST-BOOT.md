# Operator first-boot checklist

Use this immediately after the next real install to minimize post-install churn.

## 1. Confirm the sidecar users file exists
By default MFA Sidecar now bootstraps a template at:

- `/etc/mfa-sidecar/authelia/users.yml`

This is intentionally a starter file, not a finished real-user database.

## 2. Preferred path: seed the first user from the YunoHost config panel
Open the MFA Sidecar config panel and use:

- **Create or update first sidecar user**

Provide:

- username
- display name
- email
- password

The package will generate the Argon2 hash via the local Authelia CLI, write it into `/etc/mfa-sidecar/authelia/users.yml`, and restart Authelia.

## 3. Manual fallback path
If needed, you can still edit:

- `/etc/mfa-sidecar/authelia/users.yml`

Replace the placeholder values with a real first user:

- real username key
- real display name
- real email
- real **Argon2 hash** instead of `REPLACE_WITH_ARGON2_HASH`

You can generate the hash manually with:

- `authelia crypto hash generate argon2`

## 4. Retrieve the admin gate secret
Read:

- `/etc/mfa-sidecar/mfa-sidecar.env`

and copy:

- `MFA_SIDECAR_ADMIN_GATE_SECRET`

You will need that value to pass the `/admin` auth gate during install validation.

## 5. Reload/restart if you used the manual fallback path
If you edited `users.yml` manually, refresh runtime state with one of:

- `yunohost app upgrade mfa_sidecar --debug`
- or restart both services:
  - `systemctl restart mfa-sidecar-authelia`
  - `systemctl restart mfa-sidecar-admin`

## 6. Validate the portal
Check that:

- the portal domain loads
- the logo renders
- `/admin` no longer returns nginx 500

## 7. Validate first managed-site workflow
In `/admin`:

- add the first managed site
- verify policy apply succeeds
- test enable/disable
- test edit/delete

Suggested first target on wm3v:

- `home.wm3v.com`

## 8. Validate user sync behavior
Use the config panel action:

- **Sync users from YunoHost**

Confirm that:

- new YunoHost users appear in `/etc/mfa-sidecar/authelia/users.yml`
- missing upstream users become `disabled: true`
- existing sidecar password/MFA state is not overwritten

## 9. Validate auth flow
Confirm:

- redirect into the sidecar portal
- successful login/enrollment path
- return to the protected target
- bypass still works for disabled entries

## 10. Record what still hurts
If anything still requires manual surgery after install, record it immediately. The goal is to burn down post-install footguns, not normalize them.
