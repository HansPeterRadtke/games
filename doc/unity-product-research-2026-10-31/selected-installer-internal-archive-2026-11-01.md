# Internal Unity buyer archive containing the selected-object installer

Date: November 1, 2026. Status **INTERNAL / NOT SUBMITTED / NO COMMERCIAL GO**.

## Exact source and immutable-artifact origin

The original product-owner worktree
`/data/src/worktrees/unity-integrated-suite-20261030` contains fourteen
uncommitted owner/other-agent files. **This QA session did not modify them.**
The earlier frozen internal candidate was built under
`/data/tmp/hpr-caltask2fb-20261101`, from committed Games product source
plus four observed uncommitted owner buyer-source/docs files, overlaid with
the previously verified metadata preflight for orphan Unity `.meta`
destination files. That first candidate passed clean Unity 6.6 import,
thirteen serialized scene refs, twelve auxiliary checks, forty-seven
runtime source scripts, and ten actual integration/gameplay/save smoke checks;
it upgraded a customer game without changing fifty-nine protected files.

An **additional isolated, distinct candidate** was then built under
`/data/tmp/hpr-caltask2fb-selected-20261101`, by *copying* the frozen
source. It includes one extra optional Editor-only file,
`Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs`, which
had previously passed its own real Unity 6.6 Editor attach/Undo/Redo/
serialization/window structure checks in a private customer game, and
adds documentation for this experimental feature. The candidate has a
new unique, deterministic Unity `.meta` GUID for this Editor source
while retaining the original guided-integration source and all
pre-existing asset GUIDs. A reviewable, source-only patch is recorded at
`patches/add-selected-installer-to-private-archive-20261101.patch`.
The patch was verified with `git apply --check` against the earlier
**frozen private** source, but was not applied to the owner's dirty
product worktree.

Build commands use the original owner Unity release builder with
`HPR_SUITE_PROJECT_ROOT`, `HPR_SUITE_RELEASE_ROOT`, and
`UNITY_BIN` intentionally set to **new paths**, with real installed
Unity 6000.6.7f1 running in batch mode. This is a local `.unitypackage`,
not an online store upload. Logs/source manifest/release receipts and SHA
checksum are saved inside the private release directory, not in Git.

The real Unity export exited zero on the installer-enabled candidate.
The independent archive reader reported **one hundred and sixty-one
buyer assets**, ten original runtime modules, one original real Unity
arena scene, **three Editor scripts**, no test assemblies/UGUI dependency,
the original authoring GUID/YAML baselines, the AI disclosure and
single package root. Compared with the prior frozen internal archive,
all **one hundred and sixty shared asset GUIDs were unchanged**, no asset
was removed, and the **one new Editor source** was the only added file.
The archive contains the exact patched guide and selected-ability installer
C# source bytes, with no C# errors, C# warnings or obsolete API messages
reported in the real Unity 6.6 export compilation logs.
Evidence: `snapshot-prototype.json`, `archive-integrity.json`,
`build.stdout.log`, `release/build-export.unity.log` and
`release/hpr-gameplay-systems-suite-candidate.unitypackage`.

## Actual source-only and customer Editor tests already performed

The selected installer source has source-contract tests for safe
non-automatic behavior, public Unity Undo and serialized Inspector
property APIs, read-only preview/validation and UI Toolkit controls.
These source checks alone never establish product correctness.

In a separate real **Unity 6000.6.7f1** private customer game, the
installer prototype (source overlay, *before* it was packaged) actually
attached a customer-owned healing ability to an existing player,
left the original controller/prefab/settings unchanged, supported Undo
and Redo, retained inspector state through a scene save/reload and
constructed the selected-object Editor UI. All sixty-one protected
previous customer files retained their SHA-256 bytes; only the new scene
and two private QA script .meta files were created. See
`selected-ability-installer-experiment-2026-11-01.md`.

## Acceptance verified against the EXACT new archive

The Unity 6000.6.7f1 **export** process exited zero on the *new* package,
and the independent source/structure validator read exactly **161** buyer
assets, **ten** runtime modules, one real training-arena scene and three
Editor scripts. The prior **160** assets retained their exact GUIDs and
there was just one additional stable Editor-source GUID. The archive
actually contains the metadata-safety preflight and the selected-installer
source matching the frozen source byte for byte, with zero C# compiler
errors, warnings or obsolete-API messages in export logs.

**Customer upgrade:** an earlier fully populated Unity 6000.6 customer game,
which already contained its own controller, prefab, scenes and independent
ability assets, imported **this exact archive** successfully. A digest
comparison of all **59** pre-existing nonvendor Assets, ProjectSettings
and Packages files passed: **zero modified or deleted originals**.
Its new selected Editor script source matched the frozen and archived bytes.
Evidence: `customer-selected-import.unity.log`,
`customer-existing-pre-import.json`, and local actual package contents.

**Customer Editor operation against the installed archive:** private
`HprSelectedAbilityInstallerValidator` was appended *after import* only
as test code. Actual Unity 6000.6 Editor invoked the **installed** buyer
script, not a QA substitute. All eight checks passed: safe invalid input,
explicit selected-object add, Undo and Redo, serialized Inspector state after
new scene save/reopen, preservation of the customer's controller and
settings, actual UI Toolkit fields/buttons/status and no automatic scene
save/project configuration mutation. Independent SHA-256 verification
found all **59** original customer files unchanged, plus only the two
intended new demo scene/meta and private validator script/meta. Evidence:
`customer-installed-installer-editor-receipt.txt`,
`customer-installed-installer-editor.unity.log`, and
`customer-installed-installer-file-integrity.json`. No C# compiler error
or warning was found in this actual installed-package Editor test.

**Unity 6000.4.0f1 cross-version import:** the same new archive was
imported in a separate private real Unity 6.4 Editor. The process exited
zero, retained all **27** previously present protected test-game files,
and reported `CUSTOMER_INTEGRITY_PASS 27`. This verifies source compile
and importer compatibility, not a complete second customer authoring
study or URP combined on that older Editor version.

These successes are evidence of real Unity Editor tasks and source integrity.
They do not imply that buyers can integrate arbitrary external controllers
without supplying an ability-resource provider, nor that users will pay.

## Cross-version and runtime gates verified for the exact archive

**Clean Unity 6000.6.7f1 project:** the installer-enabled exact archive was
imported into a wholly new Unity project and independently passed all
**thirteen scene references**, **twelve supporting assets**, **forty-seven
runtime scripts** and **ten real gameplay/save integration checks**, including
JSON disk save/restore and corrupted-state rejection. The actual Unity
process completed with exit zero. Evidence:
`cleanroom-selected.stdout.log`, the separate Unity create/import/scene/
runtime logs and the scene/runtime receipts in the release directory.

**Domain reload disabled:** a new disposable copy of the exact installed
archive, with the independent private Unity Editor state validator, entered
Unity 6.6 Play mode **twice** without domain reload and passed fresh
vitals/inventory/weapon state, exact one-time typed combat event delivery
and registry reinitialization. The actual Unity process completed with
exit zero, reporting `domain_reload_disabled_two_editor_play_entries=PASS`.
Evidence: `selected-domain-reload-disabled-receipt.txt` and its Unity log.
The separate `UnityEditor.Search.SearchDatabase` indexer exception also
appears, but is independently reproducible with HPR source absent.

**Unchanged original gameplay and URP sample assets:** exact tar asset-byte
comparison to the historically verified v14 buyer archive found all
**one hundred and sixty shared file paths**. Only four paths differ:
the three authoring guides and the patched original Editor guide.
The sole additional buyer asset is the new selected Editor installer.
**All eighty inspected runtime source, scene, sample ScriptableObject
and material asset files are byte-for-byte unchanged**; no prior
asset path or GUID was removed. Evidence:
`runtime-material-identity-v14-v16.json`.
This supports traceable reuse of the v14 URP test results, but does **not**
replace an actual complete URP import and new-input-only Play-mode test
on the exact newer archive.

**Persistent private release evidence:** the exact new archive, frozen
source and manifest hashes were copied into a private, restrictive
access folder outside Git at
`/data/var/marketplace-account-setup/hpr-unity-internal-selected-installer-20261101`.
Its `IMMUTABLE_RECEIPT.json` and README explicitly state **not approved,
not submitted**, no public provider effects. The original concurrent dirty
owner product branch was not modified. The scratch projects and Unity QA
receipts remain under `/data/tmp/hpr-caltask2fb-selected-20261101`.

## Acceptance gates for the EXACT new selected-installer archive

The real Unity 6.6 cleanroom, source/metadata, repeated
Play-mode/domain reload and selected-installer customer workflow all
passed. Unity six point four compilation/package import also passed, with
all twenty-seven original test files unchanged. The remaining open
gates are a **completed exact-package** URP 17.6 and modern-input-only
combination test, actual user-facing screenshot/layout/accessibility QA,
asset migration/uninstall when a customer game truly depends on HPR,
independent buyer/competitor task-time measurement and publisher approval.
A URI/import request or earlier v14 result is not proof those later
checks completed.

## Commercial blockers

The generic ten-module offer does **not** have verified differentiated
market demand. PackageLens offers free import conflict previews.
Ability System Kit and Game Creator 2 have broader paid workflows.
The selected installer reduces source editing for one already configured
ability, but still requires a buyer-side IAbilityResourcePool provider,
valid independent AbilityData and customer-permitted scene changes.
Its UI has not been independently visually audited across layouts,
or benchmarked by experienced external developers against real
competitors. No sale, publisher approval, identity verification or
willingness to pay has been verified.

**Commercial verdict: NO-GO.** This archive, even if all technical QA
passes, is only an internal QA candidate pending commercial research
and the owner's specific release decision.
