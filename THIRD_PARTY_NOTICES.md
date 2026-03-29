# Third-Party Notices

This package includes and integrates third-party software.

## Authelia

- Project: Authelia
- Upstream: https://github.com/authelia/authelia
- Website: https://www.authelia.com/
- Included here as: vendored pinned release artifact used by MFA Sidecar packaging/runtime
- License: Apache-2.0

MFA Sidecar currently installs a vendored Authelia release artifact from:

- `sources/vendor/authelia-v4.39.16-linux-amd64.tar.gz`

That vendored artifact is intentional. The package chooses a pinned, sha256-verified release input because this integration sits on a live authentication path and the project currently values reproducible installs/upgrades over install-time upstream fetching.

A copy of the upstream Authelia license text is included in:

- `licenses/Authelia-Apache-2.0.txt`

## YunoHost integration environment

MFA Sidecar is built to operate inside YunoHost and integrates with YunoHost-managed nginx and access control behavior (including SSOwat interaction on YunoHost systems).

This notice file is not intended to replace upstream licensing or attribution requirements for YunoHost itself or other software already distributed by the host system. It exists to document the software vendored or directly packaged by this repository.
