# 2026-03-26 — policy seed fix

- Caught an install-time conceptual bug: the seeded policy was creating a managed entry for the portal domain itself (`portal_root_seed`).
- That contradicted the intended model where the sidecar portal is its own dedicated domain and managed targets are separate host/path entries.
- Fixed the seed policy to start with `managed_sites: []`.
- Updated alpha notes to explicitly tell the operator where to retrieve the generated admin-gate secret for `/admin`.
- Added a lightweight smoke contract test to ensure the helper script no longer seeds `portal_root_seed` and still includes the admin-gate secret wiring.
