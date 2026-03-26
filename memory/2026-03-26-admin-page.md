# 2026-03-26 — admin page direction

- John explicitly redirected work toward creating the **MFA Sidecar admin page**.
- Reviewed current notes/artifacts after reset.
- Confirmed intended operator UX from project docs + daily memory:
  - list managed host/path entries
  - on/off toggle per entry
  - add custom host/path entry
  - portal domain remains separate from managed targets
  - longest matching path wins stays mostly under the hood, but should be explained
- Repo state confirms package/render/staging work exists, but thin control plane/admin page is still the missing build item.
- Added `docs/ADMIN-CONTROL-PLANE.md` to lock down the alpha admin-page scope and implementation direction.
- Current build intent: create a small bundled local web app for operator control rather than attempting native YunoHost admin-panel integration first.
