# wm3v.com read-only preflight (2026-03-25)

## Access mode used
- SSH as non-root user: `ickx@wm3v.com`
- Strictly read-only inspection only
- No writes, reloads, installs, or config edits performed

## Verified facts
- Host reachable over SSH with agent key
- Hostname: `wm3v.com`
- OS: Debian 12-ish kernel/userspace lineage (`Linux 6.1.0-43-amd64`)
- `python3` is installed
- PyYAML is available (`import yaml` succeeds)
- `yunohost` CLI is installed, but admin commands require root/sudo
- `nginx` config tree exists at `/etc/nginx/conf.d/*`
- LDAP local socket exists at `/var/run/slapd/ldapi`
- `ickx` is in `ssh.main`

## Important package-fit findings
### Good
- YunoHost per-domain nginx include directory layout is present and looks conventional for this project model
- Example domain snippets inspected (`home.wm3v.com`, `ickx.wm3v.com`) match the reverse-proxy style the sidecar expects to wrap
- `2fa.wm3v.com.d/` already exists as a domain config directory, but appears empty from this access level. That may be a useful candidate portal domain, or at least evidence the name/path has already been reserved.
- Python + PyYAML being present removes one likely first-install failure for the renderer/stager helpers
- Local LDAP socket presence suggests same-host LDAP integration options may be available later

### Expected blockers / not-yet-ready items
- `/usr/local/bin/authelia` is currently **missing**
  - this matches the package's explicit preflight failure path
  - first install would currently fail there unless Authelia is installed first
- No evidence of existing Authelia deployment or auth_request sidecar snippets found in the readable nginx tree
- `ickx` does **not** have passwordless sudo, so root-only YunoHost/SSO state could not be inspected in this pass
- `/etc/ssowat/conf.json.persistent` and `/etc/yunohost/apps` were not readable from this access level

## Readable nginx observations
- `/etc/nginx/conf.d/home.wm3v.com.d/homebox.conf`
  - simple reverse proxy to `http://127.0.0.1:59150/`
- `/etc/nginx/conf.d/ickx.wm3v.com.d/redirect.conf`
  - reverse proxy to `http://192.168.60.188:18789`
  - includes `yunohost_panel.conf.inc`
- no existing readable files containing `authelia` or sidecar-auth request wiring were found

## Confidence impact
### Reduced risk
- package helper runtime dependencies (`python3`, `yaml`) are present
- host nginx structure is compatible with the sidecar model
- there is no obvious readable conflicting Authelia deployment

### Remaining real-install risk
- Authelia binary must be installed first
- root-only YunoHost/SSO internals still need inspection if we want higher confidence before install
- LDAP filters/group semantics remain unverified against live directory contents
- multi-domain include rollout still needs real host validation

## Best next step before install
1. install or place a known-good Authelia binary at `/usr/local/bin/authelia`
2. optionally allow a **read-only root/sudo-assisted probe** for:
   - `yunohost tools versions`
   - `/etc/ssowat/conf.json.persistent`
   - app settings under `/etc/yunohost/apps`
   - selective LDAP inspection
3. take a VM snapshot
4. perform first install on the snapshot
