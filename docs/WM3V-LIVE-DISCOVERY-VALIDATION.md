# wm3v live discovery validation

## Purpose
Record the read-only live host check used to validate the simplified YunoHost-first discovery model before the next install attempt.

## Access method used
- SSH to `ickx@wm3v.com` on port `44220`
- narrow sudo allowance for read-only commands:
  - `/usr/bin/yunohost domain list --output-as json`
  - `/usr/bin/yunohost app list --output-as json`

## Result summary
The simplified model held up well on the live host.

### YunoHost domain inventory
Live YunoHost returned the expected domain inventory including:
- `wm3v.com`
- `auth.wm3v.com`
- `home.wm3v.com`
- `gitlab.wm3v.com`
- `wallabag.wm3v.com`
- and many others

### YunoHost app inventory
Important non-root app installs included:
- `wm3v.com/243`
- `gitlab.wm3v.com/gitlab`
- `wm3v.com/hextris`
- `wm3v.com/kanboard`
- `wm3v.com/librespeed`
- `wm3v.com/google`
- `wm3v.com/nextcloud`
- `wm3v.com/pgadmin`
- `wm3v.com/phpinfo`
- `wm3v.com/phpmyadmin`
- `wm3v.com/phpsysinfo`
- `wm3v.com/webmail`
- `wm3v.com/wallabag`

### nginx sanity-check read
A read-only nginx inspection of `/etc/nginx/conf.d` showed those same important root-domain app paths are present, while also revealing extra regex/helper locations that would be noisy if nginx were treated as the primary discovery source.

## Conclusion
This strongly supports the simplified discovery design:
- **YunoHost-first** for domains and app paths
- **nginx only as a sanity check**
- **manual add** for custom nginx-only oddities

That is a better fit for wm3v than the earlier broader nginx-heavy discovery path.
