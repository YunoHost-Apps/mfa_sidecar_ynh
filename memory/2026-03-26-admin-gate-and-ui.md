# 2026-03-26 — admin gate + UI clarity

- John explicitly asked for both:
  - clearer domain/app presentation in the admin UI
  - a draft auth gate for `/admin`
- UI was kept aligned with the simpler YunoHost-first discovery model.
- Added an alpha admin gate:
  - generated shared secret in env
  - nginx requires `X-MFA-Sidecar-Admin-Secret` presence on `/admin`
  - admin UI also verifies the secret value
- Added smoke coverage for the admin gate and kept full suite green.
- This is documented as an interim hardening step, not the final auth UX.
