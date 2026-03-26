# Policy model pivot: managed host+path entries

## Why the pivot happened
The earlier `protected_domains` model was too simplistic for real YunoHost deployments where:
- some sites should be toggled on/off manually one at a time
- some applications live on top-level domains with path-based installs
- a deeper subpath may need to override a broader host/root rule

## New model
Use explicit `managed_sites` entries instead of only domain-centric protection rules.

The **portal app itself** is separate from managed sites and must live on its own dedicated domain at `/`.
Managed sites are the targets being protected or bypassed.

Each entry has:
- `id`
- `host`
- `path`
- `enabled` (primary on/off switch)
- `upstream`
- optional `label`

## Rule semantics
- default policy should be `bypass`
- managed entries are explicit operator-managed objects
- **longest matching path wins** for a given host
- this allows exceptions such as:
  - `wm3v.com /` -> protected
  - `wm3v.com /nextcloud` -> bypass
  - `wm3v.com /nextcloud/apps/files/morestuff` -> protected

## Why this is intentionally "reverse" from some security systems
The operator goal here is practical, reversible access control on mixed-use hosts.
That means a more specific path often needs to create a bypass exception inside a broader protected rule.

## Product/UI implication
The admin surface should focus on:
- a list of managed sites
- on/off toggle per entry
- add custom host/path entry form
- refreshed list showing the new entry immediately

Advanced rule semantics stay under the hood; the visible control should remain simple.
