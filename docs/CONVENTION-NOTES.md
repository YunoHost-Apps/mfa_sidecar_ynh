# Convention notes

## Current packaging posture
The goal is for MFA Sidecar to behave like a boringly normal YunoHost package as much as practical, while still carrying the extra integration logic it needs.

## Repo hygiene expectations
- generated test artifacts belong under `tests/out/` only during execution
- generated deploy artifacts under `deploy/generated-alpha/` are disposable and should not be treated as source files
- Python `__pycache__` directories and `.pyc` files should never be committed

## Package identity split
- human-facing package name: `MFA Sidecar`
- package/app id: `mfa_sidecar`
- engine underneath: `Authelia`

## Admin-side nature
This package should be treated as an admin/operator tool, not a normal end-user dashboard application.

## Portal rule
The sidecar portal app itself must be installed on its own dedicated domain at `/`.
