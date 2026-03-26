# Authelia binary provisioning strategy (alpha-to-beta bridge)

## Current recommendation
Use a **vendored pinned release artifact** in the package sources for the tested target architecture, with checksum verification before installation.

This repository now follows that direction for the Linux amd64 test target.

## Why
- avoids brittle network fetch during YunoHost app install
- keeps supply-chain review explicit
- reduces surprise failures during install/upgrade

## Implementation direction
The package should:
- carry the pinned tested release artifact in `package-base/sources/vendor/`
- verify the artifact sha256 before use
- install the verified `authelia` binary into `/usr/local/bin/authelia`
- fail crisply on checksum mismatch or extract failure

## Later improvement
Add architecture-aware vendoring/update workflow and refresh procedures for future version bumps.
