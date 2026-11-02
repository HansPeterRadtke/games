# Customer asset copy — prevent unrelated unsaved Inspector edits being saved

Date: November 2, 2026, Nitro. **Independent engineering QA only.
Not a shipped feature or tested new Unity package.**

## Buyer risk discovered from actual source and official Unity API semantics

The current private HPR seller package has an Editor Integration Guide
that explicitly copies vendor sample ScriptableObjects and their
dependencies into a customer's Assets folder. The new copies are intended
to have unique GUIDs and independent identifiers. The previous guide
ended that operation with `AssetDatabase.SaveAssets()`,
which according to the **official Unity API documentation** saves **all
currently unsaved asset changes** in the project, not just the new copies.

Therefore a developer who was editing an unrelated customer ScriptableObject
in another Inspector could have those pending edits saved to disk when
pressing HPR's "Create my own healing ability" button. This is a
**documented API-level side-effect risk**, not yet a reproduced
adversarial Unity Editor failure in the user's customer project.

Unity first-party documentation:
- https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetDatabase.SaveAssets.html
- https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetDatabase.SaveAssetIfDirty.html
- https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AssetModificationProcessor.OnWillSaveAssets.html

Unity's `SaveAssetIfDirty(Object)` writes only the
**specified asset** if dirty. It explicitly does **not** invoke
`AssetModificationProcessor.OnWillSaveAssets`, in contrast
to general `SaveAssets`. This is a relevant tradeoff for
custom version-control/locking callbacks: it must be reviewed rather
than silently marketed as completely compatible with every VCS workflow.

## Isolated, exact-scope engineering fix

A new internal private **source-only** copy was staged at:
/data/var/marketplace-account-setup/hpr-unity-sample-copy-isolated-save-20261102`.

It starts from the previously SHA-verified 161-asset internal seller
candidate plus the already separately tested QA-only component-detach
source proposal. Only the existing guide's global save operation was
replaced with a loop that loads each newly created customer-owned copy
and calls `AssetDatabase.SaveAssetIfDirty(copy)`.
The loop refuses a missing cloned asset rather than silently ignoring
it. No previously existing buyer asset, vendor-owned sample or project
setting is intentionally saved by the new code.

The minimal independent reviewable patch is:
`patches/hpr-copy-save-only-authored-assets-2026-11-02.patch`.
It applies cleanly to the previous frozen guide. The immutable
161-asset candidate binary and the other agent's fourteen uncommitted
owner source files remain untouched.

An independent full snapshot comparison confirmed:
- **1,093 original source-tree paths** present with no additions/removals.
- Exactly **five expected edited paths** versus the frozen original:
  the original four source-only detachable-installer/doc changes,
  plus the corrected integration guide C# file.
- **All 516 source-controlled Unity metadata files byte-identical**.
- All four pre-existing source-tree symbolic links unchanged, including
  the two pre-existing non-shipping external helper-project aliases.
- A separately preserved source manifest lists the patched guide SHA-256.

## Actual tests completed and remaining work

Three test-first deterministic Python source/validator contracts passed,
covering replacement of the global save, targeted clone-only saving and
the private Unity Editor test fixture. The *genuine Editor test* code
`HprUnrelatedDirtyAssetValidator.cs` has been prepared
but **not executed** against Unity while Nitro's broker reports high CPU
pressure and the existing URP job has resource priority.

That test will deliberately leave a customer's independent
`CustomerHealing.asset` unsaved in memory, invoke the
real HPR sample copier, and compare the unrelated asset's disk SHA-256,
original scene, vendor source and GUID metadata before/after the copy.
It will also ensure the cloned healing ability still has its newly
owned effect reference and unique ID. The validator writes a private
PASS/FAIL receipt and is not included in the buyer package.

A disposable populated Unity 6000.6.7f1 customer-project copy with the
patched guide, private validator, and **64 customer/project settings
files baselined** is staged under
/data/tmp/hpr-unity-dirty-asset-save-qa-20261102`.
The test's new output path did not exist, and original customer asset
bytes were independently checked against the source project before
staging. Unity Editor has not yet been launched for this experiment.

Separately, a lightweight **offline .NET8 C# compile** referencing
the actual Unity 6.6 managed API assembly files, 47 original HPR
runtime source files, the revised Editor Integration Guide and the
private validator passed with **zero compile errors** and three
warning CS0649 messages from fields Unity serializes through its
Inspector. This is an API/syntax check only and not a Unity Editor
compile, runtime check or marketplace package acceptance. Its log and
project are retained in a private QA scratch folder.

## Release decision

The relevant product and market decision remains **NO-GO**. Before
signing off, run the real Unity test with an unrelated dirty customer
asset, inspect whether targeted saving changes VCS callback behavior,
build a new immutable exact archive containing both the reviewed
detacher and targeted save fix, and rerun purchaser cleanroom/import,
custom controller preservation, URP/modern input, visual Inspector
usability, full migration/uninstall and independent competitor/buyer
value checks. No publication or other provider effect is authorized
by this source-only result.
