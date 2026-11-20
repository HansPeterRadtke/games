# Existing-game ability integration: source comparison and acceptance correction

Research date: November 3, 2026. Scope: the owner-authorized Unity work resumption,
actual pinned HPR buyer archive, current customer-test source, original ABC
integration documentation, Unity 6.6 sample guidance, and a pinned legal Flexi
package source. No production C# change, product purchase, marketplace operation,
new Unity Editor launch, human test, or comparative performance measurement.

## Decision and what changed

**Commercial NO-GO remains.** The new result is a more specific, source-verified
reason and a cheaper falsification route, not another feature roadmap. Prior
research already established crowded supply and the free PackageLens comparator;
repeating those findings would not constitute a new milestone.

The existing customer healing proof verifies HPR's runtime behavior and retention
of a pre-existing controller. It does **not** establish that the selected-object
installer connects the customer's independently existing health and input systems.
Those are separate integration boundaries. Do not turn a direct test-code API
call and an independent QA health store into a zero-code customer integration
claim. Preserve the earlier real Unity passes with their original narrow scope.

A new source-level free comparator is now available without a paid purchase:
**PhysaliaStudio/Flexi 0.14.1**, revision
`51da089e62d7b9bea03ddd7fa087078ecef2254d`. Its package-specific MIT notice was
read and retained. Only the own-package subtree, root license and README were
checked out for review; unrelated bundled plugins and sample dependencies are
not part of this review or any claimed license grant. No competitor code is
copied into this repository or the HPR product.

## Exact HPR evidence, independently checked against the archive

Reviewed archive SHA-256:
`1140e9bf5c7a9848003ce0ccd8168c298ced2bf957194364f9f08b3f52974f5e`.
This is the reviewed private package, not the dirty commercial source worktree.
Fourteen read-only source/archive assertions passed, with exact source hashes
and the full Flexi package inventory retained in private QA evidence.
These are structural source checks, not gameplay or usability tests.

| Buyer boundary | Verified evidence | Honest interpretation |
| --- | --- | --- |
| Original controller | Prior real Unity tests retain the controller and its configured speed | Retention is proven for that fixture; original health/input integration is a separate question |
| Authoritative health | `qa/HprCustomerAbilityResourceBridge.cs` stores its own serialized health and stamina fields; `Heal` changes that local state | The bridge is a self-contained QA resource component, not a demonstrated adapter to an independent pre-existing customer health system |
| Activation | `qa/HprCustomerAbilityPlaymodeValidator.cs` calls `runner.TryActivate(asset.Id)` directly and reads the QA bridge | Real Play-mode API activation is useful evidence; the test does not drive an existing input action or UI gesture |
| Installer scope | Packaged `Editor/HprSelectedAbilityInstaller.cs` requires an `IAbilityResourcePool` on the same scene object and configures the runner's serialized references | The customer still needs a compatible provider. An ordinary unrelated health component is not automatically adapted |
| Native Stats path | The newer native pool supports HPR ActorStats, as recorded in the existing adapter study | This integrates HPR's own stats. It is not universal external-health compatibility |
| Delivery footprint | Exact archive has 55 C# files and 10 runtime asmdefs; dependency traversal for Abilities reaches Stats and Eventbus, with 17 runtime scripts in that closure | Selecting one runtime feature is different from importing a minimal package subset. Do not claim three-module delivery from the present full archive |
| Persistence and removal | Earlier scene/reopen and Undo/Redo fixtures have genuine passes on their recorded candidates | They do not prove arbitrary customer save-system persistence or safe full package uninstall |

Internal source references are relative to `unity/tools/release/gameplay_suite/`,
except runtime contracts under `unity/packages/com.hpr.abilities/Runtime/`.
The reviewed archive's source was read without extracting or rewriting it.

## Competitor evidence beyond store descriptions

**ABC directly documents a customer-health integration seam.** The vendor's
[API and integration guide](https://dicelockstudio.gitbook.io/abc-toolkit/introduction/api-and-integration-with-abc)
shows overriding health access and adjustment to delegate to an existing
controller's stats, in a separate partial-class source file intended to survive
updates. It also documents effect subscribers connected to customer methods
through Unity Events. This is a concrete documented alternative to HPR's
resource-interface adapter, not just a general compatibility slogan. We have
not compiled or installed ABC, verified its partial-class assembly placement,
or independently tested update safety. Do not assume the vendor example's
integer casts, clamping, death semantics or save behavior fit every game.

**Flexi supplies another source-first integration architecture for free.** Its
[pinned package manifest](https://github.com/PhysaliaStudio/Flexi/blob/51da089e62d7b9bea03ddd7fa087078ecef2254d/Packages/studio.physalia.flexi/package.json)
identifies version 0.14.1, minimum Unity 2021.3 and a real dependency on
`com.unity.nuget.newtonsoft-json` 3.0.2. The repository's project-version record
is Unity 6000.3.9f1; that does not certify 6000.6. Own-package inventory contains
118 runtime, 32 Editor and 58 test C# files. Counts describe footprint, not code
quality, successful tests, product completeness or user productivity.

The [typed process-node source](https://github.com/PhysaliaStudio/Flexi/blob/51da089e62d7b9bea03ddd7fa087078ecef2254d/Packages/studio.physalia.flexi/Runtime/Graph/Nodes/ProcessNode.cs)
exposes `ProcessNode<TContainer>` over a game-defined `AbilityContainer`; the
[core](https://github.com/PhysaliaStudio/Flexi/blob/51da089e62d7b9bea03ddd7fa087078ecef2254d/Packages/studio.physalia.flexi/Runtime/FlexiCore.cs)
uses explicit runner, event and stat-refresh resolver seams. This supplies a
source-level route to game-owned state without requiring HPR's architecture.
It still requires programmer integration. The author's README explicitly marks
work in progress, unfinished UX, samples and blackboard-list layout concerns.
It is a valid low-cost comparator to evaluate, **not a verified ready replacement**.

The older sjai013 Unity GAS repository was also inspected, but its owner archived
it in August 2022. Do not quietly use it as a current supported-Unity baseline
merely because it has many stars. Flexi's pinned own-package code is the better
new source-comparison candidate; actual Editor compatibility remains untested.

Unity's [current sample-package guidance](https://docs.unity.com/en-us/engine/6000.6/manual/packages-list/cus-pkg-lp/cus-pkg-development/cus-samples)
already provides explicit optional sample imports. Keeping customer-owned authoring
outside vendor data is therefore expected packaging practice. UPM migration stays
subject to the existing package-format decision; no format switch was made here.

## Bounded comparison task and evidence needed

Use one common pre-existing game with a separate authoritative health component,
an existing input action, visible health display and existing save/load mechanism.
Run every arm from a separate byte-identical copy. Keep the customer's original
files, HPR candidate and competitor revisions pinned. Permit new customer-owned
adapter code; count it honestly rather than forcing impossible universal
zero-code compatibility with arbitrary private APIs. Never change the benchmark
mid-run to make one implementation pass.

| Phase | Required observation | Disqualifying shortcut |
| --- | --- | --- |
| Prepare | Record baseline health, action binding, HUD, save state and original file identities | Initialize HPR-only resource state and call it the customer's existing health |
| Integrate | Configure the healing action through the documented buyer workflow; count source edits, components and manual steps | An invisible private QA script supplies a missing production adapter |
| Activate | Drive the existing player input; original health and HUD change once; cost and cooldown obey configuration | Call TryActivate directly and claim the player's input path passed |
| Reopen | Save/reopen scene and use the customer's save/load path with a defined cooldown persistence policy | Inspect only the ability asset reference and infer complete game-state restoration |
| Revise | Change the effect in a customer-owned definition, update the toolkit candidate and verify retained intent | Rebuild or overwrite the buyer's original definition to repair the test |
| Remove | Remove only the selected feature with explicit scope; controller/input remain usable and dependencies are reported | Delete the entire package or silently remove unrelated customer code |

Measure actual participant task time, corrected failures, new/edited customer
source files, component/Inspector actions, unexpected file changes and successful
completion. Include a simple hand-authored existing-game implementation as the
no-package counterfactual, with equivalent cost/cooldown/configuration semantics;
otherwise a trivial one-effect task can misleadingly favor any framework demo.
HPR, Flexi and ABC comparative times and outcomes are all **NOT MEASURED**.
Only add a priced positioning claim after real buyer behavior and a fair task
comparison establish a benefit. No invented developer participants or sales.

## Next engineering work, constrained by these findings

The next useful QA fixture must observe the existing game's input-to-authoritative-
health path and its persisted state. Prioritize that over adding more generic
modules, rebuilding broad validators or rewriting the demo UI. Start with a
failing end-to-end acceptance case; use a separate customer-owned adapter if
needed and record its full integration burden. Do not replace the existing
controller or introduce a second health store to make the test pass. Preserve
any currently failing/unsupported outcome rather than lowering the contract.

Before a new Editor run, inspect current source/other agents and resource-broker
admission. The live refreshed Nitro observation in this session showed all eight
logical CPUs busy and CPU pressure around 78 percent; no new Editor or competitor
runtime process was launched. That is a session observation, not an eternal ban
on testing. The new source audit does not upgrade the latest candidate's Editor
release status. Publishing still requires separate owner authorization.

## Evidence storage and verification

Private source receipt, original worktree baselines and the sparse competitor
reference are outside Git under the existing marketplace QA runtime area,
`unity-buyer-workflow-research-20261103-resumption`. This report is checked into
an isolated research worktree based on the latest QA commit. The fourteen dirty
commercial files, five dirty buyer-copy QA files and two dirty customer-integrity
QA files were hashed before changes and are checked again before completion.
No raw competitor source, downloaded books, runtime logs or credentials are
included in this commit. No production source changed during this research pass.
