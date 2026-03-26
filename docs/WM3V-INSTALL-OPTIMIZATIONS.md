# wm3v install optimizations before first real install

## Goal
Maximize the chance that the first install works cleanly enough that snapshot restore is unnecessary.

## Additional findings from comparison pass
### 1. `auth.wm3v.com` is the better portal domain default
Why:
- it already exists as a proper YunoHost domain nginx server config
- it is more conventional and readable than `2fa.wm3v.com`
- using the already-registered auth domain should reduce first-install domain friction

### 2. `2fa.wm3v.com` is probably historical residue
- there is a `2fa.wm3v.com.d/` directory visible in nginx tree from earlier inspection
- no readable active config content was found via current access path
- treat it as archaeological residue unless later evidence says otherwise

### 3. Homebox remains the cleanest first protected target
Why:
- app config is simple
- upstream is local (`127.0.0.1:59150`)
- nginx snippet is minimal
- no obvious special-case rewrite/auth complexity was observed

### 4. Current package should prefer host-shaped LDAP defaults
- user filter should be `(&(uid={input})(objectClass=inetOrgPerson))`
- group filter should be `(&(member={dn})(objectClass=groupOfNamesYnh))`

### 5. Current package should fail early and honestly on missing Authelia
- `/usr/local/bin/authelia` is absent today
- this is the first real install prerequisite to satisfy before package install

## Recommended pre-install sequence on wm3v
1. **Use `auth.wm3v.com` as portal domain**
   - keep the sidecar app on its own dedicated domain at `/`
   - do not try to host the portal on a shared path/domain

2. **The package now carries a vendored Authelia artifact**
   - no manual binary staging should be needed if package sources are intact

3. **Choose one first protected target**
   - recommended: `home.wm3v.com`
   - do not start with a complicated or already-weird app

4. **Snapshot before install**
   - still strongly recommended even though risk has been reduced

5. **After install, validate in this order**
   - generated files under `/etc/mfa-sidecar/`
   - nginx include placement
   - `auth.wm3v.com` portal response
   - redirect/challenge behavior for `home.wm3v.com`
   - successful return after auth

## Things that would improve confidence even further before install
- a second constrained root wrapper that prints the contents of:
  - `/etc/nginx/conf.d/auth.wm3v.com.d/*`
  - possibly `nginx -T` excerpts for `auth.wm3v.com` and `home.wm3v.com`
- this is optional, not mandatory

## My current recommendation
If you want the best odds of a first clean install:
- portal = `auth.wm3v.com`
- first protected app = `home.wm3v.com`
- install Authelia binary first
- snapshot
- then install the package
