# YunoHost packaging notes for MFA Sidecar

This file captures authoritative packaging guidance gathered after the failed wm3v install attempts, so the next pass starts from YunoHost expectations instead of donor inference.

## Sources consulted
- YunoHost packaging overview: `https://doc.yunohost.org/en/dev/packaging/`
- YunoHost manifest docs: `https://doc.yunohost.org/en/dev/packaging/manifest/`
- YunoHost config panels docs: `https://doc.yunohost.org/en/dev/packaging/advanced/config_panels/`

## High-confidence takeaways

### 1. Package-root-at-top-level is real, not optional
YunoHost packaging docs describe a conventional app repo/package with top-level items like:
- `manifest.toml`
- package scripts/resources/config files at repo root

This validates the installer-facing `github-package` branch approach.

### 2. Stick to YunoHost conventions, even when they feel arbitrary
The packaging overview explicitly says that while some conventions are historical or inelegant, it is still more important to align with common community practices than to invent a cleaner private structure.

Implication for MFA Sidecar:
- keep development/source layout if useful internally
- but the install-facing package must stay boring and convention-aligned
- do not keep improvising packaging structure from first principles

### 3. YunoHost expects admin-facing configuration to be considered through config panels
The config panel docs explicitly position `config_panel.toml` + `scripts/config` as the standard mechanism to expose useful admin settings in YunoHost's web UI.

Important wording from the docs, paraphrased:
- config panels are meant to expose app settings to YunoHost admins through a nice web UI
- most use cases should be covered automatically by the core
- packagers should keep things simple and expose only useful high-level parameters

Implication for MFA Sidecar:
- our custom `/admin` operator UI may still be justified for richer managed-site workflows
- but we should no longer assume it is the correct first/default admin integration model
- tomorrow's task should explicitly compare:
  - native config panel for simple settings / state
  - custom `/admin` app only for workflows YunoHost config panels cannot reasonably express

### 4. Install questions and app config are separate concerns
The manifest docs reinforce that:
- `manifest.toml` install questions are for pre-install choices
- ongoing admin-side configuration belongs in config panel / settings mechanisms, not ad-hoc install questions forever

Implication for MFA Sidecar:
- install-time questions should stay minimal
- admin operations after install should be reviewed against config-panel suitability

## Concrete questions to answer next
1. Should the current `/admin` managed-site workflow remain a bundled app at all?
2. Which pieces should become native YunoHost config-panel fields instead?
3. If `/admin` remains, what is the smallest justified scope for it?
4. What does YunoHost expect for icon/admin presentation in practice for operator-focused apps?
5. Are we fighting the platform by using a dedicated custom admin UI where a config panel would be more idiomatic?

## Practical next move
Before the next live install attempt:
1. inspect example/real YunoHost apps that use config panels
2. inspect apps with more complex operator/admin UX to see what they do for admin workflows
3. decide whether MFA Sidecar should split into:
   - native config-panel settings
   - optional richer `/admin` workflow only for managed target editing/actions

## Bottom line
The docs do **not** prove that the current `/admin` model is wrong.
But they do prove that we should stop assuming it is the default or most YunoHost-native answer.
