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

No normal graphical EditorWindow screenshot, human usability acceptance,
formal retail licence, Unity Terms acceptance, seller listing, actual sale
or paid buyer demand has been verified. Unity now provides a native
"Import Unreferenced Takes" per-model button; the possible value of these
complementary tools is limited to project-wide bulk checking and the
specific duplicate local-ID failure. They should be considered as one
combined importer health workflow rather than two repetitive standalone
marketplace products. The single shared seller owns any eventual listing.
