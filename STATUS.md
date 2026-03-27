# STATUS.md — MFA Sidecar

## Current phase
Browser-first v1 perimeter shell confirmed; local package hardening is strong, and the remaining meaningful uncertainty is live host validation plus operator UX polish

## Current recommendation
Use **Authelia** as the sidecar auth engine for a **browser-first perimeter shell** in front of selected YunoHost-managed web apps, with:
- passkeys / WebAuthn primary
- TOTP fallback
- separate sidecar-owned credential + MFA store
- thin custom control plane for managed host/path entries and generated config
- remembered-device/session behavior to reduce repeat prompts
- explicit non-goal for v1: mail protocols, sync/mobile-client-first apps, and generic protocol-wide firewall behavior

## Why this path currently leads
- cleanest fit to the gatekeeper model
- removable without invading YunoHost internals
- supports the desired passkeys-first posture
- lighter and more sidecar-shaped than a full IdP platform

## Current open questions
- exact recovery-code/operator recovery strategy for first live install
- whether the temporary `/admin` shared-secret gate is acceptable for first live install or needs one more UX pass afterward
- whether YunoHost-driven user sync should eventually become automatic/scheduled rather than operator-triggered only
- how the operator bootstrap/config story should look so a fresh install does not strand the user at a login page with no obvious way to create users or define protected targets

## Current checkpoint
The repo is now in a **documented alpha package state with strong local validation**, and the nginx protection model has been materially corrected:
- package lifecycle scripts are in place
- policy seed + renderer + runtime staging are aligned
- bundled admin UI works for add/edit/delete/toggle/apply
- protected targets now use **location-block injection + reinjection hooks** instead of generated replacement `location` blocks, which better preserves app-specific nginx behavior
- direct Authelia portal is live and reachable once bootstrap/user and permission bugs are corrected
- GitHub `main` is the installer-facing package branch, while GitLab mirrors that package view on `github-package`
- browser-first perimeter-shell framing is the right v1 scope; protocol-wide/firewall-like behavior is out of scope for now
- earlier install iterations exposed real operator-footgun classes: publish drift, runtime permission mistakes, bootstrap confusion, and nginx-shadowing semantics; the repo now contains fixes and regression coverage for those classes, but they still need live-host confirmation
- first-run UX is improved but still rough around the edges: the operator path exists in config actions/docs, yet it still needs live validation to prove a fresh admin will not get stranded at the login page
- the injector is deliberately conservative and tested against a few uglier nginx shapes, but it is still not a full nginx parser; ambiguous or missing targets should fail loudly rather than guess

## Immediate next step
Run live-host validation against a compatible browser-first target app, with special attention to discovery/target-conf accuracy, reinjection survival after regen-conf/app upgrade, and emergency-disable recovery behavior.
