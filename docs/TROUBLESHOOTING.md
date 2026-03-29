# MFA Sidecar Troubleshooting and Recovery

This document is for operators.

The goal is not to be clever. The goal is to get the system back into a known-good state without making recovery harder.

## First principles

When something breaks, decide which layer is broken:

1. **host / nginx / web surface**
2. **sidecar portal / Authelia**
3. **policy / protected-target state**
4. **user account / password / MFA enrollment**

Do not assume every auth problem is a user problem.

## Break-glass recovery

### Preferred break-glass: disable enforcement globally

Edit the package policy file, typically:

- `$install_dir/config/domain-policy.yaml`

Set:

```yaml
access_control:
  enforcement_enabled: false
```

Then regenerate/reload runtime.

This preserves your configuration while bypassing protection.

That is usually the right recovery move if the sidecar policy itself is the problem.

## If the web surface hangs or appears down

Symptoms:

- host still responds to ping/SSH
- ports 80/443 listen
- browser hangs instead of returning a page
- curl from localhost also hangs

This often points to nginx being wedged rather than the whole server being gone.

### First response

```bash
sudo systemctl restart nginx
```

Then test:

```bash
curl -k -I --max-time 5 https://your-root-domain/
curl -k -I --max-time 5 https://your-portal-domain/
```

If it comes back, write down that nginx was wedged and recovered by restart.

### If it does not come back

Collect immediately:

```bash
sudo systemctl status nginx --no-pager -n 50
sudo journalctl -u nginx -n 100 --no-pager
sudo tail -n 100 /var/log/nginx/error.log
```

## If the admin UI loads but discovered targets are missing

Check:

- the admin service is running updated code
- the sudoers file includes YunoHost discovery commands
- discovery can run under the service account

Important commands:

```bash
sudo cat /etc/sudoers.d/mfa-sidecar
sudo -u mfa_sidecar sudo /usr/bin/yunohost domain list --output-as json
sudo -u mfa_sidecar sudo /usr/bin/yunohost app list --output-as json
```

## If the portal loads but logins fail

Check:

- Authelia is running
- the users file exists
- the user exists in `users.yml`
- password or MFA enrollment state is valid

Useful commands:

```bash
sudo systemctl status mfa-sidecar-authelia --no-pager
sudo cat /etc/mfa-sidecar/authelia/users.yml
```

## If a user is stuck

From `/admin/users`, admins can:

- set/reset password
- reset MFA
- disable/enable the user

Use those before you reach for hand-editing files.

## If everyone needs to sign in again

Use the admin action:

- **Clear active sessions (force re-login)**

In the current package design, this restarts Authelia and destroys memory-backed sessions.

## If the portal/admin UI is reachable but protected apps behave strangely

Test one protected target in a private/incognito window.

Verify the full flow:

1. target request redirects to portal
2. password works
3. MFA works
4. redirect returns to target
5. app actually loads

If redirects work but the app itself fails, the issue may be downstream/upstream-specific rather than sidecar auth.

## Dangerous changes to avoid first

Do not start troubleshooting with:

- protecting the root domain more aggressively
- protecting the portal domain because you think “more MFA” will fix auth
- mass role changes
- manual file deletions in `/etc/mfa-sidecar/nginx/protected`
- random nginx surgery without first checking whether a simple restart clears a wedged state

## Useful files

### Policy and generated runtime

- `$install_dir/config/domain-policy.yaml`
- `$install_dir/deploy/generated-runtime/render-index.json`
- `/etc/mfa-sidecar/runtime-metadata.json`

### Auth and users

- `/etc/mfa-sidecar/authelia/configuration.yml`
- `/etc/mfa-sidecar/authelia/users.yml`
- `/var/lib/mfa_sidecar/db.sqlite3`

### Nginx and portal staging

- `/etc/mfa-sidecar/nginx/portal.conf`
- `/etc/mfa-sidecar/nginx/protected/`

## Useful services

```bash
sudo systemctl status nginx --no-pager
sudo systemctl status mfa-sidecar-authelia --no-pager
sudo systemctl status mfa-sidecar-admin --no-pager
```

## Recovery philosophy

The package should be operable by a human under stress.

If you find yourself inventing clever undocumented recovery steps, stop and make the recovery path simpler instead.