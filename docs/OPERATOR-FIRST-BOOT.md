# Operator first-boot checklist

Use this immediately after the next real install to minimize post-install churn.

## 1. Confirm the sidecar users file exists
By default MFA Sidecar now bootstraps a template at:

- `/etc/mfa-sidecar/authelia/users.yml`

This is intentionally **not** a finished real-user database. It is a starter template so the operator has an explicit place to finish first-user setup instead of discovering that requirement later.

## 2. Create the first real sidecar user
Edit:

- `/etc/mfa-sidecar/authelia/users.yml`

Replace the placeholder values with a real first user:

- real username key
- real display name
- real email
- real **Argon2 hash** instead of `REPLACE_WITH_ARGON2_HASH`

Use the Authelia CLI to generate the password hash, for example:

- `authelia crypto hash generate argon2`

Then save the generated digest into the `password:` field.

## 3. Retrieve the admin gate secret
Read:

- `/etc/mfa-sidecar/mfa-sidecar.env`

and copy:

- `MFA_SIDECAR_ADMIN_GATE_SECRET`

You will need that value to pass the `/admin` auth gate during alpha validation.

## 4. Reload services after first-user setup
After updating `users.yml`, refresh runtime state with one of:

- `yunohost app upgrade mfa_sidecar --debug`
- or restart both services:
  - `systemctl restart mfa-sidecar-authelia`
  - `systemctl restart mfa-sidecar-admin`

## 5. Validate the portal
Check that:

- the portal domain loads
- the logo renders
- `/admin` no longer returns nginx 500

## 6. Validate first managed-site workflow
In `/admin`:

- add the first managed site
- verify policy apply succeeds
- test enable/disable
- test edit/delete

Suggested first target on wm3v:

- `home.wm3v.com`

## 7. Validate auth flow
Confirm:

- redirect into the sidecar portal
- successful login/enrollment path
- return to the protected target
- bypass still works for disabled entries

## 8. Record what still hurts
If anything still requires manual surgery after install, record it immediately. The goal is to burn down post-install footguns, not normalize them.
