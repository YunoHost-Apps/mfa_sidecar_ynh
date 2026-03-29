# MFA Sidecar Restore / Remove Expectations

This document exists to set operator expectations clearly.

It is not a promise that nothing can ever go wrong. It is a guide to what the package is intended to do, what it relies on, and what to check when lifecycle operations behave strangely.

## Remove: what should happen

When the package is removed, it is intended to:

- stop and disable sidecar services
- remove sidecar-managed nginx auth injection blocks from target configs
- remove per-target bridge include files such as `mfa-sidecar-*.conf`
- remove the sidecar-generated portal/managed nginx snippets
- remove the app install directory and data directory through normal YunoHost lifecycle handling
- leave downstream apps themselves intact

### Important nuance

MFA Sidecar modifies other apps' nginx configs using marker-bounded managed blocks.

That means a clean remove depends on:

- the marker blocks still being present and recognizable
- the remove/reinject helper being available during the operation

If prior packaging failures or partial restores damaged the helper path, cleanup may need manual verification.

## Restore: what should happen

When the package is restored from backup, it is intended to:

- restore the package layout and shipped helper files
- restore sidecar policy, users, and secrets
- restore generated/staged runtime material
- re-enable sidecar services
- leave the system able to regenerate/reapply runtime cleanly

## What restore currently assumes

Restore expects the packaged source payload (helper scripts, docs, vendored Authelia artifact, etc.) to be present in the app archive in the same relative locations used by the lifecycle scripts.

That means packaging-path drift can break restore in ugly ways.

This is one reason the project now includes:

- a shared packaged-file install helper
- regression checks for shipped file references

## Practical operator checks after restore

After a restore, verify:

1. package exists in YunoHost app list
2. install dir exists
3. sidecar services exist and can start
4. `/etc/mfa-sidecar/nginx/protected/` is populated when managed targets are enabled
5. the portal loads
6. one protected target behaves correctly in an incognito window

## Practical operator checks after remove

After a remove, verify:

1. sidecar services are gone or inactive
2. sidecar-managed auth blocks are no longer present in target nginx configs
3. no stale `mfa-sidecar-*.conf` bridge includes remain in target nginx `.d/` directories
4. target apps still load as expected without sidecar
5. no stale sidecar snippets remain in `/etc/mfa-sidecar/nginx/protected/`

## Manual recovery mindset

If lifecycle behavior becomes inconsistent, do not guess.

Prefer to inspect:

- the package install dir (currently typically `/opt/yunohost/mfa_sidecar/`)
- `/etc/mfa-sidecar/`
- target nginx config files under `/etc/nginx/conf.d/`

And use the package's own render/stage/apply flow before inventing ad-hoc mutations.

## Why this document matters

The point is not to sound enterprise. The point is to keep operators from having to reverse-engineer package intent during a bad day.
