# Branching / publication model

## Intended branch roles
- `dev`: canonical development branch
- `main`: installer-facing distribution branch for GitHub/YunoHost installs

## Why
YunoHost expects an app/package repo shape at the top level (`manifest.toml`, `scripts/`, `conf/`, `sources/`, etc.).

But MFA Sidecar development is easier in a source-oriented repo with docs, tests, notes, and helpers that should **not** be the direct install surface.

So this repo uses a split model:
- work happens on `dev`
- package-root export is generated from `dev`
- exported package tree is published to `main`

## Operator rule
If you are installing MFA Sidecar from GitHub, use:
- `https://github.com/wonko6x9/mfa_sidecar_ynh`

That should resolve to the installer-facing `main` branch.

Do **not** install from `dev`.

## Maintainer workflow
From the dev branch:
1. update `package-base/` and source/docs/tests
2. run smoke tests
3. export package root into `dist/package-root/`
4. publish `dist/package-root/` to `main`

The distribution branch should be treated as a generated release surface, not hand-edited source of truth.
