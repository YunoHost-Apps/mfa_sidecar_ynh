# Emergency disable / break-glass path

If MFA Sidecar is interfering with access and you need the fastest non-destructive rollback path, use the **Emergency disable sidecar protection** action from the YunoHost config panel.

## What it does
- removes the **portal include hook** from the sidecar portal nginx file
- removes **managed MFA Sidecar blocks** previously injected into protected app `location` blocks
- reloads nginx
- stops `mfa-sidecar-authelia`
- stops `mfa-sidecar-admin`
- leaves generated sidecar artifacts on disk for later inspection/recovery

## What it does not do
- does not uninstall the package
- does not delete `/etc/mfa-sidecar`
- does not delete the users file or MFA state
- does not delete generated auth-endpoint snippets from disk
- does not try to guess or rewrite arbitrary nginx logic beyond removing the managed MFA Sidecar blocks it owns

## Why this is the right break-glass behavior
This is meant to restore primary access quickly without forcing immediate destructive cleanup. If the sidecar caused trouble, you want the auth hook removed first and the forensic cleanup second.

## After emergency disable
Choose one of these paths:
1. **Recover**
   - inspect config/state
   - fix the issue
   - use the runtime reload action to stage and restart cleanly
2. **Remove**
   - uninstall the package normally if you want it gone entirely

## Manual shell fallback
If the config panel is not reachable, the equivalent rough shell behavior is:

```bash
sudo python3 /opt/yunohost/mfa_sidecar/bin/inject_protected_include.py remove /etc/nginx/conf.d/<portal-domain>.d/mfa_sidecar.conf || true
sudo python3 /opt/yunohost/mfa_sidecar/bin/inject_protected_include.py remove /etc/nginx/conf.d/<target-domain>.d/<target-app>.conf || true
sudo nginx -t && sudo systemctl reload nginx || true
sudo systemctl stop mfa-sidecar-authelia mfa-sidecar-admin || true
```

Adjust `<portal-domain>` and `<target-domain>/<target-app>.conf` to the actual files on the host. The important part is: remove only the **managed MFA Sidecar blocks** from target files, not the rest of the app nginx configuration.
