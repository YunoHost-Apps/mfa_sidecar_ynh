# Beta-gap closure plan

## What was closed
- package lifecycle wiring
- render/stage runtime loop
- managed runtime layout
- backup/restore handling
- include injection/removal helper exists for protected-domain rollout

## Remaining gaps to call this truly beta-shaped
1. **Live host validation**
   - run install/upgrade/remove on a YunoHost VM
   - validate nginx reload behavior and include placement

2. **Authelia binary availability**
   - currently explicit operator-supplied binary strategy
   - can be improved later with pinned checksum provisioning

3. **Least-privilege hardening**
   - move service off root once binary/runtime ownership constraints are tested
   - tighten file ownership and secret handling

4. **First-user and recovery realism**
   - confirm first-user bootstrap, login, enrollment, and operator recovery on a real host

5. **Control plane ergonomics**
   - current state is still file/config driven
   - future step is thin UI or YunoHost panel integration

## Honest conclusion
The project is now beyond bare-bones alpha and into a strong alpha / pre-beta candidate in repository form.
What keeps it from a confident beta label is mainly **live system validation**, not missing project structure.
