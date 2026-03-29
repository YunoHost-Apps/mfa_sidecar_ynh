# MFA Sidecar admin notes

For installation, operations, and recovery guidance, see the richer packaged docs in:

- `docs/ADMIN.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESTORE-REMOVE.md`
- `docs/LIVE-BOX-VERIFICATION.md`

Admin highlights:

- the portal should live on its own dedicated domain
- protected targets are enforced by generated Authelia config plus managed nginx auth-request injection
- `access_control.enforcement_enabled: false` is the primary break-glass switch
- `/admin` is the main operator control plane for target management and runtime apply actions
- target protection should always be validated live after meaningful runtime or packaging changes
