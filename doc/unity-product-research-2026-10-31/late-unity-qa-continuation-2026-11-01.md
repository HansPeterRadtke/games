# Unity product engineering QA — second November 1 continuation

Scope: buyer-oriented HPR Gameplay Systems Unity Editor integration, Nitro.
The owner product worktree remains unchanged and had fourteen other-agent
uncommitted files. New QA source is in independently owned branch
qa/unity-customer-integrity-20261101. Previous frozen candidate, actual
Unity tests and commercial verdict: see QA_HANDOVER_2026-11-01.md.

## Exact internal release URP test — still incomplete

The previous copied-project URP 17.6 and Input System 1.20.1 new-input-only
import attempt timed out after six hundred seconds inside Unity Bee/ILPP
compilation before importing the new HPR selected-installer archive.
All sixty pre-existing buyer files remained unchanged.

An independent second project was constructed on Nitro with no Library
cache, no HPR scripts and no pre-existing buyer scene. It contained only
Unity 6000.6.7f1 project settings, the official URP and Input System
package manifest/lock, renderer/volume assets, and the matching
GraphicsSettings render pipeline GUID. Thirty-five original assets,
ProjectSettings and Packages files were hashed before importing the
exact immutable selected-installer candidate from the owner's private
QA location.

The real Unity Editor again became stuck in URP Bee/ILPP postprocessing
before extracting HPR, and the bounded nine-minute Editor invocation
timed out. No HPR selected-installer source was created in the project.
All thirty-five pre-existing project and renderer files remained
byte-identical. No HPR source even existed when this failure occurred.
This demonstrates that the failure can occur without HPR and without
a previously cloned Library cache, but does not identify the precise
internal Unity compiler issue. No original or failed QA project was
reset, modified, deleted, or blindly retried.

Live Nitro samples during the affected compilation: eight CPU cores in
the process affinity, a one-minute Linux load generally around sixty
to seventy-five, and ten-second CPU some-pressure around eighty to
ninety percent. Unity process scheduling had long runnable wait periods,
and the Editor was launched at nice ten under the local execution host.
Severe CPU oversubscription is a plausible important contributor,
not independently proven as the only cause. No trading, browser,
graphics, language-model or other agent process was stopped or reprioritized.

Immutable machine evidence is stored under
/data/tmp/hpr-caltask8c-20261101/evidence, including the exact Unity
Editor log and original-file hashes. The exact new-archive URP test is
FAILED/INCOMPLETE, not a package or gameplay PASS.

## Conservative read-only CPU preflight

A new QA-only tool at
unity/tools/release/gameplay_suite/qa/unity_cpu_preflight.py reads Linux
CPU affinity, load average, and ten-second CPU some-pressure.
Its safe-threshold inputs are named and configurable. It produces an
explicit admit/defer decision and never renices, stops, reserves or
otherwise changes processes. Its results are advisory, not a broker
lease or guarantee about future CPU time.

Six deterministic tests first failed without the implementation and
passed after it was added, covering ordinary load, severe overload,
threshold boundaries, malformed kernel measurements and invalid
parameters. The complete existing QA suite had forty-three passing
Python tests after adding the six cases. The actual Nitro measurement
correctly returned defer under the current high CPU pressure.

## Real Editor interactive state behavior

A separate genuine Unity Editor 6000.6.7f1 project containing the exact
installed HPR buyer selected-ability installer tested dynamic UI Toolkit
object fields, button state, and HelpBox feedback, not just static
field presence or direct method calls.

The Editor process exited zero with seven acceptance checks passing:
missing customer ability disabled attachment; vendor-owned ability
was rejected with actionable guidance; valid independent customer
ability enabled attachment; removing the provider disabled it;
restoring the provider re-enabled it; unrelated scene selection
disabled it; reselecting the original player restored readiness;
and a read-only preview added no HPR runner.

Independent full SHA-256 protection covered sixty-four existing
nonvendor Assets, ProjectSettings and Packages files with zero changes
or removals. Only the private Editor validator's Unity .meta file
was added. No C# compiler errors or warnings were recorded.
Visual legibility in light/dark themes, keyboard navigation and
actual external developer usability remain unverified.

## Explicit scene detach prototype

The previous installer could add an ability with Unity Undo, but had
no dedicated safe detachment operation after the user later returned
to the saved project. An independently owned QA prototype now adds
a single-component remove control, read-only validation, explicit
confirmation, and Unity Undo support while retaining the original
controller, ability definitions and other customer assets.
It never deletes a user asset, silently uninstalls dependencies or
saves a buyer scene automatically. Three deterministic source contract
tests first failed without the new functions and passed after implementation.

The real Unity 6000.6.7f1 Editor then executed the privately copied source
against a representative EXISTING customer-authored scene that already had
an HPR ability runner, independent player controller and resource provider.
An explicit removal rejected prefab assets/unrelated objects; removing the
one HPR runner left the player and provider untouched; Unity Undo restored
the original runner with its serialized selected ability and provider;
Redo removed only the runner again; and the *new disposable* customer
scene retained the removed state after saving/reopening. The actual
Editor process exited ZERO with EIGHT independent PASS checks.

A separately captured full SHA-256 baseline of SIXTY-FOUR pre-existing
nonvendor customer asset, ProjectSettings and Packages files remained
byte-identical. The only THREE additions were the new disposable scene,
its Unity .meta and the private QA script .meta. Source, original customer
scenes, prefab, ability assets and GUIDs were preserved. Evidence:
customer-detach.txt, customer-detach.unity.log, detach-before.json and
detach-file-integrity.json under the unique private Nitro scratch root.

The exact independently tested feature has a reviewable source-only patch:
patches/reversible-selected-ability-detach-20261101.patch. The patch
was applied only in a PRIVATE cloned imported project and separately
checked read-only against the preserved installer-enabled archive source.
For review cleanliness it preserves the archive's original introductory
comment while the actual tested source still says QA-only; this is a
nonfunctional comment-only difference. No owner product file changed.

This detach feature is NOT in the currently immutable installer-enabled
buyer archive and has no Unity Asset Store or owner publication approval.
It improves reversibility but is not full safe package uninstall for an
arbitrary project still referencing HPR services elsewhere.

## Commercial decision

The frozen installer-enabled candidate retains prior passing Unity
six point four and six point six imports, full fresh cleanroom/runtime
QA, two domain-reload-disabled Play-mode entries, customer file
preservation, and actual attach/Undo/Redo/Inspector tests.
The exact URP import remains unverified and future expert buyer
task comparison, screenshot-level UI evaluation, commercial demand
and Unity publisher approval are absent.

Commercial status remains NO-GO. No account, publisher, trade,
purchase or external provider write was attempted.
