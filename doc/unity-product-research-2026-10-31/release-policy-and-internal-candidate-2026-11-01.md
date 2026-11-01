# Unity commercial product policy and independent candidate

This is an engineering gate, not a draft for public submission. Checked
November 1, 2026 against Unity's **official** current English Asset Store
Submission Guidelines and Unity 6.6 scripting/project documentation. Do not
interpret a successful local build as Asset Store approval.

## First-party references and relevant requirements

Unity submission guidelines:
https://assetstore.unity.com/publishing/submission-guidelines

- Section 1.1.a/b: professional production quality, no package-origin
  errors/warnings after setup; Unity-engine problems are allowed only if
  not usability blockers and disclosed.
- Section 1.3.c: products submitted **using Unity 6.5 or later** must support
  URP or HDRP. A Built-in-only default scene is not sufficient without
  validated support for at least one required pipeline.
- Sections 1.6.a/d and 2.1.h: AI-assisted content must be disclosed using
  specific tools and added human value, and rejected content cannot be
  mass resubmitted or evade review. Former nine rejected HPR submissions
  may not be resubmitted unchanged.
- Sections 2.1, 2.3, 2.5: one well-organized root, no duplicate content,
  short file paths, comprehensive readable offline documentation,
  user-declared namespaces, maintainable source, no unsupported internal
  Unity Editor reflection, no obsolete APIs, domain reload disabled
  compatibility for Unity 6.6 onward.
- Section 2.5.1: Editor UI must serve actual users, no unconsented
  external redirects, and no unsolicited project package mutations.
- Section 3.1: list features and material limitations accurately.
- New UPM publishing officially supports tools, extensions and SDKs.
  Its package separation/updates may fit a mature HPR SDK in the future,
  but Unity verifies publisher identity for UPM and a naive migration
  could break the current buyer GUIDs, paths and project copies.
  Do not switch format merely to claim improved differentiation.

Unity UPM official:
https://assetstore.unity.com/publishing/upm-publishing
Unity Editor domain reload:
https://docs.unity.com/en-us/engine/6000.0/manual/programming-environment/code-reload-serialization/code-reloading-editor/domain-reloading
Unity Editor project setting:
https://docs.unity.com/en-us/engine/6000.6/manual/unity-editor/editor-settings-reference/comp-manager-group/class-editor-manager

Note: accessible localized Unity pages and cached versions can display
different last-updated dates and older sections. The English official page
consulted in this QA pass displayed **May 20, 2026**. Check the live official
publisher policy again **at submission**, not by assuming this snapshot is
frozen. No proposal to bypass review or switch publisher identities.

## Source-frozen new internal candidate on Nitro

The previous October HPR candidate and v14 archive are historical receipts.
A **new unique private scratch release** is under
`/data/tmp/hpr-caltask2fb-20261101`, wholly outside Git and provider
accounts. Its source begins from an exact read-only archive of the product
branch's committed head, overlaid with four relevant uncommitted buyer
guide/docs files from a bounded observed snapshot, and the **two-condition
GUID metadata safety patch** independently verified against a real Unity
Editor in the earlier QA session. The new candidate is intentionally *not*
a merger or commit of the owner's concurrent dirty work.

The frozen snapshot and its original/snapshot hashes are recorded in
`snapshot.json`. Unity 6000.6.7f1 actually created a new project and
exported a new `.unitypackage` with no provider publication. The new
archive was independently validated to contain exactly one hundred and
sixty source/data assets, all ten runtime modules, one demo scene, no
test assemblies or UGUI dependencies, correct AI disclosure and stable
source-controlled YAML/GUIDs. Comparison with the v14 buyer archive
found all one hundred and sixty GUIDs unchanged and **no removed files**.
The archive's integration guide bytes match the **patched frozen source**,
not the older v14 guide; it contains the orphan `.meta` preflight.
No C# compiler warnings, errors or obsolete messages were found in the
candidate's actual Unity 6.6 export log.

**This is an INTERNAL QA candidate only, not final artwork, not publisher
approved, not a paid SKU or release permission.**

## Acceptance that remains necessary for this exact archive

A clean-room import and real scene/runtime tests in Unity six point six,
cross-version Unity six point four checks, exact-v15 upgrade into a populated
customer game, customer-owned asset/scene/Editor-settings preservation,
disabled-domain-reload double entry, new-input-only URP combined checks,
genuine demo material/render validation and user-facing Inspector usability
must be separately tested on the new immutable archive. Prior v14
results do not automatically transfer.

Even after these pass, a commercial decision needs comparison with
existing paid/free ability tools and actual expert developer task success,
time to completion, surprise mutations and willingness to purchase.
The generic ten-module suite remains **NO-GO** for Asset Store submission.
