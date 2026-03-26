# MFA Sidecar repo notes

This directory is now the canonical standalone git repo for MFA Sidecar.

## Remotes
- GitLab: `ssh://git@gitlab.wm3v.com:44220/shared/mfa_sidecar_ynh.git`
- GitHub: `https://github.com/wonko6x9/mfa_sidecar_ynh.git`

## Rule
Do not publish or push MFA Sidecar from the workspace root repo.
Work, commit, and push from `shared/yunohost-mfa-sidecar/`.

## Packaging shape
- Development/source-of-truth lives in this repo.
- YunoHost package-root export is represented by `package-base/` and related tests here, not by dumping package files into `/home/wonko/.openclaw/workspace/`.
