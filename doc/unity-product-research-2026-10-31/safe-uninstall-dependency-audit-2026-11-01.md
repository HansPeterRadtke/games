# Buyer-owned Unity HPR dependencies — read-only safe-uninstall preflight

Date: November 1, 2026. Status: **independently verified QA, NOT a shipping
customer Editor feature**, commercial NO-GO.

The previous Unity customer uninstall succeeded because its representative
controller/scene did **not** consume HPR interfaces. The new selected-ability
installer now correctly leaves optional HPR AbilityRunner components in an
existing customer's edited scene. Removing the HPR package before examining
customer dependencies could break serialized MonoBehaviours, ScriptableObject
data, custom C# classes or assembly definitions. This is not resolved by
simply retaining the original controller and project settings.

## Independent read-only QA implementation

A deterministic, conservatively scoped CLI prototype lives at:
`unity/tools/release/gameplay_suite/qa/unity_uninstall_preflight.py`.
It takes an existing local Unity project root and the precise .unitypackage
candidate that supplies source-controlled GUID provenance. It reads GUID
identities from the original package, then scans **non-vendor** customer
Assets for exact serialized reference GUID matches. It separately detects
C# source references to HPR namespaces, asmdef/asmref references to HPR
assemblies or vendor GUIDs, and `Packages/manifest.json` **and** `Packages/packages-lock.json`
dependencies on com.hpr modules. A dedicated test confirmed that a
resolved HPR entry remaining only in the package lock is detected,
even if it is no longer listed in the manifest.

The tool uses explicit refusal of symlinked file paths and invalid archive
paths, bounded file reads, and conservative unknown-content reporting for
uninspectable files. It **never modifies any Unity project**, never deletes
assets, does not load or execute third-party C#, and always reports
`deletion_permitted=false` regardless of findings. The three
classifications are customer dependencies found, unknown content requires
review, or no direct references detected. **The third outcome is NOT a
promise that uninstall is safe**, because reflective access, binary assets,
runtime-generated scenes and unobserved external consumer packages can
remain.

A prior test-first run failed because the CLI module was absent. The first
twelve deterministic tests passed after initial implementation. An actual
source-controlled Unity package then exposed a missed root-folder GUID
identity at pathname `Assets/HPRGameplaySuite`. A targeted new
regression first failed, its archive-root rule was corrected, and all
**fourteen** deterministic module tests passed after a further failing-
then-passing regression for an orphaned HPR package-lock dependency.

## Real source evidence, not synthetic-only claims

The same preserved installer-enabled archive previously passed real Unity
6.6 import, customer scene creation and Inspector attach/Undo/Redo checks.
The preflight independently read that REAL exported archive and indexed
**one hundred sixty-one GUID identities**. On the actual imported populated
customer project, it found **ten** direct customer-facing HPR references:
C# source references, an HPR AbilityRunner in **two** serialized customer
scenes, and HPR definitions in **two** customer-owned ScriptableObject assets.
The result was `customer_dependencies_found` and the tool
returned nonzero with `deletion_permitted=false`.

A separate **already HPR-uninstalled** fixture with only an unrelated
customer controller and original scene was correctly classified as
`no_direct_reference_detected`. Even then the tool retained
`deletion_permitted=false` pending user-controlled review.

An additional disposable sample was built from an ACTUAL already verified
Unity customer-created healing scene and intentionally did **not** contain
the vendor HPR root. The preflight still detected the orphaned serialized
AbilityRunner MonoBehaviour GUID in this scene using the saved archive
GUID list, proving the check can find broken HPR references even **after**
vendor sources are gone. All scans were read-only; no original project or
archive was changed.

Grounded logs and JSON reports are preserved outside Git, under the
private Nitro QA scratch evidence directory, with separate source tests
under `tests/test_unity_uninstall_preflight.py`.

## Remaining product gates and commercial verdict

This is a **detector**, not a safe automatic uninstall or migration tool.
Before any buyer-facing release, test against real Unity Editor
AssetDatabase dependencies and nested prefabs, assembly references,
serialized objects inside packages, Unity GUID collisions and dynamic
runtime dependencies. Present precise failure categories, user-authorized
repair options, explicit Undo/migration review and a clear refusal to
silently remove user files. Independent expert user trials remain absent.

A buyer must be able to undo an individual optional runner safely, without
confusing that with uninstalling the entire dependency tree. The selected
ability detach experiment already passed actual Unity 6.6 component-level
Undo/Redo, but full package uninstall with dependent customer game code
remains **UNVERIFIED**. The existing immutable candidate must not be
published based on these read-only findings.

Commercial decision remains **NO-GO**. Source research into existing
paid/editor competitors shows similar workflow claims, and there is no
verified time-to-value, conversion or pricing edge.
