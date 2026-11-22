# Original Unity animation importer products: real coinstall fix and sample quality — 22 November

This is original developer evidence for **unpublished first-party product candidates**,
not a sales/publisher receipt. Earlier first-party source records and original
owner instructions remain authoritative for their separate dates.

## Buyer integration defect reproduced, then corrected

The original `HPR FBX Clip Identity Audit` excludes only its own first-party
FBX teaching model from whole-project scans. Likewise, the new `HPR FBX
Source Take Visibility` excludes its own two teaching models. A developer
installing both tools therefore gets a misleading "no issues" result even
when there is no actual customer FBX present: each product counts its
neighbor's original bundled teaching model as customer content.

A **genuine installed Unity 2022.3.22f1** fresh disposable project imported
both real original vendor folders, plus only a QA runner, and ran both
public product `ScanAssets()` methods. With no user FBX file present, the
observed customer-model counts were **2** in Clip Identity and **1** in
Source Take Visibility. Both reported normal/clean-looking scanner statuses,
which are materially misleading for buyer quality. Original immutable evidence:
`/data/var/marketplace-account-setup/unity-20261122-wave55/coinstalled-2022-before-fix/native-original-coexistence-report.txt`.

The scanners now exclude only **three exact original HPR sample FBX paths**;
no generic vendor directory, third-party package or customer FBX is filtered.
After the correction, a second **fresh independent Unity 2022** project
imported the same two source roots and repeated the real native scan. Both
reported **zero customer models** and explicit `NO_FBX_MODELS_SCANNED`/
`NO_CUSTOMER_FBX_MODELS_SCANNED` statuses rather than invented clean passes.
Test reference:
`/data/var/marketplace-account-setup/unity-20261122-wave55/coinstalled-2022-after-fix/native-original-coexistence-report.txt`.

This is a real integration fix, not a standalone test-only workaround. Both
original buyer documents and product source regression tests were updated.
Importers are read-only in the buyer release; no customer model was modified.
The installed combined package validation must also verify the exact updated
serialized metadata/GUIDs and fail-closed scanned counts.

## Genuine first-party Blender sample orientation correction

Earlier official Unity Asset Store Tools v12 reported the original Blender
teaching cubes as improperly oriented. Inspection of that exact validator's
`CheckModelOrientation` implementation confirmed it flags any imported mesh
child with a non-identity local rotation when `ModelImporter.clipAnimations`
is empty. The older Blender sample was a *real animated source* with two
automatically imported takes, but also an unhelpful hidden ninety-degree
local mesh rotation and scale of one hundred. A separate first-party Blender
4.0.2 exporter variant using `bake_space_transform=True` imported two
original Actions with identity child rotation and unit scale in installed
Unity 2022.3.22f1, verified against the old source and alternate axis exports.

Both authored first-party teaching FBX assets (healthy and deliberately one
source take unlisted) now use exactly the same tested axis-baked Blender
bytes, keeping their original distinct Unity `.meta` GUIDs and the actual
saved importer settings on the intentionally customized example. The
native prefabs and demonstration scene retained their original references
rather than being silently recreated or given new GUIDs.

A **genuine original Unity 2022 author and independent buyer** installation
of the private baked-source candidate passed the existing source take,
importer and asset-identity QA. A separate native prefab+scene geometry
inspection confirmed that each original FBX and each original prefab
contains a real mesh with at least eight vertices, nonzero bounds, identity
local rotation and unit scale; the demo scene loaded both prefab meshes
and its floor. The corresponding original Unity 6000.6.8f1 private author
and buyer packages passed and their prefab geometry probes confirmed the
same mesh/scene properties. Exact receipts:
`/data/var/marketplace-account-setup/unity-20261122-wave55/baked-mesh-author-2022-proof.txt`,
`baked-mesh-buyer-2022-proof.txt`, `baked-mesh-author-6000-proof.txt`,
`baked-mesh-buyer-6000-proof.txt`, and under
`native-2022-3-22f1-baked-trial1/`, `native-6000-6-8f1-baked-trial1/`.

The exact private baked-source Unity 2022 archive passed **all 34 of 34**
installed official Asset Store Tools checks, with zero warnings or C#
compilation errors, compared to the old source's 32/34 and two warnings.
The buyer documentation is genuine original instructions and now contains
an explicit **Documentation and first-use guide** heading, addressing the
validator's simplistic content check rather than masking the actual asset
warnings. Exact official receipt:
`/data/var/marketplace-account-setup/unity-20261122-wave55/official-ast-2022-baked-old-documentation/asset-store-tools-counted-results.txt`.
The folder's historical label is not evidence of a failing documentation
check: its actual source README had already been updated before this export.

A real original one-to-two-Action Blender source replacement retained the
private customer's Unity GUID and manually customized list, and the scanner
still identified the newly added Hop source take on native Unity 2022 with
the corrected baked source. This is reproducible in the private QA runner.

## Source and commercial truth

The corrected original first-party binary source has sample SHA-256
`cf617c46018dfbec648765c0487e3215b1e1251c26817916f6f4a23aef0228fa`.
The old source SHA-256 remains in earlier untouched artifacts; it must not
be presented as the new package's content. Actual original importer `.meta`
GUIDs, referenced prefabs, scene paths and Unity Editor sources are preserved.
The exact final canonical source after this correction requires new author/
buyer export verification in both installed Unity Editors and an independent
current-source official validator run before claiming a final released
package; the private baked trial is a proof of the proposed source change.

## Follow-on original clip-ID sample and combined package quality gate

The **other** original first-party FBX sample, `OriginalMotion.fbx` within
`HPRFbxClipIdentity`, had the same Blender model-axis problem as the newer
source-take teaching models. Installed Unity 2022 confirmed the original
model's imported mesh orientation could be corrected by exporting with
Blender `bake_space_transform=True`; the genuine native importer retained a
source AnimationClip and the read-only duplicate-ID diagnostic remained clean.
The original model was regenerated from its existing author-controlled Blender
script, and the same original asset GUID was retained. A fresh independently
imported Unity 2022 buyer archive passed the existing original FBX positive,
negative and source-byte preservation tests. Evidence:
`/data/var/marketplace-account-setup/unity-20261121-evening/native-2022-3-22f1-wave55-baked-prefab/`.

A separate original Unity 2022 author project created a genuine prefab with
a nonempty original Blender mesh reference. The prefab's Unity GUID was
generated by Unity itself and the prefab depends on the unchanged existing
model GUID, rather than on a private placeholder or a new copy of the model.
Evidence: `/data/var/marketplace-account-setup/unity-20261122-wave55/original-clip-id-prefab-author-2022/prefab-original-author-receipt.txt`.
The new first-party retail source has **two additional original Unity assets**:
the prefab and its folder, with separate `.meta` files. Both the original
standalone clip-ID archive validator and the independent three-root bundle
validator must include their exact GUID/meta/source bytes.

The original Blender FBX exporter emits certain timestamp and generated-ID
bytes which can change between separate export invocations even with identical
mesh and animation instructions. A fresh same-script export therefore did
**not** reproduce an identical file hash. Do not misstate bit reproducibility:
the authoritative release is the *exact committed original FBX payload*,
verified byte-for-byte against the two independently Unity-exported customer
archive contents, with genuine Unity importer validation of the geometry.
The previous FBX asset version remains in Git history and older untouched
private archives, not in a customer upgrade procedure that could change IDs.

On 22 November, the **new exact twenty-nine-asset combined** package, with
the original clip-ID prefab and corrected axis-baked Blender sample, was
independently exported and imported on installed Unity 2022.3.22f1. All
original author/buyer vendor-only and deliberately customized source-take
checks passed. Official installed Unity Asset Store Tools v12, running on
that exact combined buyer `.unitypackage` inside a new isolated Unity 2022
project, returned **34/34 passing checks, zero warnings and zero C# compile
errors**. This genuinely resolves the earlier two combined-package warnings
(Mesh Prefab and Model Orientation), rather than hiding or muting warnings.
Private receipts:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-2022-3-22f1-clip-prefab-fix1/`
and
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-ast-2022-clip-prefab-fix1/official-validation-counted-results.txt`.

The complete Unity source regression suite passed **465 tests** after this
revision; the result was observed independently from native Unity Editor
compilation. The corresponding final Unity 6000.6.8f1 combined author/buyer
acceptance **also passed independently**. Both installed Unity Editors
exported the exact 29 first-party asset roots, imported their own package
into a separate fresh buyer project, ran the original vendor-only scan and
the real private customer FBX positive/negative checks; original author and
buyer receipts matched. The 6000.6.8f1 archive is a separately generated
Unity export of the same controlled source, not a claim of identical archive
bytes. Private proof:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-6000-6-8f1-clip-prefab-fix1/`.

Further native buyer-only read-only geometry checks in **both Unity versions**
verified that all three original Blender teaching models import real meshes
with identity local orientation and unit scale. All three genuine first-party
Unity prefabs resolve their source FBX mesh references; the demo scene
references both source-take prefabs. Private proof files:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-2022-3-22f1-clip-prefab-fix1/final-independent-buyer-original-geometry.txt`
and
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-6000-6-8f1-clip-prefab-fix1/final-independent-buyer-original-geometry.txt`.
The combined native QA test is an actual installed Unity Editor run, but **not** a
normal graphical EditorWindow screenshot or human visual approval. Official
validation is not owner acceptance of Unity Software Terms, genuine Editor
window screenshot review, legal seller rights, a proven buyer or storefront
approval. No customer FBX files or published listings were changed.


No normal graphical EditorWindow screenshot, human usability acceptance,
formal retail licence, Unity Terms acceptance, seller listing, actual sale
or paid buyer demand has been verified. Unity now provides a native
"Import Unreferenced Takes" per-model button; the possible value of these
complementary tools is limited to project-wide bulk checking and the
specific duplicate local-ID failure. They should be considered as one
combined importer health workflow rather than two repetitive standalone
marketplace products. The single shared seller owns any eventual listing.


## Actual Unity 6.6 Fast Enter Play Mode quality check, 22 November

The official October 23 Unity Asset Store submission rules require packages
with scripts on Unity 6.6 or newer to support entering Play Mode when **Domain
Reload is disabled**. We tested this in the actual independently imported
Unity **6000.6.8f1** combined animation buyer project. Only that disposable
private project's `EditorSettings.enterPlayModeOptionsEnabled` and
`EnterPlayModeOptions.DisableDomainReload` were changed for the test; no user
project, source FBX or source material was modified. An original private QA
Editor callback observed genuine `EnteredPlayMode` and `EnteredEditMode`
transitions. The **same actual project-wide combined read-only scanner**
returned a consistent one-customer-model missing-source-take warning before
and after Play Mode, with **zero captured console errors/exceptions**. The
private harness itself exited only after observing both actual Unity state
transitions and saving a create-only receipt. No unapproved Terms acceptance
or graphical EditorWindow testing was attempted.

Exact native proof:
`/data/var/marketplace-account-setup/unity-20261122-wave55/fast-enter-playmode-6000-6-8f1-real-original-buyer.txt`
and preserved native Editor log under the same basename. This is one actual
supported-version Play Mode scenario, not universal Player build/runtime
compatibility, visual acceptance or Asset Store listing approval.


## Actual rendered visual QA and original caption repair — 22 November

The original first-party source-take teaching scene was rendered from a
**real installed Unity 2022 buyer project** inside a new isolated Xvfb
virtual display, with Unity's real Camera, RenderTexture and PNG encoder.
It was NOT an AI-generated mockup or a manually assembled promotional
image, and no normal EditorWindow or Unity Software Terms dialog was
accepted or bypassed. The first authentic 1440-by-900 preview revealed a
serious visual defect that earlier source tests and official Asset Store
Tools did not detect: both long prefab labels overlapped and were unreadable.
The original capture is preserved privately as
`/data/var/marketplace-account-setup/unity-20261122-wave55/verified-real-unity-buyer-scene-preview-20261122.png`.

A fresh private first-party Unity 2022 author project reopened both
original prefabs using genuine `PrefabUtility.LoadPrefabContents`, changed
only their textual guide labels to concise centered two-line versions,
reduced the TextMesh character size and moved the captions upward. Unity
then wrote the revised prefab assets, preserving both exact existing Unity
GUIDs and each original animated FBX mesh dependency. The original Unity
scene retained the same two prefab GUID references and was not rewritten.
Two labels now read **AUTO IMPORT / 2 takes available** and **CUSTOM IMPORT
/ 1 take unlisted**. Exact private native author evidence:
`/data/var/marketplace-account-setup/unity-20261122-wave55/original-two-caption-repair-author-2022/original-prefab-caption-repair-receipt.txt`.

The *revised product* was then independently exported in actual Unity
2022.3.22f1, imported into a new consumer project and tested with its real
author/buyer scan fixtures; the strict original archive checker verified
**29 authored assets** including the two revised native prefabs and all
original `.meta` GUID identities. The real Unity scene was rendered again
from the freshly installed buyer package. The second untouched original
1440-by-900 PNG has two separate legible labels and side-by-side original
cubes, confirmed by direct visual inspection of a downsized copy. It is
**usable as a genuine static first-party example preview**, but is not a
screenshot of the actual EditorWindow or proof of human UI acceptance.
Private exact camera screenshot:
`/data/var/marketplace-account-setup/unity-20261122-wave55/verified-real-unity-buyer-scene-preview-captionfix1.png`;
source/export/independent consumer receipts:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-2022-3-22f1-captionfix1/`.

The **exact revised buyer package**, not the earlier overlapping-caption
archive, again completed all **34 of 34 official Unity Asset Store Tools v12
checks with zero warnings and zero C# compilation errors**, in a separate
new Unity 2022 validation project. Exact independent receipt:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-ast-2022-captionfix1/official-validation-counted-results.txt`.
The source-only full Unity suite passed **467 tests** for this revision.
The **actual updated Unity 6000.6.8f1** author/export and independently
installed fresh buyer project also passed the final original three-root
package acceptance, including genuine positive/negative private customer FBX
importer outcomes and the strict 29 original Unity vendor asset archive
scope/GUID verifier. Private immutable proof:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-6000-6-8f1-captionfix1/`.
A genuine second camera-rendered scene PNG was captured **inside that real
Unity six buyer project** using an isolated Xvfb display and Unity graphics
pipeline, not a synthetic mockup:
`/data/var/marketplace-account-setup/unity-20261122-wave55/verified-real-unity-buyer-scene-preview-6000-6-8f1-captionfix1.png`.
It is 1440 by 900, and direct visual inspection of a 960 by 600 inspection
copy confirmed **both white two-line captions are legible, separated,
centered above their corresponding gray Blender cubes**, with no original
caption overlap. Both Unity 2022 and Unity six corrected original previews
are safe source-grounded example-scene images, but they are **not** actual
EditorWindow screenshots. The graphical Editor tool window inspection,
licensing, transparent AI-assisted source disclosure, demonstrated paid
demand and seller publication authority remain separate release gates. Do
not use the raw first overlapping screenshot as marketing media.

## Successor buyer navigation improvement — 22 November

The prior combined FBX import checker displayed aggregate counts but instructed customers to open two separate vendor windows to locate the affected model. That defeated the main purpose of a combined workflow. The successor adds a single **issue-first results browser** with a case-insensitive FBX path filter, a read-only **Select FBX** Project-window navigation button, per-model local-ID and source-take statuses, and the actual unlisted source take names. A customer can disable the issues-only toggle to inspect all analyzed files without changing their model import settings.

The new `HprAnimationImportScan.BuildRows` derives rows from the already completed scan and refuses to present results from null, incomplete or differently aligned source reports. The matching requirement preserves exact customer model paths; no rewrite/reimport, network access, asset deletion, or existing JSON overwrite operation was introduced. Showing results in the Editor UI does not constitute a separate validation of Unity GUI usability.

Original source QA on the current successor revision: all **467 Unity source tests passed**; focused combined/FBX checks passed nineteen. An actual fresh Unity 2022.3.22f1 author/export and independent buyer import checked all **29 original first-party assets**, matching package bytes and GUIDs, bundled samples excluded from customer counts, and both positive and negative private FBX cases. The private one-to-two-take customer sample showed the unlisted source take `HPR_Original_Two_Take_Cube|HPR_Original_Sway` and zero duplicate local IDs; the new results helper returned exactly that model and take. The independent original author and buyer QA receipts matched byte-for-byte. Exact new private runtime evidence:
`/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-2022-3-22f1-browse-20261122-v1/`.

The successor's **fresh Unity 6000.6.8f1 independent author/export and buyer installation also passed**. The exact twenty-nine original first-party assets and their GUIDs were preserved; author and buyer receipts matched byte-for-byte for bundled examples, healthy customer source, and the deliberately omitted original animation take. No tested customer FBX bytes changed. Native proof: `/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-6000-6-8f1-browse-20261122-v1/`.

The **fresh official Unity Asset Store Tools version twelve** completed all **thirty-four of thirty-four checks** on the exact successor Unity 2022 exported archive with **zero issues and zero C# compilation errors**. Proof: `/data/var/marketplace-account-setup/unity-20261122-wave55/combined-ast-2022-browse-20261122-v1/official-validation-counted-results.txt`. Earlier clean validation receipts do not substitute for this new result. This does not establish normal human-facing EditorWindow acceptance, renewed Play Mode testing for this revision, licensing or paying demand. The standalone diagnostic remains commercially weak because modern Unity already offers per-file missing-source-take import assistance. There is no verified paid demand, seller authorization, legal/licensing approval, or authentic graphical EditorWindow screenshot. Keep the revised tool private and disclose AI-assisted functional work accurately if a publisher later considers a listing.
