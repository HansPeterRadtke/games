# Existing-game input/health native acceptance experiment — November 3 afternoon

## Final native milestone — PASS, bounded scope

The corrected native Unity 6000.6.7f1 run exited zero with all sixteen required
observations. A queued keyboard event reached the existing input callback once,
healed the authoritative existing vitals from 40 to 60, consumed stamina from
100 to 80, updated the HUD binding, enforced cooldown, survived subscription
reenabling, round-tripped the customer save and detached the optional feature
without disabling the original action. Scene reopening and original-scene byte
preservation passed. All 67 protected files were unchanged and all 55 packaged
C# files matched the exact reviewed archive. Domain reload was ENABLED. This is
native simulated-input/component evidence, not a physical-keyboard, rendered-GUI,
external-user, cold-restart, URP or commercial acceptance.

The successful fresh-database case and the preceding reused-cache serialization
failure used byte-identical private C# fixtures. The former scene has zero embedded
MonoScript objects and six external script references; the latter had five embedded
script objects. This is bounded reproducible evidence for rebuilding copied asset
and script databases in this QA setup, not a universal Unity bug claim. All 21
pre-existing dirty files across five original worktrees remained unchanged.

## Scope and status

This continuation implements private QA of the input-to-authoritative-health gap
identified by the morning source comparison. It does not expand the product's
module count or change the dirty commercial worktree. The game fixture is
self-authored and representative, not an external customer's game or a human
buyer study. All new runtime examples and the Editor probe remain under QA and
are absent from the reviewed buyer archive. **Commercial release remains NO-GO.**

The fixture has independent customer-owned health, stamina, InputAction, HUD data
binding and a JSON save-extension seam. An explicit optional resource adapter
delegates to the existing health object; the input adapter subscribes to the
existing action. It does not create a second health store. Their code/configuration
counts as real integration work; no arbitrary zero-code compatibility is claimed.

## Intended native contract

The validator creates an independent baseline scene and integrates only a new
scene copy through the exact packaged selected-object installer. It saves and
reopens that scene, queues native KeyboardState events, checks health/stamina,
cooldown, HUD data binding, duplicate subscription prevention, save/load and
selected-feature detach. It checks the original scene's bytes. The driver also
checks every original protected file and all 55 C# sources from the exact archive.
Native exit status and every distinct named observation are required for success.

The separate shadow scenario deliberately uses the earlier QA-only independent
health store. It is valid only if input actually reaches the runner and failure
then occurs at unchanged authoritative customer health. Earlier compile errors,
input-routing failures or scene-authoring failures are NOT passing shadow controls.
Physical keyboard input, rendered HUD appearance, cold application restart,
third-party controller compatibility, URP output and external buyer usability
remain separate unverified acceptance gates.

## Completed verification and preserved failures

Twenty-two focused deterministic tests passed: eight receipt-contract tests and
fourteen archive-policy tests. Before the receipt fix, three genuine false
positives were reproduced: duplicate PASS lines, a missing contract observation,
and a contradictory failure marker. The corrected classifier requires all sixteen
distinct named observations with exit zero and no failure file.

An intermediate 63-source offline API build passed against the installed Unity
6000.6.7f1/New Input System assemblies, with zero errors and the same fifteen
serialization-field warnings as the earlier packaged source baseline. Its initial
five SessionState.GetString default-argument errors were retained and corrected.
That compiler receipt is not proof of native workflow completion or every later
fixture revision.

The native experiments used broker-owned processes with explicit CPU/memory caps,
private copied projects, strict wall-time limits and unused output directories.
No other agent's process was stopped. One owned probe with a known scene-folder
staging defect was stopped through its own broker capability; its logs remain.

Observed native failure classes, all preserved rather than relabeled as success:

* Unity compiled a new probe against the old installed package before processing
  command-line ImportPackage. The independent archive-source check detected five
  mismatches. The driver now imports the archive before staging the new probe.
* The subsequent actual Unity archive import exited zero. Every one of its 55
  packaged C# sources later matched the pinned archive. A native gameplay probe
  entered Play mode, but its first queued-input assertion failed; it was not
  accepted as a valid shadow-health control.
* The explicit InputSystem.Update(updateType) overload is internal in installed
  Input System 1.20.1. Native compilation rejected it. The fixture now uses only
  public manual-update/focus settings and the public argument-free Update call.
  The installed manager source shows that IgnoreFocus alone is insufficient in
  the Editor without AllDeviceInputAlwaysGoesToGameView. No internal reflection
  or API patch was used.
* Timestamped scene folders initially disagreed with the actual folder creation
  name. The SaveScene failure was retained, and folder creation now uses exactly
  the same path as subsequent saves.
* A reused project cache produced a scene containing embedded MonoScript objects
  for five fixture components instead of external GUID references. The required
  save/reopen assertion failed. The original fresh-import shadow scene had six
  external script references and no embedded MonoScripts. Cached script/asset
  association is a leading explanation, not yet a proven general Unity defect.
  A bounded fresh-database experiment preserves the copied databases separately
  and rebuilds SourceAssetDB, ArtifactDB, Bee and ScriptAssemblies, retaining the
  downloaded PackageCache. Native scenario receipts determine its actual outcome.

No failure here proves the HPR product's runtime is broken: several are explicit
new private test-staging defects. Equally, fixing a fixture or importing an archive
does not prove that a customer workflow passed. No green status is inferred from
a running process, compilation alone, counts of logs, or this document.

## Reproduction and durable evidence

See the private fixture [README](../../unity/tools/release/gameplay_suite/qa/ExistingGameWorkflow/README.md)
and create-only native driver. Reuse a previously imported template only with its
successful native-import receipt and exact 55-source checks. Each scenario and
reload condition gets a new output. Do not replay existing or uncertain outputs.
The fresh-cache option preserves only this experiment's own copied caches; it
never deletes or modifies the source template's Library.

Private logs, native results, compiler failures, source hashes and original
worktree baselines remain outside Git under the marketplace QA runtime folder
`hpr-existing-input-health-20261103-wave1`. All original worktrees are checked
again before completion. No binary, downloaded package, credential, vendor source
copy, marketplace operation or account change is part of this source commit.

## November 3 second continuation: native reload matrix and negative control

The same byte-identical private fixture and exact reviewed archive completed two
new native Unity 6000.6.7f1 / Input System 1.20.1 Built-in experiments. Each used
its own newly cloned project and rebuilt copied asset/script databases. The
successful native archive-import receipt from the first continuation was reused
only after independently matching every one of the 55 packaged C# files.

| Scenario | Domain reload | Native exit | Observed result | Protected files |
| --- | --- | --- | --- | --- |
| Existing-vitals adapter (first continuation) | Enabled | 0 | All 16 named checks PASS | 67 unchanged |
| Existing-vitals adapter (second continuation) | Disabled | 0 | All 16 named checks PASS | 76 unchanged |
| Independent shadow health (second continuation) | Enabled | 3 | Input and runner reached; authoritative customer-health assertion rejected | 76 unchanged |

The second continuation's wired test took 289.7 seconds; the shadow control took
345.1 seconds. Both independently retained the exact 55 packaged C# sources.
The shadow result is a successful *test of rejection*, not a successful gameplay
integration: its native failure log reaches the queued-keyboard and packaged-runner
checks, then fails exactly at
`authoritative_existing_health_and_stamina_changed`. Compile/import/staging errors
would not satisfy this control. Both broker-owned jobs exited with no remaining
cgroup processes.

Private evidence is under
`/data/var/marketplace-account-setup/hpr-existing-input-health-20261103-wave2/`:
`wired-off/RESULT.json`, `wired-off/native-result.txt`, `shadow-on/RESULT.json`,
`shadow-on/native-failure.txt`, corresponding Unity logs and protected-file hashes.
The higher protected-file count reflects cloning the prior completed fixture
project; it is not evidence of more buyer-owned features or test coverage.

Preservation is bounded to each recorded protected-file baseline, taken after
bootstrap import and probe staging. These receipts alone do not establish that
bootstrap import preserved every nonvendor file before that baseline. The
source template and owner worktree preservation are checked separately.

## Test-first correction: preservation must include bootstrap import

Review of the matrix exposed a QA-driver defect: its original protected-file
baseline began only after native bootstrap import and fixture staging. Two new
controlled-native-boundary tests reproduced false PASS results when import
respectively overwrote or deleted an existing customer file, even though the
later gameplay receipt contained all sixteen correct observations. A third
vendor-only import control passed, isolating the defect from archive installation
itself. These are driver-level simulations, not Unity AssetDatabase tests.

The corrected driver hashes existing nonvendor Assets, Packages and ProjectSettings
before bootstrap import (after its explicitly requested reload-option changes in
the private clone), stores that baseline separately and immediately fails on any
changed or missing original before staging gameplay probes. It retains the
post-staging baseline to cover new fixtures too. All eleven focused tests passed
after the fix; both original failing traces are retained in
`import-preservation-before.log`, with the corrected run in
`import-preservation-after.log`. Earlier native receipts are not retroactively
upgraded to this stronger contract. A new native import case then completed the stronger contract successfully.

`import-guard-built-in` used a new copy of the earlier Input System template and
ran actual Unity archive import, followed by the full asynchronous Play-mode
probe, rather than reusing the first continuation's import receipt. Both native
processes exited zero. Its result records 40 original nonvendor files unchanged
across bootstrap import, 48 protected files unchanged after fixture staging, all
55 exact archived C# files and all 16 named gameplay checks. It took 430.3 seconds
with domain reload enabled in Unity 6000.6.7f1 / Input System 1.20.1 / Built-in.
The broker job exited with zero remaining cgroup processes. Evidence is retained
in `import-guard-built-in/{IMPORT_RESULT.json,RESULT.json,pre-import-protected-before.json,protected-before.json,archive-import.log,unity.log,native-result.txt}`
below the second-continuation private evidence root. This is genuine native
positive acceptance for preservation, not native fault injection of an importer;
the overwrite/deletion negative cases remain controlled-boundary Python tests.

## Official requirements rechecked November 3

The current [Unity Asset Store Submission Guidelines](https://assetstore.unity.com/publishing/submission-guidelines)
show an October 23, 2026 update. Section 2.5.h requires domain-reload-disabled
Play-mode support starting with Unity 6.6; section 2.5.i separately covers obsolete
API warnings. Sections 1.6.a and 1.6.d require useful, differentiated AI-assisted
content and transparent disclosure. Passing this narrow fixture does not satisfy
all of those requirements or approve the commercial product.

Unity's [domain-reload manual](https://docs.unity.com/en-us/engine/6000.0/manual/programming-environment/code-reload-serialization/code-reloading-editor/domain-reloading)
explains that static state and event handlers can persist across successive Play
sessions. The current matrix tests one Play session per native process and
component disable/enable within it. It does **not** prove repeated enter/exit cycles,
all static event cleanup, scene-reload-disabled combinations or a Player build.
Those limits remain explicit rather than treating one toggle test as full policy
compliance. The attempted 6000.6 documentation URL was unavailable; the cited
6000.0 manual is context, while actual behavior is measured in installed 6000.6.7f1.

## Next release gate

The Built-in wired reload-enabled/disabled cases and the specific shadow negative
control are now complete for this private fixture. Physical input, rendered UI,
cold application restart, third-party controller compatibility and independent
buyer usability remain open. A separate URP-configured project experiment is
being recorded independently; no rendered pipeline acceptance follows from a
headless gameplay test. Do not merge these private examples into the seller
package without a product decision, real compatibility proof and the original
owner-source reconciliation. Competitive differentiation and human buyer gates
remain open. Commercial release remains **NO-GO**.
