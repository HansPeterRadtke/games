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
