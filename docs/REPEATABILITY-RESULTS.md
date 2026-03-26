# Repeatability results

## Purpose
Move confidence from "it passed once" to "it appears stable under repeated dry-run execution".

## Repeated validation performed
- full smoke suite executed once as baseline
- full smoke suite then executed **3 consecutive times** via `tests/repeat_smoke.sh`

## Included checks during each run
- renderer smoke
- runtime staging smoke
- include injection/removal smoke
- edge-case policy rendering smoke
- include idempotence smoke
- failure-contract smoke
- vendored binary contract smoke
- package-tree dry-run smoke
- service contract smoke
- vendored Authelia install smoke
- repeated vendored binary extraction consistency smoke
- tampered vendored artifact rejection smoke

## Result
- all repeated runs passed
- no flaky failure observed during the repeated dry-run pass
- vendored Authelia artifact extraction remained consistent across repeated runs
- tampered vendored artifact was consistently rejected

## What this does and does not prove
### Stronger confidence in
- deterministic local packaging logic
- deterministic config rendering/staging
- deterministic vendored binary verification/extraction
- idempotent include helper behavior in dry-run scenarios

### Still not fully proven
- first real install on YunoHost host
- first live auth flow against LDAP with real bind password
- service startup/restart behavior on live host
- interaction with historical config stalagmites under real install conditions

## Practical conclusion
The package now has **repeatable dry-run behavior**, not merely one lucky green pass.
That materially improves confidence for a first snapshot-backed install.
