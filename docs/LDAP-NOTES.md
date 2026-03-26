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

## Current implementation direction
- package lifecycle now owns a **managed service bind account** at `uid=authelia,ou=users,dc=yunohost,dc=org`
- install / upgrade / restore reconcile that LDAP entry idempotently via local `ldapi:///` using `ldapadd` / `ldapmodify`
- remove deletes the managed service bind account so stale sidecar logins do not accumulate
- bind password source of truth remains `/etc/mfa-sidecar/secrets/ldap_bind_password`, which is mirrored into the service env file for Authelia runtime use

## Remaining caveats
- the current implementation uses local OpenLDAP client tooling (`ldap-utils`) and assumes EXTERNAL auth over `ldapi:///` is available on the host
- service privilege is still root-heavy overall; this fixes lifecycle honesty before it fixes least-privilege
- if future YunoHost-native primitives for service-account lifecycle are found, they may be preferable to hand-managed LDAP object operations
