# Operator first-boot checklist

Use this immediately after the next real install to minimize post-install churn.

## 1. Confirm the LDAP bind password state
By default MFA Sidecar now auto-generates:

- `/etc/mfa-sidecar/secrets/ldap_bind_password`

You should not need to replace it unless you explicitly want to override it with a known value.

If you do change it manually later, refresh runtime state with one of:

- `yunohost app upgrade mfa_sidecar --debug`
- or restart both services:
  - `systemctl restart mfa-sidecar-authelia`
  - `systemctl restart mfa-sidecar-admin`

## 2. Retrieve the admin gate secret
Read:

- `/etc/mfa-sidecar/mfa-sidecar.env`

and copy:

- `MFA_SIDECAR_ADMIN_GATE_SECRET`

You will need that value to pass the `/admin` auth gate during alpha validation.

## 3. Validate the portal
Check that:

- the portal domain loads
- the logo renders
- `/admin` no longer returns nginx 500

## 4. Validate first managed-site workflow
In `/admin`:

- add the first managed site
- verify policy apply succeeds
- test enable/disable
- test edit/delete

Suggested first target on wm3v:

- `home.wm3v.com`

## 5. Validate auth flow
Confirm:

- redirect into the sidecar portal
- successful login/enrollment path
- return to the protected target
- bypass still works for disabled entries

## 6. Record what still hurts
If anything still requires manual surgery after install, record it immediately. The goal is to burn down post-install footguns, not normalize them.
