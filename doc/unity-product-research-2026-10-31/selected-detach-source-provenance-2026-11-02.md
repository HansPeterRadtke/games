# Selected ability detachment — frozen source-only proposal

November 2, 2026. Nitro. **QA only — not a compiled or published Unity Asset Store package.**

The previous immutable Unity internal candidate has **161** buyer assets and
has been successfully imported into clean and populated Unity 6.6 buyer
projects, with Unity 6.4 import and original GUID preservation verified.
Its selected-object Editor installer supports explicit attachment, Unity
Undo/Redo and Inspector persistence, but it does not include a later
separate removal button.

A November 1 **independently isolated Unity Editor test** already verified
a private component-only detachment modification: owner-approved scene
object, no prefab asset edits, Undo restoration of the serialized ability,
Redo component removal, and preservation of original controller, settings,
ability assets and GUIDs. The exact tested source modification exists as
`patches/reversible-selected-ability-detach-20261101.patch`.

## Additional real engineering work on November 2

A new **private source-only** proposal was staged at Nitro's local
marketplace-account-setup working area, separate from the immutable 161-asset
Unity archive and separate from all owner/other-agent dirty worktrees.
The proposal begins with the previous exact archive's full source snapshot
and applies only that independently verified removal patch to
`HprSelectedAbilityInstaller.cs`. Three buyer documentation
files were updated to explain the new remove control and its strict limits.

The new independent read-only source verifier
`unity/tools/release/gameplay_suite/qa/verify_detach_overlay.py`
has test-first regression cases in
`tests/test_unity_detach_source_snapshot.py`. It checks
every previous file identity, every .meta GUID byte, exactly four authorized
source/documentation changes, the presence of public Unity Undo and
read-only validation APIs, forbidden asset-delete/implicit scene-save calls,
and explicit not-yet-released documentation.

The first read of the **actual** historical source snapshot failed closed:
the original unrelated Unity helper-project tree contains symlinks that
the initial verifier refused to follow. Further inspection identified
two relative links to the source's own packages and **two pre-existing
absolute links** to the older main games checkout under
`unity/tools/assetstore/helper_project/Packages`. These
non-shipping helper aliases were already present in both original and
proposed source. The verifier was corrected to inspect symlink *text*
rather than following targets, accept stable internal relative links,
allow only those narrowly recognized, unchanged non-shipping absolute
helper aliases while reporting them, and reject every other
external/unexpected symlink. The first failed audit receipt was retained.
The real source audit then passed:

- **1,093 original source-tree entries** compared, unchanged path set.
- Exactly **four changes**: the selected Editor installer and the three
  explicitly updated buyer documentation files.
- **516 .meta identity files** byte-identical to their frozen originals.
- Two unchanged **non-shipping** absolute helper symlinks disclosed.
  The *entire old source checkout* is therefore not fully hermetic; the
  standalone Gameplay Suite release-script subtree has no such external
  symlinks. Do not claim the whole unrelated helper-project checkout is
  a completely self-contained release.

All eight new synthetic source verifier cases pass, including forbidden
GUID changes, added/missing files, external symlink escape, misleading
documentation, missing detachment implementation and forbidden
destructive APIs. Combined with the previous broker/Unity tests the QA
suite passed **81** Python tests.

## Independent offline C# API compilation

An additional small **offline .NET eight** compiler project referenced
**167** installed Unity six point six managed Editor/Engine modules,
the **47** original HPR runtime C# files and the newly patched selected
Editor installer source. Its source-only API compilation completed
successfully, with **zero compiler errors** and **three C-sharp warnings**
for Unity-serialized private fields that the standalone compiler cannot
see assigned by Unity's Inspector. This is NOT a Unity Editor compile,
not a package import, not proof of actual runtime behaviour and not
permission to ship the .NET eight assembly. The original Editor
six point six package tests were for the previous internal archive;
the new detachment patch has not been compiled inside a new Unity
archive yet.

A separate offline Unity six point four managed-reference check found
that twenty-three Unity six point six modules did not exist under the
older Editor distribution. Its later standalone compilation attempt
did **not complete**, so no new Unity six point four compatibility
claim is made for the detachment source. The original attach-only
archive's Unity six point four importer did pass.

The private source-only proposal contains a full source manifest, an
exact permitted-change audit receipt and an explicit warning that it is
**not an independently compiled commercial product**. The original
binary archive remains SHA-pinned and unchanged.

## Current broker-controlled Unity testing

The installed Unity six point six URP plus modern-only Input System
acceptance remains incomplete. A resource-broker-supervised Nitro
worker is running with an actual CPU/memory quota, no reservation
while CPU is overloaded, and a twenty-four-hour bounded monitoring
window. It only requests a proper secure broker lease after repeated
acceptable CPU pressure and no existing Unity instance. Its original
idle predecessor was unloaded via its own broker control token, without
touching other owners' processes. The new worker has a tested own
Unity process-group cleanup: a timed-out Editor and its own Bee/compiler
children are terminated together; a misleading zero exit with a
live child is also treated as failure. The worker creates new unique
projects and never blindly repeats uncertain partial imports.

Nine earlier plus one additional clean-process synthetic worker
tests passed, and the combined Python suite now has 81 passes. No
new real Unity URP import success has yet occurred in this worker.

## Remaining required acceptance and commercial conclusion

Build a new, separately frozen internal Unity package **from this
source-only detachment proposal** once CPU resources are available,
then independently test the actual packaged add/remove/Undo/Redo
workflow and unchanged customer data, URP plus modern/legacy input
combinations, scene rendering and accessible Editor UI. Reconcile
other agents' uncommitted product changes only through owner-approved
review; no live product source was overwritten. A dependent-game safe
migration/uninstall workflow remains unimplemented. Experienced
developer comparison with real competing products, completion-time
and purchase-intent evidence are absent.

**Commercial verdict remains NO-GO. No publication, account change,
purchase or Asset Store submission occurred.**
