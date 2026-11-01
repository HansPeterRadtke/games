# HPR Unity Asset Store listing: original draft versus verified internal candidate

November 1, 2026. **PRIVATE QUALITY AUDIT — NO PUBLIC SUBMISSION.**
The other agent's **uncommitted original listing draft**
`doc/unity-suite-listing-draft-2026-10-31.md` was inspected
read-only. It was not edited, copied to a publisher account or resubmitted.
The relevant candidate is the preserved SHA-pinned 161-asset internal
selected-installer archive from the earlier Unity QA continuation, not a
new approved commercial release.

## Source-verified claims that can remain, with exact context

- The archive contains ten original HPR runtime modules, one fully
  integrated Unity primitive-based training arena and a single package
  root. The new Editor-only selected-object installer is included in the
  internally built release candidate. The archive excludes test runners,
  third-party art and bundled UGUI code.
- Unity 6000.6.7f1 cleanroom package import and ten actual runtime
  gameplay/save tests passed. Unity 6000.4.0f1 source/Importer also
  compiled and retained old asset identities. Unity 6.6 two Play entries
  without domain reload passed. The original 160 GUIDs remained stable.
- A representative existing buyer controller/scene/prefab and standalone
  serialized customer settings survived real Unity 6.6 v14-to-current
  package import. All 59 protected original customer files remained
  unchanged. Actual installed Editor tool attached a customer-owned
  ability with an explicit resource provider, and Undo/Redo/serialized
  Inspector and dynamic UI behavior were independently tested.
- AI-assisted C# and documentation provenance is accurately disclosed
  as a candidate draft; the exact earlier tool history must still be
  independently signed off. No claims of independent human visual
  handcrafting or buyer testimonials are supported.

## Statements requiring careful limits or additional testing

- The original listing says URP 17.6 sample-material conversion and
  camera screenshots were validated on an **older v14 imported buyer
  archive**. That older result is genuine QA history. The new frozen
  selected-installer archive has runtime/demo/material bytes identical
  to that v14 package, but **two** actual attempts to import the exact
  newer archive into a URP 17.6/Input 1.20.1 new-only Unity 6.6 test
  project timed out **before any new HPR source was imported**, including
  a clean Library project. A current exact-archive URP qualification
  would therefore be misleading. Clearly name the v14 evidence and the
  unverified newer candidate if the listing is revised later.
- The product does not provide a complete plug-and-play replacement
  controller or general no-code ability setup. The selected-object
  installer requires an appropriate user-owned AbilityData and a
  MonoBehaviour provider implementing `IAbilityResourcePool`.
  The private QA fixture has a short adapter script, and no measured
  external buyer completion-time result.
- Reversible component-only removal with Unity Undo/Redo has passed in
  a separate internal Editor QA overlay. The reviewed detach patch is
  **not in the immutable selected-installer archive**. Do not imply the
  packaged buyer UI contains that dedicated removal button.
- Full safe package uninstall **for customers whose scenes and code
  actually depend on HPR** is not implemented. The new read-only CLI
  correctly identified ten direct HPR dependencies in a real populated
  customer fixture, from actual vendor GUIDs, C# source and scene/data
  references. It also found an orphaned GUID after vendor removal.
  It emits review actions but never authorizes automatic deletion;
  it is QA-only, not a distributed commercial feature.
- A real Unity 6.6 Editor Search index exception reproduced *without*
  HPR source; it should not be misreported as an HPR compilation error
  or hidden if it affects final buyer workflow. The actual URP Bee/ILPP
  timeout remains an engine/toolchain acceptance blocker even without
  HPR source, amid heavy Nitro CPU contention.
- Screenshots/media must come from the exact or byte-identical actual
  Unity scene with truthful notes. The source-specific full-dark/light,
  high-DPI, keyboard navigation and buyer-facing readability of the
  new installer tool have not been visually accepted in this sprint.
- Claiming 'unique', 'easy', 'zero-code', 'production-ready' or a justified
  selling price requires a genuine external developer task benchmark
  against one direct competing ability editor. Current public competitors
  already advertise easy two-component ability integration, user
  configurable abilities and source-level APIs. No purchase intent,
  verified sales or testimonial evidence exists for HPR.

## Suggested conservative listing decision

Do not publish or submit this draft. Maintain the accurate source/demo
description as private documentation. If an owner later requests
commercial review, replace generic framework positioning with a
demonstrated single existing-game integration task and enumerate
user-owned input/controller/resource requirements. Pass a new source-
and-archive-specific Unity URP/new-input matrix, actual visual UI
review, buyer Undo/migration/uninstall validation, verified AI-tool
attribution, publisher verification and actual competitor/user-value
trials before making price or approval claims.

**Commercial status: NO-GO.** This audit wrote only an independent QA
document and left the owner/other-agent dirty listing untouched.
