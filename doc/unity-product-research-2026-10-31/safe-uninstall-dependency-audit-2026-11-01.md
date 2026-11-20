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
**seventeen** deterministic module tests passed after further failing-
then-passing regressions for an orphaned HPR package-lock dependency,
concrete non-destructive per-category reviewer guidance and a vendor GUID
reference embedded in a customer-owned Unity importer .meta file.
The latter is a distinct potential failure source: importer metadata
can reference an HPR shader or material even when no scene YAML directly
does. The scanner now inspects non-vendor importer .meta text rather than
assuming all metadata is only a self-GUID. The CLI now
returns reviewed next actions for serialized scene references, HPR C# use,
assembly definitions and package manager dependencies; these actions
are text only, never automatic file edits. Its file reads are bounded even
if an asset grows after initial size inspection. The filesystem traversal
itself now streams file paths and stops at a configurable bounded count
(default two hundred thousand) with an explicit unknown/review outcome;
it does not create an unlimited in-memory list for huge Unity projects.
A new test first failed on the absent bound and passed after adding it.

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

## Addressables dependency checks, November 12, 2026

A copied installation contained all 161 GUID identities from the older exported suite.
Two buyer fixtures referred to assets in that installation. A shop asset pointed to
Repair through a serialized Addressables reference. A prefab instance in an embedded
customer package overrode an array element to point to Pulse through the legacy field
name. Previously, the uninstall check reported zero dependencies and the upgrade
preview passed its source checks with both references present.

Both commands now return exit code 2 for this project. Each lists the buyer file,
the referenced GUID, and the corresponding vendor asset for review. The scanner reads
the current and former AssetReference field names and Unity's serialized prefab
property-path/value pairs. This check covers GUIDs stored in Unity text assets.
Runtime addresses constructed in code still require separate testing.
[Unity Addressables field definition](https://docs.unity3d.com/Packages/com.unity.addressables@2.7/api/UnityEngine.AddressableAssets.AssetReference.m_AssetGUID.html)

The before-and-after command reports and the SHA-256 inventory are under
`/data/var/marketplace-account-setup/hpr-addressable-reference-preflight-20261112`
on Nitro. All 297 files matched the original inventory after both scans. The
uninstall and upgrade test suites cover ordinary object references, Addressables
references, prefab overrides and unrelated GUID strings.

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
