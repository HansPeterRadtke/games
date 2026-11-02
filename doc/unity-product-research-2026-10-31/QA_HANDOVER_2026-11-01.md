# HPR Unity commercial-product QA handover — November 1, 2026

**Decision: commercial NO-GO; significant independently verified engineering
progress.** No Asset Store publication, resubmission, alternate account,
purchase or user-account mutation occurred.

Owner source worktree: `/data/src/worktrees/unity-integrated-suite-20261030`,
branch `product/unity-integrated-suite-20261030`. It had **fourteen**
owner/other-agent uncommitted files throughout our checks. **No files in
that worktree were modified in this QA session.** In particular, the
latest uncommitted source guide and product docs are **not** the same
bytes as the last verified buyer v14 package.

Independent owned Git QA branch:
`qa/unity-customer-integrity-20261101`, worktree
`/data/src/worktrees/unity-customer-integrity-20261101`.
QA source/docs were tested, committed and pushed to GitHub; the remote was
independently checked and the branch was clean at the last check.
Source and QA tests in this branch are **not** a new commercial archive.
The original combined product branch remains undisturbed.

## Verified actual Unity results

- **Unity 6000.6.7f1, Built-in, v14 release archive:** fresh independent
  project creation, true .unitypackage import, all thirteen serialized
  scene refs, twelve additional assets/docs, forty-seven runtime source
  scripts and ten integration/snapshot/runtime tests passed.
- **Existing customer upgrade, v13 to v14:** preexisting custom C# player,
  scene, prefab, serialized ScriptableObject settings, Unity project
  input/graphics settings and manifest protected; all original twenty-one
  test-snapshot files preserved byte-for-byte; actual Unity Editor
  successfully reloaded the customer scene and configuration.
- **Uninstall from nondependent customer game:** Unity Editor removed HPR;
  original twenty-one customer files preserved; subsequent fresh Unity
  compile and scene/controller/prefab/Editor-setting check passed.
  Uninstall safety for an app that *actually depends* on HPR interfaces
  remains unsupported and requires user-controlled migration.
- **Disabled C# domain reload:** two actual Unity 6.6 Play mode entries,
  fresh runtime state and no duplicate typed combat subscribers passed.
- **Latest uncommitted customer-copy source frozen into scratch v14:** real
  Unity **6.6** and **6.4** separate tests passed. Created buyer-owned
  ability/weapon copies, independently cloned effect, distinct GUID/runtime
  identifiers, safe occupied-path/root/path traversal rejection, original
  vendor asset bytes preserved. The actual Unity 6.4 copy test emitted
  zero C# errors, warnings or obsolete messages. These test successful
  copies; **the newer code has not yet been packaged in a new saleable archive**.
- **Actual customer healing integration:** separate customer controller,
  prefab, scene and custom settings were preserved, one new custom ability
  and its effect cloned to buyer-owned assets, explicit Inspector
  `unlockAllConfiguredAbilities` set through `SerializedObject`, a new
  authored scene saved and reopened. The fresh corrected Editor builder
  passed without a recovery. A complete before/after SHA-256 scan preserved
  all **forty-nine** prior non-vendor asset/ProjectSettings/Packages files
  and identified exactly ten expected new demo and private QA files.
  Fresh actual Play mode restored twenty health, spent twenty stamina,
  blocked a duplicate cast via cooldown, and retained the old controller.
  The **fifty-nine** post-build protected files remained byte-identical
  after Play mode.
- **URP plus modern new-only Input System in the same Unity 6.6 Editor:**
  actual URP 17.6 and Input System 1.20.1 (new-only), imported arena
  camera and virtual keyboard presses/modifiers/releases in real game
  update passed when the **private headless Editor** test explicitly
  routed test input to an unfocused Game View. Five original game scene
  and project-setting files remained unchanged. Initial failed runs
  are intentionally preserved.

Machine-readable actual receipts, evidence, logs and disposable Unity
projects are under **Nitro**
`/data/tmp/hpr-caltask33-20261101-0903`.
No original user files, private credentials, or large Unity caches were
committed to Git. This private scratch directory may be transient and
should not be mistaken for an installed or published customer product.

## Reproduced negative findings, now gated

**Most important release blocker: GUID metadata overwrite in the new
source asset-copy feature.** A new destination with an existing orphan
`.meta` but no matching `.asset` was overwritten by the uncommitted
guide's copy operation. A real Unity 6.6 negative test proved the
preexisting GUID changed. A separately compiled **two-extra-check
guard** in frozen scratch source rejected the same operation and preserved
the GUID and file, with an actual real-Editor positive receipt. The minimal
reviewable patch, not yet applied to the owner's dirty source, is
`patches/hpr-guide-reject-orphan-meta-2026-11-01.patch`.
The QA fixture and detailed receipts are in
`orphan-meta-safety-2026-11-01.md`.

**Actual failed new-customer authoring** revealed an initial unlock
persistence bug in the private QA builder: calling runtime
`SetUnlockedAbilityIds` did not serialize the Inspector default; the
saved scene reopened with `unlockAllConfiguredAbilities: 0`. Its
negative log and exact failed scene were preserved, then a targeted
separate repair was validated; the corrected fresh builder and new Play
mode test both passed. Details:
`customer-healing-integration-experiment-2026-11-01.md`.

**Combined URP/input QA initial failures:** duplicate private input probe
class generated `CS0101/CS0111`, fixed only by removing our redundant
QA source; next run had no keyboard updates because Game View was not
focused in headless Unity Editor. The native diagnostic confirmed
`Application.isFocused=false` and default keyboard focus routing.
Only the **private** QA probe was changed to route virtual test input
to the game and restore its prior input settings on destruction; final
Unity acceptance passed. Details in
`combined-urp-new-input-2026-11-01.md` and first-party Unity input
documentation linked there. This is not a promise that all physical
keyboard/Android/new-input settings are tested.

**Unity Editor Search indexer exception**:
`UnityEditor.Search.SearchDatabase` threw
`ArgumentOutOfRangeException` in several real Play mode logs even when
gameplay and package checks passed. It was absent in separate cleanroom
creation/import/compilation runs; **package-free Play mode reproduction
has not been performed**. Do not attribute this conclusively to HPR or
claim the Editor logs are fully clean.

## Commercial gates still open

The last researched verdict correctly rejects generic marketing as a
ten-module gameplay framework. A free import-review competitor already
covers conflict preflight, and mature competing frameworks have far more
functionality/reviews. The only demonstrated narrower hypothesis is
**adding a functioning customer-owned healing ability to an existing game
non-destructively**. This was a developer-authored QA fixture, not a
prospective-buyer study or paid-user workflow.

Before proposing any Unity Asset Store release:

1. First reconcile only the **verified metadata patch** and the other
   agent's dirty guide changes with that worktree's owner. Do not
   overwrite the owner's files or claim our independent branch has been
   merged.
2. Build an immutable **new** Unity buyer package from the reconciled
   source in a fresh release path. Run all cleanroom compilation, input,
   pipeline, GUID and upgrade tests against that **exact archive**,
   then actual customer-install/undo/uninstall behavior including a game
   that uses HPR in earnest. Do not reuse v14 receipts as new release proof.
3. Provide a customer-facing Inspector workflow, useful validation,
   opt-in effects and explicit Undo/rollback. The current helper QA
   manually adds a bridge and calls Editor methods, not a fully
   guided commercial feature.
4. Compare task completion time/errors/source edits using real
   experienced developers and actual relevant competitor products.
   Test first-use on pre-populated customer games with their own
   input/controller/save setup. No such human market proof exists.
5. Verify cross-version/pipeline/input matrix, genuine demo appearance,
   user-controlled buyer assets, AI assistance disclosure and actual
   account verification before submission. No store/public side effects
   are authorized by this QA checkpoint.

**Current commercial status: NO-GO. Current engineering status: PARTIAL,
with real reproduced and corrected QA problems.**

Applied owner-wide rule: stage/commit/push only independently owned
tested files, protect source/GUIDs and secrets, preserve negative results,
and distinguish actual Unity process receipts from source-only tests.
The owner Infra and relevant guideline documents were consulted; a full
semantic reading of **every** Infra file has not been independently
verified in this session, and no claim to that effect is made.


## November 1 evening internal selected-installer archive — latest independently verified state

A newer experimental, nonpublished Unity Editor product archive has been
frozen from the existing committed source plus the four observed buyer-source
working-file overlays and the independently verified orphan-Unity-metadata
safety patch. This **is not** a merge, overwrite or approval of the owner’s
fourteen concurrent dirty files. An isolated selected-ability Editor
installer was added as **one new optional Editor script**, with its own
stable GUID, owner-oriented menu/UI and explicit Undo/Redo source/Inspector
operations. An independently verified source-only patch and all relevant
receipts live on this QA branch. The exact archive and its frozen source
are also privately preserved under the Nitro internal selected-installer
QA folder in marketplace-account-setup, with explicit NOT SUBMITTED status.

**Actual finished acceptance:** the exact archive contains **161 assets**;
all **160 previous GUIDs** survived unchanged, with no removals. Unity
6.6 actual cleanroom import passed thirteen scene references and ten
independent runtime/save integration checks. Unity 6.6 imported the new
archive into a real populated customer fixture and preserved all
**59 original files**. The **actual installed Editor script** (not an
overlay) passed read-only preflight, selected-object attach, Undo and Redo,
Inspector serialization after save/reopen, and UI Toolkit control checks.
The user-controlled test created only a new scene and private QA files.
Unity 6.4 independently imported the same archive and preserved **27**
pre-existing files. Unity 6.6 double Play-mode entry with domain reload
disabled passed without duplicate gameplay subscriptions. The combined
Python source/integrity suite passed **37** checks. These positive
results are grounded in real Unity process exit codes and logs, not
synthetic claims of complete product readiness.

**One distinct technical failure remains:** the selected-installer
archive's Unity 6.6 URP 17.6 with new-input-only *import* timed out after
600 seconds while Unity ILPP/Bee was compiling the older cloned test
project **before** the new installer file was imported. The process exit
was **124**, no HPR C# compiler error was observed, and all **60**
original customer files remained byte-identical. This is explicitly
recorded as FAILED/INCOMPLETE in
[selected URP test](selected-urp-new-input-timeout-2026-11-01.md).
The previous v14 URP test passed, and all **80** runtime/demo/material
asset bytes are unchanged in the new archive, but **these are not
substitutes for an exact new-archive URP test**. Do not blindly retry
against the uncertain copied Unity Library; use a new project in any
separately authorized follow-up.

**Release decision: COMMERCIAL NO-GO.** No independent expert buyer trials,
comparative measured development-time benefit, willingness to purchase,
fully verified render pipeline/input matrix, user visual QA, publisher
verification or Asset Store approval is established. No outside uploads,
paid services, trades, publisher submissions or new Calendar events
occurred. The owner’s original product worktree was not modified.


## November 1 evening follow-up — CPU-saturated URP test and reversible customer detach

The second independent URP attempt used a new Unity six point six project
with a CLEAN missing Library cache, official URP 17.6 / modern Input
System 1.20.1 manifest and matching renderer settings, but NO HPR source.
Unity reached Bee/ILPP postprocessing and timed out before extracting the
frozen internal package. Thirty-five pre-existing renderer/ProjectSettings/
Packages files stayed unchanged. Nitro had eight CPU cores available,
very high runnable load and sustained ten-second CPU pressure around
eighty percent or higher. CPU contention is a measured important factor,
not a proven complete Unity root cause. A new private resource preflight
would now advise deferral and cannot interrupt other workloads.

A second real Unity six point six Editor test exercised the installed
selected-ability window's DYNAMIC controls: valid/invalid ObjectField
values, button enablement, actionable messages and read-only preview.
Seven checks passed with sixty-four prior customer files preserved.

A separate, intentionally NOT packaged customer-detach QA prototype
now provides explicit, confirmed removal of ONE HPR AbilityRunner
component with public Unity Undo/Redo while retaining customer
controllers, resource providers, prefabs, ability definitions and project
settings. Eight real Unity Editor checks passed, including Undo restoration,
Redo removal and separately saved new scene. Sixty-four original customer
files remained unchanged. This is a reviewed patch against the prior
immutable installer-enabled archive, NOT a claim that it is shipped or
safe for automatically uninstalling all HPR dependencies.

All details, negative evidence, correct per-file baselines, pending
human visual UX and market gates are in
[the late continuation report](late-unity-qa-continuation-2026-11-01.md).
**Commercial status remains NO-GO.**


## November 1 final buyer-owned uninstall dependency audit

The prior passing HPR uninstall scenario did not represent a real customer
game that still uses HPR. A new independent READ-ONLY preflight now checks
buyer-owned Unity scene/prefab/asset YAML references against the actual
archived vendor asset GUIDs, plus HPR namespaces in customer C# source,
assembly references and package manifests including their resolved locks.
Seventeen deterministic tests first reproduced missing/incorrect
implementation, then passed, including
a genuine Unity package vendor-root GUID case. Its real archived source
scan detected TEN HPR references in the previously tested buyer project:
HPR runner scripts in serialized customer scenes, HPR ScriptableObject
assets and customer/QA C# references. A controlled orphan-scene sample
without the HPR vendor root STILL revealed the missing HPR GUID reference.
An unrelated package-free customer scene produced no direct HPR references.
The preflight explicitly never authorizes deletion in any case.

This narrows an important product gap: ability **component** detach with
Undo is verified in a customer scene, but dependency-aware HPR package
uninstall/migration is NOT. A customer with HPR dependent scenes or code
must be warned and offered a reviewed migration before removal. See
[safe uninstall audit](safe-uninstall-dependency-audit-2026-11-01.md).
The commercial conclusion remains NO-GO.


## Commercial seller-draft verification

The owner/other-agent's latest private Unity Asset Store listing was
inspected read-only against source/asset provenance and actual Unity
Editor logs. A separate [listing-claim audit](listing-claim-verification-2026-11-01.md)
identifies which source/demo claims are technically supported, and why
URP compatibility of the NEW archive, no-code ability setup, in-package
reversible detach, safe dependent-game uninstall, completed visual
Editor QA and justified price **must not be claimed**. The proposed
seller text was NOT changed or published. Commercial status NO-GO.


## November 2 reproducible source-only detach proposal

The previously tested reversible selected-object installer source was
applied to a separate copy of the exact frozen internal seller-package
source, not to the published/candidate package binary or other agent's
product worktree. The copy contains exactly four edited files: one Editor
C# script and three explicit buyer documents. A new read-only verifier
reported **1,093** identical source-tree paths, **516** unchanged Unity
.meta GUID files, four permitted changes, and only two originally
present unrelated absolute helper-project symlinks. None were followed.
The actual game-suite release subtree is free of those external links;
the wider old helper-project tree is not entirely hermetic.

A standalone offline .NET eight C# compile referencing Unity six point
six API assemblies, all 47 real HPR runtime C# files and the new selected
Editor prototype passed with zero errors and three expected standalone
serializer-field warnings. This is NOT a real Unity Editor compile
or a new package-import acceptance. The exact previously frozen
161-asset archive remains unmodified and no release is authorized.

The existing broker-supervised Unity URP/new-only-input retry job is
running independently and waiting for actual CPU capacity. Its updated
process-group cleanup tests prevent timed-out Unity/Bee descendants from
continuing as orphaned workloads; the previous idle broker job and its
receipts were preserved. No other owner's resource-consuming processes
were stopped or preempted. Full findings:
[selected detach source-only provenance](selected-detach-source-provenance-2026-11-02.md).

**Commercial decision remains NO-GO**: real developer demand, final
accessibility/media QA, dependent-game migration and complete Unity
URP/Input matrix are still unverified.


## November 2 customer asset-copy side-effect research

The exact frozen private seller archive's integration guide calls
Unity AssetDatabase.SaveAssets after cloning customer ScriptableObjects.
Unity's documented API writes **all unsaved assets** in the current
project, potentially committing unrelated buyer Inspector edits. A new
private **source-only** guide patch saves only specifically created
clones with SaveAssetIfDirty, and explicitly discloses that this
method bypasses OnWillSaveAssets VCS callbacks. All previous source
GUID identities and the immutable archived buyer package remain
unchanged. Three new Python contracts passed, and an offline Unity six
API C# compile passed with zero errors and three serialized-field
warnings. A real Unity Editor fixture with a deliberately unsaved
unrelated buyer ability is staged with a sixty-four-file baseline but
**has not yet been run**, because CPU pressure and the independently
registered broker-managed URP job remain high. Full detail:
[scoped sample saving](scoped-sample-save-2026-11-02.md).

This does not change the **commercial NO-GO** verdict or authorize
publisher submissions, purchases, account changes or overwriting the
other agent's product worktree.


## November 2 native HPR Stats resource persistence gap

A source audit identified another genuine buyer integration blocker:
the HPR training arena calls HprSuiteAbilityPool.Bind(stats) at runtime,
but that adapter stores the Stats source in a NON-SERIALIZED field.
Manually configuring its component in an existing customer scene leaves
Health and Stamina at zero unless the buyer authors a custom runtime Bind.
The selected-object Editor preflight previously checked only that the
provider implemented IAbilityResourcePool and therefore could accept
an unconnected native pool.

A separately staged source-only correction now serializes the native
ActorStatsComponent reference and lazily resolves the same-object Stats
when manually installed. Cross-object Stats binding is explicitly
refused, and the installer warns when native HPR Stats are absent.
Existing custom third-party health systems still require a separate
user-authored adapter: **no generic no-code claim is made**. Four
independent source contracts passed. A low-priority offline C# API
compiler including all 47 HPR runtime sources, the corrected Editor
code, an actual buyer controller source and private Editor QA fixture
passed with zero errors and three serialized-field warnings. A separate
low-priority offline compile of the same native/Editor/customer QA sources
against installed Unity 6000.4.0f1 managed API assemblies also passed
with zero errors and three serialized-field warnings. Neither offline
compiler run proves real Unity Editor import/Play mode compatibility.

A representative populated customer game with sixty-four original
nonvendor Assets/ProjectSettings/Packages files protected has been
prepared for a real Unity six point six scene save/reopen and healing
Play-mode test, but the Editor process has NOT run under current Nitro
CPU congestion. The source-only revision preserves 1,093 source files
and all 516 pre-existing GUID metadata identities. The original
compiled buyer archive and owner dirty product source remain untouched.
Details: [native Stats integration](native-stats-buyer-resource-2026-11-02.md).

The buyer product remains **commercial NO-GO**.


## November 2 late-morning seller-readiness QA and remaining blockers

The owner-loaded independent commercial candidate remains a frozen
161-asset internal Unity package, **not an approved saleable product**.
A cumulative source verifier compared all **1,093** frozen source-tree
entries and all **516 Unity .meta GUID identities** against a separate
native-Stats/reversible-detach/scoped-save source-only proposal. Exactly
SIX intended files differ: three Editor/runtime C# files and three
explicitly revised buyer documents. The verifier disclosed two
pre-existing unrelated external helper-project symlinks and verified
no new source paths, metadata/GUID changes, or unexpected source edits.

New official Asset Store competitor supply research found that Ability
& Combat Toolkit already advertises numerous abilities and a
configurable controller, while Game Creator 2 has extensive visual
authoring and an installed paid audience. Current official product
listings are NOT sales numbers. A directly comparative experienced
buyer task is still missing: do not market HPR as unique/no-code.

The genuine previous Unity 6.6 URP camera-capture log was inspected,
with both HPR_MEDIA_SAVED events, actual output hashes, a completed
camera-render PASS event and process exit zero. An objective image-QA
gate independently rejected the original black v14 URP arena render
and passed both corrected 1600x900 arena/encounter captures as distinct
non-black images. This is not subjective composition approval and not
proof of a new exact-archive capture.

A second key-art QA gate found the historical 1600x900 file named
store cover does NOT meet the official historical 1950x1300 cover key
image format. Dedicated card, icon and social artwork was absent from
that inspected gallery. Correct-size truthful marketing images, visual
quality review and a live publisher portal requirements check remain
required before sale. No new art was fabricated or uploaded.

An independently staged serial customer Unity acceptance worker has
now passed its read-only upstream/CPU/permission/secure-broker mock
contracts and strict source/customer-file prechecks. It is intended
to run native HPR Stats Editor save+Play mode and unrelated dirty
asset-copy tests only AFTER the existing URP broker job has a genuine
terminal outcome and CPU is available. A separate synthetic
child-process integration test invocation was REJECTED by platform
safety controls, preserved privately, NOT rerun or circumvented.
Consequently the new follower was NOT activated and the actual Unity
Editor checks remain **outstanding**. The previously activated
URP broker worker is still separately monitored.

A final independent batch of permitted regressions ran successfully:
**120 Python tests passed**. No source was merged into the concurrently
dirty owner product worktree, whose fourteen pre-existing uncommitted
changes remain intact. All details and negative evidence are linked
through the research README and private Nitro QA receipts.

**Commercial release decision remains NO-GO**, irrespective of these
valid engineering QA advances.


## November 2 private seven-source QA archive and demo-material save isolation

An additional source audit identified two global SaveAssets invocations
in the packaged opt-in HPR demo-material adapter and internal scene builder.
These could flush unrelated buyer Inspector edits. A separate source-only
patch now saves only HPR-owned authored sample assets and explicitly
retargeted HPR sample materials through SaveAssetIfDirty. Its documented
tradeoff is bypassing OnWillSaveAssets VCS callbacks. Three new source
contracts passed, and a genuine disposable buyer project was staged with
sixty-four protected original customer files to test the actual Unity
Editor behaviour. This real Editor test HAS NOT yet been run.

A deterministic create-only repacker built a NEW PRIVATE 161-asset
Unity tar-format QA candidate from the previously frozen 161-asset
selected-installer binary. It replaces exactly seven previously reviewed
HPR script/document payloads while preserving all original GUID .meta,
pathnames, 10 assembly definitions and every other asset byte. Ten
first-test synthetic packaging regressions passed, and an independent
existing archive GUID upgrade tool found all 161 GUIDs unchanged. A
second archive-policy audit found no issues; the maximum asset path
length remained ninety bytes. A second independent real-source rebuild
produced a byte-identical candidate. This is NOT a native Unity Editor
export, a passed Unity import, or a publication.

The proposed C# source and all 47 original HPR runtime scripts also
passed separate low-priority offline API compilations against installed
Unity 6000.6.7f1 and 6000.4.0f1 managed assemblies, and a distinct
Unity 6000.6 build with ENABLE_INPUT_SYSTEM defined and the actual
Unity Input System reference. All returned zero compiler errors;
serialized-field warnings remain a standalone-compiler caveat. None
of these compilations proves real Unity Editor import/Play mode, URP,
or the fully packaged customer workflows. Logs and private build receipts
were preserved.

The earlier genuine v14 Unity Store validator had thirty-four passes
and zero failures, but DOES NOT verify the new candidate. The new
full Unity cleanroom, URP/new-only input, custom controller save/reload,
scoped-saver Editor tests, and publisher marketing key images remain
open. The owner QA branch is independent from the fourteen dirty
commercial product files. Full record:
[seven-source private archive](seven-source-private-archive-2026-11-02.md).

Commercial conclusion remains NO-GO, with no publisher submission.
