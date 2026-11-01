# Integration of one HPR ability into a pre-existing customer game

Evidence: actual Nitro Unity 6000.6.7f1 processes, November 1, 2026.
All files, receipts, and Editor logs are private disposable scratch outputs at
`/data/tmp/hpr-caltask33-20261101-0903`, **outside Git**. No publisher
operation, live customer project, or other agent's dirty source was changed.

## Buyer job and meaningful boundary

An experienced Unity developer already has a custom player controller, a
serializable ScriptableObject configuration, a prefab instance and a playable
scene. Add **one small healing ability**, preserving all those files, retaining
the existing input setup, and showing configurable C# authoring. Do **not**
replace the controller, import the whole original standalone HPR demos, edit
customer scene/prefab originals, or silently overwrite existing assets.

This exercise is a **self-authored representative customer fixture**, not a
real paid user's project or proof of a differentiated market opportunity.

## Actual source and test environment

The starting Unity 6.6 project was an independently verified copy of an
existing customer project upgraded from the prior archive to HPR v14. The
private customer fixture was created and serialized by the real Unity
Editor. An **additional new disposable copy** retained the customer's
original controller/scene/prefab/configuration. The currently dirty
`HprSuiteIntegrationGuide.cs` was **read only** and frozen into this copy;
its safe customer asset-copy function is not in the original v14 archive.
Private QA source on the separate branch:

- `unity/tools/release/gameplay_suite/qa/HprCustomerAbilityResourceBridge.cs`
  implements `IAbilityResourcePool` without replacing or editing the original
  controller. The fixture starts at forty health and one hundred stamina.
- `unity/tools/release/gameplay_suite/qa/HprCustomerExistingGameAbilityValidator.cs`
  creates a *new scene copy* and independently clones a customer-owned
  ScriptableObject ability and dependent effect with the vendor source frozen.
- `unity/tools/release/gameplay_suite/qa/HprCustomerAbilityPlaymodeValidator.cs`
  drives real Unity Editor Play mode and checks the actual ability resource
  state. The script is private testing code, not a production feature.

## Failures retained rather than disguised

The first actual Unity script compilation failed because the **private QA
builder** lacked `using HPR.GameplaySuite`; it did not execute the builder.
That one-line QA correction was made and the new invocation had a fresh log.

The second actual Unity invocation created the **new customer-owned demo
scene**, cloned the ability and its dependent effect, attached a separate
resource bridge and the HPR ability runner to the new scene's player, and
saved the scene. However, reopening it failed the readiness test:
`Saved ability is not configured and unlocked`. The failed scene YAML
contained the correct cloned asset reference but the serialized
`unlockAllConfiguredAbilities: 0` value. Calling runtime
`SetUnlockedAbilityIds` during authoring is insufficient to persist an
initial unlock across scene reload.

The failed Editor log and exact original failed scene are preserved as
`customer-healing-build-fixed-20261101.unity.log` and
`customer-healing-pre-repair-failure-scene-20261101.unity`.
The next step **did not replay the already completed asset creation**. A
targeted private `RepairExistingDemoUnlock` method set the existing
runner's `unlockAllConfiguredAbilities` serialized Inspector property using
Unity `SerializedObject`, saved only the disposable **new demo scene**,
reopened it, verified the ability was unlocked, and checked the original
customer/vendor file hashes and GUIDs. Actual Unity Editor receipt:
`customer-healing-inspector-repair-20261101.txt` reports three PASS checks.
The builder's future authoring path was also corrected to use the serialized
Inspector setting. A **different fresh disposable customer project** then
completed the entire corrected Editor authoring path on its first attempt,
without invoking the targeted recovery. The real Unity 6000.6 Editor process
exited zero and emitted `customer-healing-fresh-build-20261101.txt` with five
PASS observations: new customer scene, original buyer resources preserved,
independent copied ability/effect assets, preserved controller plus new
optional components, and serialized unlock retained after reloading the scene.
The new scene's YAML contains `unlockAllConfiguredAbilities: 1`.

Independent SHA-256 full-project comparison began with **forty-nine** original
non-vendor customer assets, ProjectSettings and Packages files before Unity
ran. After successful import, none of the forty-nine had changed or vanished.
Exactly **ten expected additions** appeared, all in the intentionally new
customer IntegrationDemos folder or new private QA script metadata. There
were zero unauthorized new paths. Evidence:
`customer-healing-fresh-build-baseline-20261101.json` and
`customer-healing-fresh-build-integrity-20261101.json`.

## Actual real Unity gameplay acceptance — PASS

A new disposable copy of the corrected scene was launched into **actual
Play mode**, with the customer's disabled-domain-reload Editor setting
preserved. The private Editor process reported all of:

- Original controller component and exactly its prior configured movement
  speed remained on the player.
- The new user-owned ability still referenced the **user-owned copied**
  effect, not the vendor asset.
- Ability activation restored exactly twenty health (forty to sixty).
- It consumed exactly twenty stamina (one hundred to eighty).
- An immediate second activation was correctly blocked by cooldown.
- The live Editor Play mode process exited with zero status after the receipt
  was saved. The original customer controller, scene, prefab, and serialized
  settings on disk remained byte-identical to the pre-experiment copies.

Evidence: `customer-healing-playmode-20261101.txt`,
`customer-healing-playmode-20261101.unity.log`, and the separate pre/post
customer original file SHA-256 comparisons. The ability effect is tested
in actual gameplay; this is **not merely a unit-test or Editor-asset check**.

The corrected **freshly built customer-demo project**, not merely the
repaired first prototype, independently completed another real Unity Editor
Play-mode run with all six gameplay checks passing, and the Unity process
exited zero. Evidence: `customer-healing-fresh-playmode-20261101.txt`
and `customer-healing-fresh-playmode-20261101.unity.log`.
The comprehensive post-build snapshot of **fifty-nine** protected non-vendor
Assets, ProjectSettings and Packages files was independently rechecked after
this fresh Play mode. All fifty-nine passed SHA-256 preservation verification;
no original or newly authored customer demo file changed. The actual
positive path is now tested without the earlier targeted repair method.

An `ArgumentOutOfRangeException` from
`UnityEditor.Search.SearchDatabase` startup indexing appears in this and
an earlier real domain-reload-disabled Editor log, even though gameplay
passed. It is not a HPR compile error, and its root cause has **not been
independently isolated in a package-free Unity project**. Keep this warning
visible as an unresolved Editor diagnostic rather than declaring every
Editor log clean.

## Not production-ready and not permission for submission

This is a deliberately limited technical proof with developer-written test
code. The HPR copy API must still be distributed in a **new, versioned,
independently validated actual release archive**, not just manually overlaid
on v14. The demo uses a private glue resource adapter; a paid feature still
needs its own robust Inspector authoring UX, actual compatibility diagnosis,
configurable integration with arbitrary real controllers and existing health
systems, undo/revert, incomplete-setup feedback, testable uninstall and
upgrades of vendor edits, and no unnecessary code rewrites.

No competent external developer has yet used HPR and a direct competitor in
the *same existing game* under measured conditions. No buyer demand, sales,
or willingness to pay is evidenced. Commercial verdict remains **NO-GO**.
