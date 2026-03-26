# wm3v.com root-assisted read-only preflight (2026-03-25)

## Access mode used
- SSH as `ickx@wm3v.com`
- constrained sudo wrapper: `/usr/local/sbin/mfa-sidecar-readonly-preflight`
- read-only inspection only
- no writes/reloads/installs performed by the agent during this pass

## Strongly verified host facts
- YunoHost version: `12.1.39`
- YunoHost admin: `12.1.13`
- ssowat: `12.1.1`
- Authelia binary: **missing** at `/usr/local/bin/authelia`
- LDAP socket exists: `/var/run/slapd/ldapi`
- SSOWAT persistent config is minimal and readable; no obvious custom auth portal complexity surfaced there

## Important app/nginx facts
### Existing candidate portal domain
- `/etc/nginx/conf.d/auth.wm3v.com.conf` exists
- Earlier non-root inspection also showed `/etc/nginx/conf.d/2fa.wm3v.com.d/` exists as a directory, though empty from that vantage point
- This strongly suggests at least one auth-themed domain/subdomain has already been created or partially reserved on the box

### Homebox target
- app settings confirm:
  - app id: `homebox`
  - domain: `home.wm3v.com`
  - path: `/`
  - upstream port: `59150`
  - protected=false at the YunoHost permission layer
- nginx snippet at `/etc/nginx/conf.d/home.wm3v.com.d/homebox.conf` is a simple reverse proxy to `http://127.0.0.1:59150/`
- This is exactly the sort of target domain the sidecar should be able to wrap cleanly

### Existing redirect patterns
- `/etc/yunohost/apps/redirect/settings.yml`:
  - domain: `ickx.wm3v.com`
  - reverse proxy target: `http://192.168.60.188:18789`
- `/etc/yunohost/apps/redirect__2/settings.yml`:
  - domain: `node.wm3v.com`
  - reverse proxy target: `http://192.168.60.188:8788`
- This reinforces that redirect/proxy donor patterns were a sensible packaging donor choice

## LDAP findings that materially improve confidence
### User object reality
Sample user `uid=ickx,ou=users,dc=yunohost,dc=org` has object classes:
- `mailAccount`
- `inetOrgPerson`
- `posixAccount`
- `userPermissionYnh`

This means the current alpha default user filter:
- `(&(uid={input})(objectClass=inetOrgPerson))`

is **too optimistic / likely wrong** for this host.

Safer host-aligned options now appear to be something like:
- `(&(uid={input})(objectClass=inetOrgPerson))`

or another filter validated against real entries.

### Group object reality
Sample group `cn=all_users,ou=groups,dc=yunohost,dc=org` has object classes:
- `posixGroup`
- `groupOfNamesYnh`

and uses `member: uid=...,ou=users,dc=yunohost,dc=org`

This means the current alpha group filter:
- `(&(member={dn})(objectClass=groupOfNamesYnh))`

is also **too generic / likely wrong** for this host.

A better host-shaped first approximation is likely:
- `(&(member={dn})(objectClass=groupOfNamesYnh))`

## Conclusions
### Good news
- The core sidecar architecture still fits the box well
- nginx layout, app layout, and LDAP base structure all support the project direction
- Homebox in particular looks like a good first protected-domain test candidate

### Problems caught before install
1. **Authelia binary missing**
   - install would fail immediately without provisioning it first
2. **LDAP filters need correction before first install**
   - current package defaults do not match observed user/group object classes closely enough
3. **Portal domain choice should be normalized**
   - `auth.wm3v.com` appears to exist in config tree already and may be a cleaner portal name than `2fa.wm3v.com`

## Recommended immediate project changes
1. update seeded LDAP user filter to prefer `inetOrgPerson`
2. update seeded group filter to prefer `groupOfNamesYnh`
3. bias docs/config examples toward `auth.<domain>` as portal naming default
4. keep the explicit Authelia-binary preflight
5. only then attempt first snapshot-backed install
