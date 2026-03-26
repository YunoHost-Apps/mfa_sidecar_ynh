# 2026-03-26 — upstream inference hardening

- Continued pre-install hardening after discovery work.
- Discovery suggestions now carry:
  - inferred upstream value
  - confidence (`high` / `medium` / `low`)
  - reason text for why that value was chosen
- Current inference posture:
  - nginx `proxy_pass` → high confidence
  - YunoHost app inventory without explicit upstream mapping → medium confidence fallback
  - nginx `root` or missing upstream → low confidence fallback
- Admin UI now exposes source usage and suggested-upstream confidence so the operator can see when a suggestion is a guess vs a strong mapping.
- Test suite caught two real regressions during this pass:
  - location parser was associating `proxy_pass` too loosely across locations
  - admin UI smoke test needed to follow updated `discovered_targets()` return shape
- Both were fixed and full smoke suite returned green.
