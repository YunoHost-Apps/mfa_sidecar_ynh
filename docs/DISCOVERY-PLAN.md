# Discovery plan (simplified alpha)

## Source of truth
Use **YunoHost** as the primary source of truth for discovery.

### Domains
Pull from YunoHost domain inventory (same conceptual source as the domains admin page).

### App folders / subpaths
Pull from YunoHost app inventory.
- if an app is installed at `/`, do not list it as a subpath option
- if an app is installed at `/something`, list that folder/path as an option

## nginx role
nginx is **not** a parallel discovery universe.
Use it only as a light sanity check:
- does the discovered app path appear in nginx config or not?

If it does not check out with nginx:
- show that as a simple yes/no mismatch
- do not invent more complex behavior yet
- let the operator decide whether to add it anyway or inspect further

## Manual add escape hatch
If something exists in nginx but not in YunoHost, or if the host is unusual:
- use the manual add form
- do not try to auto-discover every weird edge case

## Product intent
Keep this boring.
We want:
- domains from YunoHost
- app subpaths from YunoHost
- nginx sanity-check column
- manual add for custom stuff

We do **not** want:
- endless discovery heuristics
- confidence-score theater
- trying to model every hand-edited nginx oddity
