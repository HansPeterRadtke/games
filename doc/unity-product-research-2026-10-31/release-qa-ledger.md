# HPR Unity Gameplay Suite — Release Engineering QA Ledger, October 31, 2026

This ledger distinguishes verified evidence from open gates. It is not a publisher approval statement and does not authorize a Unity Asset Store submission.

## Evidence already verified

The latest known build on Nitro is the internal candidate in `/data/var/marketplace-account-setup/unity-consolidated-20261031-v12/release`, built with Unity 6000.6.7f1. The Unity editor completed the exporter and recorded no C# source warnings in the release log. The buyer artifact remains outside Git. Its release receipt explicitly states `INTERNAL_QA_CANDIDATE_NOT_SUBMITTED_NOT_PUBLISHED`.

The candidate contains one `Assets/HPRGameplaySuite` root with ten runtime modules, the existing editor generator and optional UI Toolkit integration guide, original demonstration scene, sample definitions, materials, user documentation and required AI-use notice. It includes no runtime NUnit assemblies, unrelated standalone demos, external model pack or additional publishing binaries. The static archive validator accepted 160 Unity assets and independently verified the exact published path-to-GUID identities of all 52 source-controlled authoring metadata records and byte-for-byte identity of the 22 source-authored scene/data/material YAML files.

A separate `qa/validate_upgrade_guids.py` compares the *actual shipped Unity package tar GUID directories*, not filenames alone. The verified baseline candidate v9 and controlled-source v12 share 160 assets. **All 160 retain their GUIDs**, with no changed or removed asset identities. Earlier independently generated v8 versus v9 releases had 48 identity changes; the source-controlled metadata approach addresses that verified regression. Synthetic upgrade test fixtures verify a passing unchanged case, failure on modified GUID and failure when an old serialized reference is removed.

Source changes that enabled this outcome: author-owned Unity scene, materials and ScriptableObjects plus `.meta` records are now checked into the dedicated Games branch. The builder stages them before Unity import, verifies hashes/GUIDs during explicit staging reuse, then exports via the public Unity Editor API without regenerating identities or overwriting previous buyer customizations. Source-controlled Unity scripts themselves are original HPR code; generated buyer releases and Unity caches remain external to the Git repository.

The original ten modules passed **34/34 real Unity EditMode tests** in an isolated Unity 6000.4 project after the latest ability-state correction. The failing precursor test demonstrated that duplicate unlocked ability IDs were silently accepted; the fix adds complete prevalidation of unlocked IDs and relative cooldowns and applies one state with one final change event. In addition, the integrated host rejects invalid nested abilities **before** applying gameplay transforms, health, inventory, weapon or enemy snapshots. A separate cleanroom runtime regression was added to verify absence of partial state restoration in the actual buyer archive.

Nineteen Python source and release builder tests passed after the new source-control staging and archive upgrade regressions. The source-controlled scene and sample asset copies inside the new development project were verified unchanged before Unity export.

The previous v9 buyer candidate (before the latest ability correction and stable metadata upgrade) was independently imported and smoke-tested in both Unity 6000.4 and Unity 6000.6. Each engine reported all thirteen scene references, twelve required auxiliary assets, forty-seven runtime scripts, no changed scene assets on attempt to rebuild, and ten full cross-module smoke checks passed, including local JSON save and corruption response. The optional UI Toolkit Editor guide was directly opened inside Unity and its scrollable controls, status version and eight working action surfaces were structurally verified. These prior results do **not** automatically verify v12 and are retained as historical evidence.

Unity's official Asset Store Tools package version twelve was acquired from the official public repository, into an isolated QA directory. Unmodified upstream tool code failed to compile under Unity six point six due to removed APIs and also had one legacy exporter symbol error under Unity six point four. A **disposable test-project-only** compatibility edit changed its exporter helper from the unresolved `GUID.Generate()` call to standard `System.Guid.NewGuid()`. No official validation tests, category severity rules, result mapping or checks were modified. That adapted copy ran **34 official Unity Asset Store Validator tests, with zero failures and zero warnings**, against v9. It is a meaningful guideline preflight but not stock-tool validation of v12, a Unity reviewer decision or commercial approval.

## Open validation

The exact v12 fresh Unity six point six cleanroom workflow was launched separately; its scene and runtime receipts were still pending when this ledger was initially written. The `qa/validate_existing_game_upgrade.py` script exists to import v12 into a copy of an already populated existing Unity game, check that unrelated customer-owned scripts/data are bit-for-bit unchanged, and run scene/runtime validation. This upgrade test must be executed before claiming full non-invasive integration. Only run inside unused disposable `/data/tmp` paths.

A second disposable Unity six point six project enables URP version 17.6 and Unity Input System version 1.20, with new-input-only active handling; the package manager locked and compiled those optional packages. Its native shader and asset import remains expensive and the end-to-end URP scene/material acceptance receipt is still open. Do not claim URP or new-only input success merely from compilation or source inspection.

Fast Enter Play Mode/domain reload off was previously verified in Unity six point four; must be rerun independently in Unity six point six before claiming that newer requirement. Store image captures for prior versions exist; actual v12 visuals and feedback across normal/small Editor panels have not received independent professional buyer usability tests.

Unity's publisher login and support/submission access remain unresolved. Previous separate nine submissions were explicitly rejected in October. The consolidated product has **never been submitted**. Claims of uniqueness or convincing willingness to pay remain unproven: the code tool overlaps mature alternatives including TopDown Engine, Game Creator 2, Ability System Kit and others. This quality work does not authorize publishing an undifferentiated product.

## Safe next sequence

Complete v12 cleanroom; investigate any actual failing assertion; verify opt-in URP and alternate input; execute upgrade-into-existing-game acceptance without editing original donor; use official Asset Store tools when an upstream-compatible version is available; capture buyer demo/Editor guide screenshots from the tested imported package; commit and push only source and documentation changes after tests, keeping generated artifacts outside Git. Any account login challenge, identity check or live publisher submission requires proper existing-account authorization and server-side verification. Do not create another publisher account.

The owner-approved Infra repository guidelines remain authoritative. All Unity implementation changes belong in the dedicated `product/unity-integrated-suite-20261030` branch; the unrelated Games main checkout and other agents' uncommitted work are never reset or overwritten.

## November 1, 2026 — v14 controlled release and real Linux input test

The newer controlled candidate in
`/data/var/marketplace-account-setup/unity-consolidated-20261101-v14/release/`
was generated on Nitro with Unity 6000.6.7f1. SHA-256 of its exact internal
buyer archive is
`830a6ccfd264e1e46a4a9f7f97d6fc04b3b7d51dc44d48d0b706887460c82ee7`
(100,003 bytes). It is **internal QA only, NOT submitted, approved or published**.
The static archive verification counted 160 Unity assets, ten runtime modules,
no non-suite paths, no shipped NUnit assemblies, all 52 authored GUIDs unchanged,
and the original 22 Unity YAML source files bit-for-bit preserved. Actual
archive-to-archive upgrade comparison against v13 found 160 shared assets with
zero changed or removed GUIDs. The source-level Python suite passed 21 tests.
No C# source warnings were detected in the Unity 6.6 build log.

The independent Unity 6.6 **new blank project** importer verified 13 serialized
demo-scene references, 12 required sample/docs elements, all 47 original
runtime module scripts, and a read-only/no-overwrite scene-builder safeguard.
The same actual imported archive passed ten runtime checks: service registry,
world metadata, keyed doors and pickups, combat/event-bus health, healing and
area pulse, weapon cooldown/loot, memory checkpoint, real JSON disk write/read,
corrupted-save rejection, and valid near-wall player checkpoint.
A separate *actual Play Mode* run on the imported package also passed scene
initialization, collision-aware CharacterController movement, enemy chase,
typed damage, ability/stamina execution, weapon mechanics and restoration.
See `cleanroom-*.unity.log`, exact scene/runtime QA receipts and
`actual-playmode-receipt.txt` in the v14 release directory.

The standalone Unity 6.6 **Linux player**, independently built from the same
`HprSuiteInput.cs` source SHA as the v14 manifest, passed actual dynamic
input-update frames with the optional Unity Input System 1.20.1 and
new-input-only handling. Verified keyboard press, the first-frame
`WasPressed` transition, held/released keys, left control, arrow and numpad
key translations. Receipt:
`/data/var/marketplace-account-setup/unity-suite-quality-research-20261101/linux-new-input-player-result.txt`.
This resolves the previous unreliable **headless Editor** simulation result;
a failing Editor callback is not evidence of a runtime defect.

**Still open at this writing:** v14 first-party Unity Asset Store Validator
in a disposable Unity 6000.4 project with a documented *exporter-only*
compatibility shim (the independent validator tests themselves are unmodified);
Unity 6000.4 v14 cleanroom; disabled-domain-reload 6000.6 on exact v14;
URP 17.6 material conversion and end-to-end input in the exact v14 archive,
and optional official `InputTestFixture` Play Mode tests. The original
publisher account remains unverified, no new product has been submitted,
and direct competitive advantage over existing frameworks is not proven.

Unity official documentation now recommends UPM for long-lived reusable
**code** packages over one-time-import `.unitypackage` where dependency and
version management matter. An explicitly researched, *unsubmitted* UPM
migration option is documented separately in
`package-format-decision-2026-11-01.md`. Do not change shipping format
without real buyer-upgrade tests and original publisher eligibility.

## Verification follow-up, November 1: both Unity versions and official Input System

The exact v14 artifact is now independently verified in **Unity 6000.4.0f1
and 6000.6.7f1**. Both fresh projects imported the archive and validated
thirteen serialized scene references, twelve required auxiliary assets,
all forty-seven original C# scripts and non-destructive sample rebuild
protection. Both independently ran the ten integrated gameplay checks and
produced a `CLEANROOM_VERIFIED` result. The 6.6 imported scene additionally
passed real Play Mode movement, autonomous enemy pursuit, EventBus damage,
ability activation, weapons and checkpoint restore. All receipts and Editor
logs remain next to the versioned archives outside Git.

The exact same v14 archive passed the Unity Asset Store Tools v12.0.0
validator in a **disposable Unity 6000.4 project**: 34 tests, zero failures,
zero warnings, no C# compilation errors. Only a separate, documented
exporter compatibility adjustment to official tooling was present; validator
test logic/severity code remained unchanged. This does not imply publication
approval or any access to the original publisher account.

Unity's supported `InputTestFixture` Play Mode tests were introduced in a
separate private project with Input System 1.20.1 and Test Framework 1.8.0.
The three tests passed with no failures: first-frame button transitions and
held/released states; alpha/arrow/modifier/numpad mappings; and pointer
position from a virtual mouse. The same production input adapter was already
verified in an actual standalone Linux Unity 6.6 player under
new-input-only settings; its source SHA matches the v14 source manifest.
Earlier headless Editor experiments that gave incorrect frame-transition
evidence were archived outside Git with hashes and logs; only the supported
passing test harnesses remain in the developer QA source tree.

Current separate work (not yet complete at this evidence point): v14 exact
URP/new-input buyer package import and material compatibility; v14 exact
two-entry domain-reload-disabled Play Mode check; refreshed v14 upgrade test
into a populated game project. Commercial differentiation, publisher login
and server-side submission are still unverified.
