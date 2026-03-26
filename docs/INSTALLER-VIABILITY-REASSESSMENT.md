# Installer viability reassessment (after vendored Authelia work)

## What changed
The installer is materially more viable now because the package no longer depends on a manually pre-positioned Authelia binary or an install-time network fetch.

It now has a package-managed binary path:
- vendored pinned Authelia release artifact in package sources
- local release metadata with sha256
- sha256 verification before install
- binary extraction from vendored tarball
- installation of verified `authelia` to `/usr/local/bin/authelia`

## Why this matters
Previously, the first install had a guaranteed hard stop if `/usr/local/bin/authelia` was absent.
That is now removed because the package carries the tested pinned artifact itself.

## Current viability scorecard
### Stronger now
- package lifecycle wiring: yes
- host-aligned LDAP defaults: yes
- real host read-only validation: yes
- constrained root-assisted read-only validation: yes
- binary provisioning story owned by package: yes
- vendored tested Authelia artifact: yes
- checksum verification on packaged binary: yes
- smoke coverage around vendor/install/render/stage/include/service contract: yes

### Still real risks
- first live auth flow still depends on a real LDAP bind password being supplied after install
- service still uses a draft root-biased unit
- protected-domain rollout is still best for first single-domain use, not broad polished multi-domain rollout
- no full live install/upgrade/remove execution on a disposable YunoHost target has happened yet
- auth.wm3v.com may still contain historical stalagmites not surfaced by the constrained inspection pass

## Bottom line
Before the vendored binary work, the installer was **not first-try viable** unless the operator manually staged Authelia.
After this change, the installer is **substantially closer to first-try viable** on wm3v, assuming:
1. portal app is installed on its own dedicated domain (recommended: `auth.wm3v.com`) at `/`
2. first protected app is `home.wm3v.com`
3. LDAP bind password is supplied immediately after install
4. a VM snapshot exists before the first run

## Recommendation
I would now describe the installer as:
- **credible for a first real install with a snapshot**
- **no longer obviously underbaked on binary provisioning**
- **still deserving of caution because live lifecycle execution remains unproven**

That is a much stronger place than where we started.
