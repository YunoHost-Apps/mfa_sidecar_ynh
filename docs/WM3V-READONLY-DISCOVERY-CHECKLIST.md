# wm3v read-only discovery checklist

Use this before the next live install attempt to compare what the simplified discovery model will likely surface.

## Goal
Verify that the YunoHost-first discovery approach matches the real host well enough that the admin page will feel sane on first load.

## Read-only commands to run on wm3v
### YunoHost domains
- `yunohost domain list --output-as json`

### YunoHost apps
- `yunohost app list --output-as json`

### nginx sanity-check for discovered subpaths
- inspect `/etc/nginx/conf.d/*.d/*.conf`
- compare listed YunoHost app subpaths against nginx `location` blocks

## What to compare
For each app with a non-root path:
- domain
- path
- whether nginx appears to expose that path

## What not to do
- do not try to auto-model every nginx-only custom path
- do not treat nginx as primary discovery source
- do not mutate host config during this check

## Decision rule
- if YunoHost app inventory mostly matches nginx, proceed with the simplified model
- if mismatches are frequent and important, document the exact mismatch class before changing code
- nginx-only/custom cases can use manual add in the admin page
