# MFA Sidecar reviewer-response cheat sheet

Use this when responding to YunoHost catalog/package review comments.

Keep responses short, concrete, and evidence-based. Do not over-argue. Answer the actual concern, provide the relevant rationale, and say what you changed or will change.

## 1. “Why is this category `system_tools`?”

Suggested response:

> I picked `system_tools` because MFA Sidecar is primarily infrastructure/auth perimeter glue for other apps, not an end-user app category in its own right. It manages protection, routing, runtime generation, and recovery behavior around existing YunoHost apps. If maintainers think another existing category fits better, I’m happy to adjust.

## 2. “Why is Authelia vendored instead of fetched at install time?”

Suggested response:

> This was a deliberate reliability/supply-chain choice. MFA Sidecar sits on the login path for protected apps, so reproducible install/upgrade behavior matters more than usual here. The vendored pinned artifact is sha256-verified and is the exact artifact exercised during real-box validation. I’m not treating the tarball as blind trust; I’m optimizing for reproducibility on a security-sensitive integration surface.

Shorter version:

> Because unexpected upstream fetch drift/outage is a worse failure mode for a login-path package than carrying a pinned verified artifact.

## 3. “Why not just use YunoHost SSO / why does this need to exist?”

Suggested response:

> Because the practical gap is MFA in front of arbitrary downstream web apps. YunoHost SSO does not magically give every app native MFA. MFA Sidecar is meant to provide a browser-first MFA perimeter for selected host/path targets even when the downstream app does not natively understand MFA.

## 4. “Isn’t this just a thin wrapper around Authelia?”

Suggested response:

> No. Authelia is one component, but the package work is in the integration layer: policy/render/apply pipeline, admin UI, YunoHost-aware app/domain discovery, managed nginx auth-request injection, break-glass controls, restore/remove behavior, and operator/recovery documentation.

## 5. “Why is the admin UI bound to localhost and relying on nginx/YunoHost auth?”

Suggested response:

> That is an explicit documented trust boundary, not an accident. The admin UI binds to loopback and relies on the fronting YunoHost/nginx layer for access control. I documented that clearly in `docs/SECURITY-NOTES.md` so the boundary is reviewable instead of implicit.

## 6. “Why block the username `admin`?”

Suggested response:

> Because it caused real-box ambiguity/failure on a live YunoHost system due to collisions with existing platform identity expectations. This was not theoretical hardening; it came from live validation. Blocking it is the safer operator default.

## 7. “How well has this actually been tested?”

Suggested response:

> In addition to repo-local smoke/regression tests, the package was validated on a real YunoHost box. That included fresh install under `/var/www/mfa_sidecar`, service health, root-mounted and subpath-mounted protected targets, shared-session behavior, disable/re-enable loops, and break-glass behavior.

## 8. “What are the sharp edges / trust boundaries?”

Suggested response:

> The main sharp edges are intentionally documented: loopback-admin trust boundary, root helper applying generated runtime state, nginx marker injection into managed target configs, local SMTP assumptions for recovery mail, and the vendored Authelia artifact decision. The package is trying to be explicit and recoverable, not magical.

## 9. “Why should this be in the official catalog?”

Suggested response:

> Because it covers a real self-hosting/YunoHost use case that is currently awkward: putting MFA in front of existing apps that do not natively support it, while keeping recovery and operator control explicit. The package is opinionated, but it solves a real operational gap.

## 10. “Would you change X if reviewers prefer Y?”

Suggested response:

> If it improves catalog fit or packaging compliance without regressing the real-box behavior we already validated, yes. If it would increase fragility on the login path, I’d prefer to discuss the tradeoff explicitly instead of pretending the change is free.

## Tone guidance

- Be calm.
- Be specific.
- Don’t write essays unless they ask.
- Don’t get defensive just because a reviewer is grumpy.
- If they are right, say so and fix it.
- If they are wrong, disagree with receipts.
