# 2026-03-26 — wm3v live discovery validation

- Completed a read-only live host validation against wm3v after John supplied the correct SSH path (`ickx@wm3v.com` on port `44220`).
- Added narrow sudo access for exactly two read-only YunoHost commands so preflight could run without broad root access.
- Confirmed live YunoHost domain inventory and live YunoHost app inventory.
- Confirmed important non-root app paths from YunoHost align with the meaningful nginx-exposed root-domain paths on wm3v.
- Confirmed nginx also contains extra regex/helper cruft, reinforcing that nginx should remain a sanity check rather than the primary discovery source.
- Conclusion: the simplified YunoHost-first discovery model is the right fit for wm3v.
