# 2026-03-26 install handoff

## Current good refs
- development branch: `dev`
- installer-facing branch on GitHub: `main`
- package mirror branch on GitLab: `github-package`
- this handoff doc records earlier install-state lessons, but the branch model has since been normalized and the package has been further hardened beyond the original handoff snapshot

## What happened tonight
The repo/package was substantially hardened, but the live wm3v install path still failed in ways that suggest **stale YunoHost package fetch state, stale systemd unit state, or both** during the install transaction.

Observed failure progression on wm3v:
1. Initial GitHub install failed because the repo root did not expose a top-level YunoHost package shape (`manifest.toml` at repo root).
2. A dedicated installer-facing branch (`github-package`) was created with proper package-root-at-top-level layout.
3. Multiple real service-unit issues were found and fixed in-repo:
   - overly aggressive namespace/sandbox settings
   - install-time service checks depending on stale unit definitions
   - `curl` dependency in runtime reachability guard removed
   - `WorkingDirectory` / `ExecStartPre` complexity removed from units for alpha host compatibility
4. Despite those repo fixes and successful local smoke reruns, wm3v install logs continued to show **older unit definitions** during install attempts:
   - namespace failures mentioning old sandbox behavior
   - `WorkingDirectory` / `ExecStartPre`-related `CHDIR` failures after those had already been removed from the repo branch
5. During one failed cycle, wm3v access degraded until nginx and failed sidecar leftovers were cleaned up manually.

## Best current theory
The remaining blocker is likely **outside the repo content itself**:
- YunoHost/GitHub fetch path may be reusing stale downloaded package content or temp work dirs during repeated install attempts
- systemd may have been using stale loaded unit definitions during or immediately after failed install/remove cycles
- repeated same-night retries on the same production host likely compounded state contamination

In short: tonight stopped being a normal package bug and started smelling like **host/install transaction state pollution**.

## Practical recommendation for tomorrow
### Preferred path
1. If wm3v remains weird in any way, **restore the Proxmox snapshot** taken before the install attempts.
2. Avoid relying on repeated GUI fetch/install against a dirty host state.
3. Do a disciplined fresh install attempt from a clean state, preferably one of:
   - restored snapshot + GUI install from GitHub `main`
   - restored snapshot + shell install from a freshly downloaded/exported local package tree
4. If using the GUI again, use only:
   - `https://github.com/wonko6x9/mfa_sidecar_ynh`

### Required host cleanup before another install attempt (if not restoring snapshot)
Run these first on the target host:

```bash
sudo yunohost app remove mfa_sidecar 2>/dev/null || true
sudo systemctl stop mfa-sidecar-admin mfa-sidecar-authelia 2>/dev/null || true
sudo systemctl disable mfa-sidecar-admin mfa-sidecar-authelia 2>/dev/null || true
sudo systemctl reset-failed mfa-sidecar-admin mfa-sidecar-authelia 2>/dev/null || true
sudo rm -f /etc/systemd/system/mfa-sidecar-admin.service /etc/systemd/system/mfa-sidecar-authelia.service
sudo rm -rf /etc/mfa-sidecar /opt/yunohost/mfa_sidecar /var/lib/mfa_sidecar
sudo mv /etc/nginx/conf.d/auth.wm3v.com.conf /root/auth.wm3v.com.conf.disabled 2>/dev/null || true
sudo mv /etc/nginx/conf.d/auth.wm3v.com.d /root/auth.wm3v.com.d.disabled 2>/dev/null || true
sudo systemctl daemon-reload
sudo nginx -t && sudo systemctl restart nginx
```

Then confirm no stale units remain:

```bash
sudo systemctl status mfa-sidecar-admin mfa-sidecar-authelia --no-pager -l || true
```

Desired result: units not found, or at least no loaded stale unit content.

## Tomorrow install procedure
1. Start from a clean host state (ideally restored snapshot).
2. Confirm nginx is healthy before touching MFA Sidecar.
3. Install from:
   - `https://github.com/wonko6x9/mfa_sidecar_ynh/tree/github-package`
4. If install succeeds:
   - confirm `/etc/mfa-sidecar/authelia/users.yml` exists
   - if you did not create the first sidecar admin during install, create it immediately via config-panel action or helper flow
   - retrieve `MFA_SIDECAR_ADMIN_GATE_SECRET`
   - validate `/admin`
   - if the portal domain still appears to fall into default YunoHost behavior, force `yunohost tools regen-conf nginx --force` and verify the parent `auth.<domain>.conf` exists before blaming the sidecar
   - test first managed target using `home.wm3v.com`
5. If install fails again, immediately capture:
   - `systemctl cat mfa-sidecar-authelia`
   - `systemctl cat mfa-sidecar-admin`
   - `journalctl -u mfa-sidecar-authelia -u mfa-sidecar-admin -n 120 --no-pager`
   - any `/var/cache/yunohost/app_tmp_work_dirs/*/manifest.toml` or package temp tree evidence if present

## Repo-level tasks that were still worth doing after the original handoff
Most of these were subsequently addressed during the 2026-03-26 hardening push:
- branch/publication model normalized (`dev` for source, GitHub `main` for installer-facing package root)
- authoritative YunoHost docs/convention review performed
- first `config_panel.toml` + `scripts/config` surface added
- package/docs updated so `change_url` fails honestly instead of pretending relocation is supported
- repeated export/publish discipline exercised to reduce branch drift risk

Still remaining after those improvements:
- continue deciding how much of `/admin` should migrate into YunoHost-native controls
- consider a shell-first install validation path against a disposable YunoHost VM so GUI/cache behavior is not the first live proof

## Bottom line
The repo is materially better than it was at the start of tonight, but **wm3v is no longer a trustworthy first-proof environment without cleanup or snapshot restore**.

Tomorrow should start from a clean host state and a documented install procedure, not another incremental midnight retry.
