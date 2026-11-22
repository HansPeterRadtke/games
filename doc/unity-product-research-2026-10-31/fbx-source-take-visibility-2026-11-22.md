# FBX Source Take Visibility — new original Unity Editor tool candidate, 22 Nov 2026

## Actual buyer problem and source-grounded choice

Unity documentation says a customized FBX importer clip list does **not**
automatically incorporate additional animations introduced by a later source
FBX edit; the user must manually add the new source take. This is not
necessarily an engine defect. Developers independently describe adding
Blender actions but not seeing them in Unity, confusion over the small
Source Take dropdown, and explicit wish for a supported GUI help button.

* Unity 6000.6 official manual, current: https://docs.unity.com/en-us/engine/6000.6/manual/assets-and-media/asset-types/models/importing/class-animation-clip
* Unity 6000.6 `ModelImporter.defaultClipAnimations` exposes takes from `TakeInfo`: https://docs.unity.com/en-us/engine/6000.6/script-reference/unityeditor/modelimporter/defaultclipanimations
* Unity 6000.6 `ModelImporter.clipAnimations` is **empty on first import**, but stores custom definitions: https://docs.unity.com/en-us/engine/6000.6/script-reference/unityeditor/modelimporter/clipanimations
* User discussion, December 2025–February 2026: https://www.reddit.com/r/Unity3D/comments/1o41nb5/unity_not_importing_new_animations_on_models/
* Related 2025 case where the manual Source Take workflow failed and another FBX import was used: https://www.reddit.com/r/Unity3D/comments/1mx41b9/issues_reimporting_updated_animation_nla_list_and/
* Narrower existing original FBX Clip Identity Audit detects a different real
  problem: repeated clip local IDs, documented in Unity Discussions April 2026:
  https://discussions.unity.com/t/duplicated-internalid-when-creating-animation-clips-on-an-imported-fbx/1716388

The new **HPR FBX Source Take Visibility** candidate explicitly detects source
take names not referenced by a *customized* importer list; it does not
change Unity's behavior, reimport a model or guess replacement animation
clip IDs. It is distinct from HPR FBX Clip Identity's duplicate-ID check.
This is particularly useful as an **import troubleshooting and QA suite
feature**, not evidence of a lucrative standalone SKU. The built-in UI and
manual workaround already exist, reducing willingness to pay. Commercial
buyer counts, store conversion, fees, support burden and probable net income
remain unknown; no claim of existing sales is justified.

## Scope and design

All buyer code lives in `unity/tools/release/fbx_source_take_visibility/Assets/HPRFbxSourceTakes/`.
It is Unity Editor-only and uses only first-party Unity APIs and original
Blender assets. This new candidate is separate from the approved earlier
FBX ID and Archive Preflight tools; no change or submission to those other
products is implied.

`ModelImporter.defaultClipAnimations` gives current source take names,
whereas `clipAnimations` gives user-customized named/time-sliced clips.
**Compare `.takeName`, not `.name`**, because the latter is an editable
clip label that can legitimately differ from the source take. Multiple
customized clips using the same take are normal when splitting one long
FBX timeline into short segments and MUST NOT count as a duplicated source
or missing take. When `clipAnimations` is empty, classify the importer as
normal automatic source-take behavior rather than warning that all source
animations are missing. An input with no source takes, disabled animation
import, ambiguous duplicated/invalid source names, canceled/oversized model
scan or unsupported importer state must not be called an animation pass.

The non-mutating Editor UI has separate example, selected-model and project
scan actions, with the included original animated cube excluded from the
whole-customer-project scan to avoid a fake clean result. It supports a
cancelable scan, readable source take names, create-only JSON export, and
plain-English manual recovery advice. No uploader, auto-repair, account
connection, licensing changes, source FBX changes or private QA scripts
belong to the buyer package. A clean take-name comparison does **not** prove
correct animation playback, clip references, future importer behavior,
retargeting, timings, or availability of every asset.

## Native first-party reproducibility

An original first-party Blender 4.0.2 animated cube was authored with two
separate Actions, `HPR_Original_Sway` and `HPR_Original_Hop`, and exported
with native Blender FBX exporter in a new private folder. The result has
23,100 original bytes and SHA-256
`280dfbfcc7b3288fea028268ed214f3dd36b589e647051c3f051e02dc7b66e1f`.
Actual installed Unity **2022.3.22f1** independently recognized two distinct
source take names in its `ModelImporter`, confirming the Blender source is
not merely a filename with no usable animation data. Its normal
`clipAnimations` list was empty on import, exactly as official Unity docs
predict. The bundled example must continue to return the automatic-default
status, and a brand-new project containing only the example must report
**no customer FBX models scanned**, not a project-wide clean verdict.

The key integration QA uses a separate, NEW disposable private clone of the
original animated FBX and manually configures one source take, then invokes
a real `ModelImporter.SaveAndReimport` **on that private QA fixture only**.
The source scanner must report one uncovered source take, preserve the
original FBX payload, and leave the customer-visible sample untouched.
A fresh independent buyer project should import the exact package exported
by the installed Unity author project and pass the same check. The public
read-only product itself must **never** call SaveAndReimport. No actual
external user FBX or existing customer project is involved.

Native Unity 6 generation, exact package identity verification, all-source
Unity regressions, official Asset Store Tools and authentic normal graphical
screenshots are independent gates. Graphical Editor earlier presented real
software license/terms prompts; those were not accepted. This source work
does not grant terms authority, retail license approval, seller account
publication, marketing images, buyer outreach or a sale.

## First actual independent buyer acceptance — November 22

The exact original first-party candidate was exported with the installed
Unity **2022.3.22f1** `AssetDatabase.ExportPackage`, then imported into a
**separate, newly created buyer Unity project**. Both author and buyer
scanned the original first-party two-action FBX and then deliberately
customized a separately copied private FBX importer to reference only one
of the two source takes. Both native stages detected exactly **one** source
take not referenced by the custom clip list and preserved the original
bundled FBX bytes. The buyer scan excluded the original sample when
computing project-wide missing-take status. Exact original vendor paths,
GUIDs, source bytes and importer metadata were verified against the genuine
Unity export by the fixed-scope fail-closed archive verifier. Private
receipt directory:
`/data/var/marketplace-account-setup/unity-20261122-wave54/native-2022-3-22f1-wave54-first/`.

This is real product code in a real Unity Editor, but the test so far
represents **one available source take deliberately not included in the
configured clip list**, not yet a demonstrated *one-take-source changed to
two-take-source* re-export. Both genuinely original one- and two-take
Blender exports exist to test that stronger update story separately.
A C# unit test alone cannot substitute for that subsequent result.

A second exact independent Unity 6000.6.8f1 author and buyer run is in
progress separately; do not claim it passed before its own native result.
All original source assets remain unmodified outside the intentionally
separate private test fixtures. No seller publication is authorized.

Additional buyer discussions show the Source Take manual process has
confused users for years, but also that Unity has documented the workaround
for years, reducing the price power of an unbundled one-feature tool:
https://discussions.unity.com/t/how-to-properly-re-import-fbx-after-making-changes/879422
https://discussions.unity.com/t/missing-animations-in-unity-from-blender/173255
This is not independently confirmed paying demand or a sales forecast.

## One-to-two original Blender source update: genuine Unity importer behavior

The separate privately isolated **Unity 2022.3.22f1** test reproduced the
actual source-change scenario, beyond an artificial comparison of two lists.
In a new real Unity project the original Blender cube with only one Action
(`HPR_Original_Sway`) was imported and the sole available source take stored
as a custom clip definition using the real `ModelImporter` API. The source
file was then replaced **only in this new disposable test project** by the
separate Blender export with TWO original Actions. The same `.fbx.meta` GUID
was retained. A fresh Editor process reimported the modified FBX and read
the current source takes and saved custom list. The importer reported two
source takes (`HPR_Original_Hop` and `HPR_Original_Sway`), but still had
**only the original Sway** in its customized clip list. The read-only
candidate auditor correctly identified the newly added `HPR_Original_Hop`
as an unlisted source take. Both original authored Blender files retained
exact SHA-256 checksums throughout; only the disposable test copy of the
one-action FBX was replaced. Independent real receipts:
`/data/var/marketplace-account-setup/unity-20261122-wave54/actual-one-to-two-take-reexport-2022-3-22f1/`.

Crucially, this demonstrates the precise Unity-documented missing-animation
workflow, not a generic source-name mismatch and not automatic animation
recovery. The model's original GUID remained unchanged and there were no
other project sources or customer assets. A fresh corresponding Unity
6000.6.8f1 source-update experiment runs independently and must be verified
before claiming both generations behave identically.

A source-only Unity Python regression suite with the new original product
and retained prior products passed **459 tests**. This is distinct from
native author/export/buyer tests and from actual visual/publisher approval.

## Initial candidate: genuine cross-generation release verification

The **same original new product** with one unmodified authored FBX example,
two Editor C# sources, buyer README and rights-review placeholder was
exported by real installed Unity Editors and independently imported into
separate freshly created buyer projects in **Unity 2022.3.22f1 and
6000.6.8f1**. Both original author and independent buyer successfully
completed the source-take probe and private customized-model omission
checks. The importer recognized exactly two original Blender Action take
names, while the uncustomized example had **zero** manual `clipAnimations`
entries and no false warning. The private duplicate FBX customized to only
one source take produced a warning listing the other. The bundled example
never counted toward project-wide scans of customer assets. A create-only
JSON report was exported and the second same-path export refused. Both
immutable source/model bytes and original first-party GUID/meta metadata
were checked against the genuine Unity-exported retail candidates: precisely
**eight buyer paths** (two Editor C# sources, one FBX and docs, three
folders), no private QA files shipped.

Exact private author/buyer evidence:

- `/data/var/marketplace-account-setup/unity-20261122-wave54/native-2022-3-22f1-wave54-first/`
- `/data/var/marketplace-account-setup/unity-20261122-wave54/native-6000-6-8f1-wave54-first/`

The stronger original one-Action-to-two-Action Blender **source file update**
was separately reproduced in Unity 6000.6.8f1 as well as 2022.3.22f1. In
both real installed Editors, a customized importer initially referenced
only Sway. After changing the private source FBX from the original one-
action export to the original two-action export and reimporting, Unity
reported two distinct current source takes but preserved the one-item
custom clip list. The auditor reported missing Hop. The same original FBX
`.meta` GUID survived the update. Original Blender files were preserved
bit-for-bit outside the deliberately disposable test copy. Private proof
for version six:
`/data/var/marketplace-account-setup/unity-20261122-wave54/actual-one-to-two-take-reexport-6000-6-8f1/`.

The full Unity Python source regression suite (including other product
source checks) passed **459 tests** at this milestone. Real Editor GUI
screenshots, official Asset Store validation, publisher approval and
commercial price/demand gates remain distinct; a working technical
candidate is **not** a retail-ready listing.

## New official market counterevidence and sample quality improvement

**Critical competitive finding before retail handoff:** Unity's own Issue
Tracker ticket **UUM-130850**, "Missing new animations in Clips section when
replacing FBX file with Loop Time enabled", states the underlying behavior
cannot automatically change customized clip lists without possibly losing
user edits. It also confirms Unity has **already implemented** an information
message and **Import Unreferenced Takes** button, in fixes listed for
**6000.4.3f1, 6000.5.0b4, and 6000.6.0a2**. The owner-installed tested
6000.6.8f1 is newer than that fix. This official statement is independent
market evidence, not a graphical screenshot observed in this owner's Editor.
Source: https://issuetracker.unity.com/issues/21902/missing-new-animations-in-clips-section-when-replacing-fbx-file-with-loop-time-enabled

This sharply weakens any claim that a standalone checker solves an unmet
single-model problem. The original code's *possible* differentiator is a
read-only, cancelable **whole-project** scan of hundreds of models, but no
actual paying buyer commitment, licensing revenue or operating cost has been
verified. Keep this as an optional importer/preflight suite feature rather
than add a speculative new listing. The buyer UI now points to the native
button first and the manual `+`/Source Take workflow on earlier Editors.

The first candidate's real official offline Unity Asset Store Tools v12 run
returned 34 checks with **30 passes, four warnings and no compilation errors**.
Warnings were **mesh without prefab, incorrect model orientation, missing
demo scene and documentation-content classification**. Exact first-version
receipt: `/data/var/marketplace-account-setup/unity-20261122-wave54/official-ast-2022-wave54-first/asset-store-tools-counted-results.txt`.
This was a quality finding, NOT a seller review.

To address first-use quality, a genuine native-Unity-authored second original
sample was added. It has exactly the same first-party two-Action Blender
FBX bytes as the healthy sample, but a distinct stable Unity GUID and
real Unity importer metadata with only one of the two source takes manually
configured. It is deliberately a *positive warning example*.
The Editor has separate one-click actions for a healthy and a deliberately
incomplete source-take sample; **both** are excluded from whole-customer
project scans. A real native Unity 2022 source author created two prefabs
referencing the respective original FBXs and one static side-by-side demo
scene with a camera and light. The scene is not a real Editor tool screenshot
and does not prove animation playback or legal retail readiness.
Original author identity and content receipts:
`/data/var/marketplace-account-setup/unity-20261122-wave54/original-real-unity-demo-author/real-original-demo-receipt.txt`.

A directory-copy loop initially copied the prefab folder and then failed
safely when it found already-copied files. Rather than rerunning or
replacing any original author effects, the completed prefab source and
metadata were compared byte-for-byte against the live author project and
only the as-yet-absent scene folder and metadata were copied. The private
helper script has since been corrected for future reproducibility; no
original source was discarded or overwritten. The final buyer package must
be re-exported/re-imported on both Unity generations and revalidated with
official tools; first-version validation is not final-source acceptance.

## Revised original package acceptance — November 22 after quality correction

An updated exact **fourteen-path** first-party archive was generated by the
actual installed Unity 2022.3.22f1 Editor, then installed into a separate,
newly created buyer project. Both original author and independent buyer
verified the two separately imported original Blender FBX samples: the normal
source imported two actions with zero manually configured clip overrides;
the deliberately incomplete importer carried a real saved one-take clip list
and the unchanged read-only source scanner correctly identified precisely one
unlisted source take. Their first-party FBX payloads were identical and their
Unity GUIDs correctly distinct. The two first-party prefabs and the actual
Unity Editor-authored side-by-side demonstration scene imported and resolved
their dependencies; the scene is not a verified normal EditorWindow screenshot.
Only the exact fourteen vendor assets (two Editor C# files, original assets,
Unity-authored prefab/scene and docs) were exported, with no QA code or
unknown third-party assets. Source, `.meta` bytes, original GUID identities
and bundled files passed independent strict archive verification. The
original Blender FBX sample remained byte-for-byte unchanged.
Private final 2022 receipts:
`/data/var/marketplace-account-setup/unity-20261122-wave54/native-2022-3-22f1-wave54-final3/`.

The **exact improved exported archive** was subsequently inspected by the
installed official Unity Asset Store Tools version twelve, offline, inside a
new and independent Unity 2022 buyer validation project. Observed result:
`RanToCompletion`; **34 checks, 32 passed, 2 warnings, zero C# compilation
errors**. The earlier "Check Mesh Prefabs" and "Check Demo Scenes" warnings
were resolved by the genuine newly authored prefabs and demo scene. Remaining
warnings are **Check Model Orientation** (the simple Blender cube import)
and **Check Documentation** (documentation file classification). These are
still open review gates, not silently excluded or recategorized. Source
receipt:
`/data/var/marketplace-account-setup/unity-20261122-wave54/official-ast-2022-wave54-final3/asset-store-tools-counted-results.txt`.

Do not claim a final Unity six buyer acceptance until the corresponding
independent native export/import run finishes and its own receipt confirms
identical first-party scope and functionality. Unity native Software Terms
consent, actual UI screenshots and usability, commercial rights and actual
buyer payment willingness remain separately unverified. No seller account
publication, marketing upload or external buyer contact occurred.

## Final independently checked candidate source checkpoint, 22 November

The **final improved fourteen-path Unity package** was exported separately
and independently imported by real installed Unity **2022.3.22f1** and
**6000.6.8f1** into fresh author and buyer projects, including the two
original Blender source examples, two native Unity-authored prefabs and
one native static demo scene. Both author and buyer observed exactly two
source takes in the normal model, one deliberately unreferenced source
animation in the customized example, genuine prefab/scene dependencies,
zero customer FBX files when only shipped examples are present, a separate
private customized model's missing source take warning, and create-only
JSON export refusal on second same-path write. Private original sample
and metadata identities, all fourteen exact buyer paths, source bytes and
original FBX SHA-256s were preserved by independent checks. The author
and buyer original-sample and private deliberately customized scanner
receipts were byte-for-byte identical within each tested Unity version.
The separate real Blender *one-to-two-action* source-update experiment
confirmed the take was omitted in both installed Unity generations.

Final native immutable evidence directories:

- `/data/var/marketplace-account-setup/unity-20261122-wave54/native-2022-3-22f1-wave54-final3/`
- `/data/var/marketplace-account-setup/unity-20261122-wave54/native-6000-6-8f1-wave54-final3/`
- `/data/var/marketplace-account-setup/unity-20261122-wave54/actual-one-to-two-take-reexport-2022-3-22f1/`
- `/data/var/marketplace-account-setup/unity-20261122-wave54/actual-one-to-two-take-reexport-6000-6-8f1/`

The full Unity source regression suite passed **460 tests** on the current
source. The exact final first-party Unity 2022 buyer package passed **32 of
34** official Asset Store Tools checks, with *zero C# compilation errors*.
Two unresolved official warnings, **Check Model Orientation** and **Check
Documentation**, remain visible for legitimate seller/license QA.
The first-version prefab/demo warnings have been removed through actual
new authored assets, not through modifying validator severity.
The Asset Store reviews, authentic Editor UI screenshots, visual sample
acceptance, end-user rights clearance, royalty terms, actual purchases and
commercial viability are **NOT VERIFIED**. Neither this engineering source
nor the seller has received authority to publish it; this is an internal
low-price-power candidate due Unity's existing native take-import button.
