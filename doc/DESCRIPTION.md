# MFA Sidecar

MFA Sidecar adds a browser-first MFA perimeter in front of selected YunoHost apps and paths.

It provides a dedicated authentication portal, a sidecar-owned user store, operator controls for host+path targets, and an explicit break-glass bypass model. The package is designed for the practical problem of protecting existing web apps that do not natively understand MFA.

Current strengths:

- protects apps at host + path granularity
- supports operator-managed Protect vs Bypass target state
- keeps MFA and recovery concerns explicit instead of implicit
- favors live recoverability over clever lockout-prone automation
- has real-box validation for root-mounted and subpath-mounted protected targets

This package should be evaluated less as a thin wrapper around Authelia and more as an integration layer for YunoHost lifecycle, nginx injection, runtime generation, and operator recovery.
