# LDAP integration notes (alpha)

## Verified from YunoHost source
From `YunoHost/yunohost` `src/utils/ldap.py` (external source, analyzed as evidence only):
- base DN: `dc=yunohost,dc=org`
- user DN pattern: `uid={username},ou=users,dc=yunohost,dc=org`
- local privileged socket bind path exists via `ldapi:///var/run/slapd/ldapi`

These values strongly support the alpha defaults already chosen for:
- `base_dn: dc=yunohost,dc=org`
- `additional_users_dn: ou=users`

## Still not yet source-verified
The following started as working assumptions and are now partially validated / corrected by live wm3v inspection:
- users container `ou=users` ✅
- groups container `ou=groups` ✅
- better user filter on wm3v is likely `(&(uid={input})(objectClass=inetOrgPerson))`
- better group filter on wm3v is likely `(&(member={dn})(objectClass=groupOfNamesYnh))`
- usable service bind account `uid=authelia,ou=users,dc=yunohost,dc=org` is still an unverified assumption
- filter mode remains the safer default than assuming `memberOf`

## Alpha decision
For now, keep the renderer on the safer/portable Authelia side:
- use explicit `groups_filter` with `group_search_mode: filter`
- do not assume `memberOf` exists and is complete
- keep service-bind user configurable rather than hard-coding it in package logic

## Practical next validation step
On an actual YunoHost alpha target, inspect LDAP directly to confirm:
1. object classes on user entries
2. object classes on group entries
3. member attribute semantics
4. whether a dedicated read-only bind account should be created or whether local socket access is preferable for the sidecar host layout

## Likely implementation direction
- packaged alpha should prefer a dedicated LDAP bind account secret in `/etc/mfa-sidecar/mfa-sidecar.env`
- if packaging on the same host proves cleaner with `ldapi:///var/run/slapd/ldapi`, evaluate whether Authelia can use that path cleanly under its service user with least-privilege access
- avoid assuming root or peercred auth for the sidecar service unless there is a very strong reason
