# New HPR FBX Clip Identity Audit candidate — 21 November 2026

Product area: animation importing, *very narrowly scoped* Editor diagnostic. The
actual problem reported by developers is duplicate serialized `internalID`
values for custom FBX `ModelImporter.clipAnimations`, sometimes causing two
animation clips to appear selected simultaneously or preventing reference
assignment. This is NOT a reproducible claim for all Unity versions or FBX
files, and the reported root cause and xxHash input encoding are observations
from community posts, not a Unity API guarantee.

Sources independently checked on November 21:

- Unity Discussions, April 13–14 2026, `Duplicated internalID when creating
  animation clips on an imported FBX`. Author reports actual `fileID already
  exists in m_UsedFileIDs`, and identifies collisions after split/reorder and
  names/take offsets. This motivates read-only exact-ID checking, not guessed
  replacements: https://discussions.unity.com/t/duplicated-internalid-when-creating-animation-clips-on-an-imported-fbx/1716388
- Unity Discussions, November 2023–February 2025, independently describes
  selecting two FBX animation subassets due to repeated `internalID`:
  https://discussions.unity.com/t/selecting-animation-from-fbx-selects-two-animations-at-once/925427
- Official Unity 2022.3 ModelImporter `defaultClipAnimations` docs and modern
  Unity 6.6 `clipAnimations` docs: the latter is empty on first import;
  intentional clip splitting stores Editor-only import settings:
  https://docs.unity.cn/ScriptReference/ModelImporter-defaultClipAnimations.html
  https://docs.unity.com/en-us/engine/6000.6/script-reference/unityeditor/modelimporter/clipanimations
- The Unity Store already offers `Zion Animation Setup & Diagnostics`, a
  broad animation-pack library, clip preview and compatibility lab. It claims
  no model metadata duplicate-ID repair. It is still meaningful overlapping
  marketing competition and further reduces standalone price power:
  https://assetstore.unity.com/packages/tools/animation/zion-animation-setup-diagnostics-402012
- `AnimBinder` focuses on editable `.anim` files and explicitly excludes
  direct repairs of embedded FBX clips. Relevant adjacent competitor rather
  than a matching detector:
  https://assetstore.unity.com/packages/tools/animation/animbinder-368186

Economic decision (not a sales or revenue forecast): zero independent paid
buyer commitments or volume evidence. A small read-only one-bug utility has
low per-license price power even if reliable; worthwhile as a specialized
*feature* of a differentiated importer/preflight pack, not automatically a
new Asset Store SKU. Highest near-term candidate remains the packaged
publisher-upgrade/installation preflight with exact buyer tests. The FBX ID
scanner ranks second as a buyer-problem prototype; a new generic gameplay
systems framework ranks lower without documented superior economics and
complete visual/legal approval. Avoid chasing additional generic validators.

Technical design: original standalone Editor-only read-only source under
`unity/tools/release/fbx_clip_identity_audit`. Scan both
`ModelImporter.internalIDToNameTable` (class 74) and
`ModelImporter.animations.clipAnimations[].internalID` (custom configured
clips). Confirmed signed 64-bit duplicates only; repeated zero values are
ambiguous placeholders and must trigger INCOMPLETE/manual review. No file
reimports, direct .meta edits, automatic ID replacement or account effects.
Missing/unrecognized metadata and capped/canceled project scans fail closed.
Use a fixture built in Blender by this producer; inspect real Unity importer
metadata on each supported Editor version before claiming functionality.

Release gates: real Unity 2022.3 and Unity 6.6 clean author/buyer imports,
custom split-clips fixture, source-byte preservation, synthetic duplicate-ID
positive/negative samples, exact archive scope/GUID integrity, official Asset
Store Tools validation, normal GUI layout screenshot/readability, license,
provenance, buyer willingness to pay and final shared-seller approval. The
source QA script alone is NOT buyer-ready evidence.

## Actual native validation and graphical limits, 21 November

Original Blender four-point-zero-two exported one independently authored,
animated FBX. Unity 2022.3.22f1 and Unity 6000.6.8f1 recognized its real
ModelImporter, AnimationClip subassets and two deliberately configured split
clips; their `.meta` files contain signed `clipAnimations[].internalID` values.
The test separately injected **synthetic duplicate ID YAML** into the
read-only parser, which correctly produced a collision finding. It did not
cause Unity itself to produce a collision and is **not** a reproduction of the
engine hashing defect. The real model's original bytes and importer metadata
were unchanged; test-only split clips were made in a separate disposable copy.

In a fresh author and independent buyer project on Unity 2022.3.22f1, the
second original product source version passed its imported-model/source and
metadata tests with no compilation errors, sixteen native checks. After the
empty-project `NO_FBX_MODELS_SCANNED` refinement, the exact final version
passed seventeen native checks in both author and buyer projects. Its actual
Unity archive passed fixed-scope source/GUID verification. The corresponding
Unity 6000.6.8f1 exact final project QA must also return PASS before claiming
cross-version completion; no unsupported Unity versions are implied.

Real GUI attempt in a separately owned private Xvfb display:
Unity 2022.3.22f1 crashed before the target window was displayed (native
SIGSEGV/Mono exception-reporting recursion after a mixed-editor layout
warning); Unity 6000.6.8f1 showed an Editor **Software Terms** consent dialog
which the producer did not accept or bypass. Neither screen may be used as
real product media. Private original screenshots and logs are preserved at
`/data/var/marketplace-account-setup/unity-20261121-evening/` and all
owner desktop tabs/layouts were left unchanged. Graphical buyer acceptance,
rights, official Asset Store validator, price and real demand remain open.

## Buyer-ready example and workflow, November 21 wave 48

A key first-use weakness was confirmed: earlier native QA used a private
Blender animation but shipped no usable example asset, and the Editor offered
only a potentially slow project-wide scan. The new candidate **ships the
first-party original animated FBX** (`Samples/OriginalMotion.fbx`, 18,236
bytes; SHA-256 `5077da866845ba9638311faa57af0cfd77a84ae2f7fe915064a73e23ca57d84e`)
with stable original vendor metadata and self-contained buyer documentation.
The Editor provides a fast bundled-example action, a selected-model single-file
check, and a separately labeled cancelable whole-project check. An FBX that
imports no animation clip no longer looks like a clean animation-ID audit;
it reports `NO_ANIMATION_CLIPS_IN_CHECKED_MODELS`.

Native acceptance using **installed Unity 2022.3.22f1** and **6000.6.8f1**
was independently completed in genuine disposable author and freshly created
buyer projects for each Editor version. Both real exports include precisely
eight vendor paths, two original Editor C# scripts, one original FBX asset;
exact metadata GUIDs, source bytes and sample animation bytes match source.
Both author and buyer receipts contain **twenty-one passing native checks**,
including original importer preservation, custom split-clip ID behavior,
malformed/repeated-zero negative fixtures, sample/selected scanning, and
clipless-scan classification. Python Unity regression suite: **four hundred
thirty-five passed**. Private unchanged receipts and exact archives:
`/data/var/marketplace-account-setup/unity-20261121-evening/native-2022-3-22f1-with-sample-wave48/`
and `native-6000-6-8f1-with-sample-wave48/`.

The shipped sample demonstrates import and a valid no-collision scan; it does
**not** reproduce Unity's rare duplicate-ID engine bug. Positive duplicate-ID
checks use explicitly synthetic data, not a mutated customer model. Real
Editor GUI screenshot acceptance remains blocked by Unity Software Terms and
a separate Unity 2022 graphical crash, neither bypassed. First-party Blender
sample is included only with its basic original mesh/animation; no third-party
asset content or stock image is used.

Market positioning remains conditional. Unity's October 23 submission rules
require truthful documentation, the correct dependencies and appropriate
samples for external-asset tools, and reject largely duplicated or generic
mass-produced assets. This improved technical demo is not proof of purchases,
commercial rights, seller approval or an acceptable marketing image. Treat
this narrowly scoped scanner as a potential feature of a broader publisher
preflight package unless measurable buyer demand justifies a separate SKU.
