# Live validation checklist

Use this when validating the current injection/reinjection architecture on a real host.

## Before touching the host
- confirm which branch/install surface is being used
- confirm the target app/domain and expected nginx conf path
- have the emergency-disable path ready
- prefer a clean host state or a snapshot/rollback point first

## Discovery / target selection
- verify the discovered `target_conf` actually corresponds to the intended YunoHost app nginx file
- verify the target location path exists in that file
- if discovery is wrong or ambiguous, set `target_conf` manually instead of trusting fallback guesses

## Injection correctness
- apply one managed target
- inspect the target nginx conf and verify the MFA Sidecar block appears inside the intended `location` block
- verify app-specific directives remain intact below the injected block
- run `nginx -t`
- reload nginx only after config validation passes

## Runtime behavior
- confirm unauthenticated request is redirected to the portal
- confirm authenticated request reaches the app normally
- confirm app-specific behavior still works (large uploads, DAV/websocket/rewrite semantics as relevant to the app)

## Regeneration survival
- run `yunohost tools regen-conf nginx`
- verify the injected block is restored correctly
- run an app upgrade/change-url scenario if practical
- verify reinjection does not duplicate blocks

## Break-glass behavior
- run emergency disable
- verify portal include hook is removed
- verify protected app-location injections are removed
- verify app becomes reachable again without sidecar gating
- verify sidecar state remains on disk for recovery

## Call it good only if
- target discovery is trustworthy or operator-overridable
- injection preserves app-specific nginx semantics
- regen/app lifecycle reinjection is stable
- emergency disable restores access cleanly
- no silent ambiguous-match behavior is observed
