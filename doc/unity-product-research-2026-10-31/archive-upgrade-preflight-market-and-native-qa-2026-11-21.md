# Unitypackage Archive Upgrade Preflight — buyer demand and technical QA, 21 November 2026

This record describes an original read-only `Assets/HPRArchivePreflight`
Unity Editor-only product **candidate**. It is not an Asset Store listing,
a verified paid product, an installation into any non-QA customer project,
or an owner-approved legal license. The existing
`package_boundary_audit` scans Unity's currently loaded assets. This
candidate instead compares **two archived `.unitypackage` files before
import** and checks their metadata identity, entire source file SHA-256s,
folder type, changes to import settings and TAR/GZIP archive integrity.
It never extracts, imports or rewrites an archive. It has no downloader,
network service, external asset dependency or automatic repair operation.

## Actual problem and competing solutions

Public evidence, read on November 21:

* Unity development forum: an August 27 developer importing a commissioned
  avatar update reported that a new `.unitypackage` overwrote older assets,
  despite separate folders, plausibly due to reused GUIDs. A temporary-
  project export did not resolve the problem. This supports a narrow pre-import
  identity check but is **one anecdote**, not measured broad willingness to
  pay: https://www.reddit.com/r/Unity3D/comments/1vzslbx/
* A February 2025 professional model artist reported broken prefab/FBX
  imports and reference warnings when asset GUIDs changed between customer
  revisions. Again this illustrates impact, not prevalence or purchases:
  https://www.reddit.com/r/Unity3D/comments/1ign07m/
* Unity's official Asset Store update documentation describes reimport of
  `.unitypackage` updates, and separate UPM package version changes; its UPM
  marketing materials promote managed update workflows. This product only
  examines **classic archived** `.unitypackage` files, not paid UPM
  entitlements or Registry package migration:
  https://docs.unity.com/en-us/asset-store/downloads/asset-store-packages
  https://assetstore.unity.com/publishing/upm-publishing
* PackageLens is a **direct existing commercial competitor**: it inspects
  incoming `.unitypackage` assets against the **current Unity project** and
  flags modified/conflicting assets, path/GUID collisions and dangerous import
  choices. Its different baseline (an installed project, not another archive)
  does not eliminate competitive overlap or demonstrate unique buyer demand:
  https://assetstore.unity.com/packages/tools/utilities/packagelens-package-import-review-tool-375592
* Free GitHub reference inspection tools and generic package validators
  remain additional low-cost alternatives:
  https://www.reddit.com/r/Unity3D/comments/1row02d/
* A November 11, 2026 publisher reported five existing Asset Store packages
  stuck in a seller-portal Error state after updates, with a buyer unable to
  download a previously paid item. This **portal backend** problem is not
  addressable by a local `.unitypackage` identity analyzer. Do not market
  this tool as a fix for it:
  https://discussions.unity.com/t/five-previously-published-asset-store-packages-stuck-in-error-after-updates-customers-cannot-download/1741648

Current commercial ranking by **relative technical feasibility and expected
support burden**, not measured sales: existing Gameplay Systems Suite is the
closest substantial product but needs real Editor walkthrough, licensing and
better buyer-facing presentation. Archive/version safety preflight is the
most technically differentiated new utility direction and can reuse tests,
source and the owner's first-party package history. It still competes with
PackageLens, and the plausible strongest offer is a combined publisher
preflight/upgrade package rather than another thin standalone SKU. FBX clip ID
detection may be one feature within an animator/importer suite but has no
independently demonstrated economic scale. Generic validation and UPM
scaffolding are not worthwhile additions to the catalog without buyer proof.
No sale, price elasticity, net income, time-to-cash or conversion rate has
been independently measured. The one shared seller owns store evaluation and
publication, and may reject this candidate.

## Strict implementation and quality boundaries

Original source under
`unity/tools/release/unitypackage_archive_preflight/Assets/HPRArchivePreflight/`
contains a strict stream reader and a read-only Editor window. A bounded,
standard TAR.GZIP interpreter validates per-member TAR header checksums,
UTF-8 pathname safety, a metadata GUID that agrees with each per-asset
member GUID, duplicate paths or payloads, type restrictions, count/size
limits, and **the actual decoded GZIP CRC32/ISIZE footer**. Nonregular
members, symbolic links, metadata mismatch, truncated compressed streams,
unsafe path segments, malformed TAR checksums, uncertain layouts and any
canceled scan are `INCOMPLETE`; no unsafe fallback import is performed.
SHA-256 compares the full original source and importer metadata bytes even
when GUIDs stay the same. It separates added/removed paths, GUID changes,
relocations, source changes and import-setting modifications.

A changed serialized fileID, broken C# API, dynamic asset loading, UPM
Registry dependency, runtime material/shader behavior or customer-specific
serialized content is **not** guaranteed safe by an unchanged asset GUID.
Publishers must still test in a populated buyer project. Huge/unusual TAR
formats currently fail closed; this is intentionally a technical candidate
rather than claiming universal `.unitypackage` compatibility.

## Native acceptance and evidence rules

Actual archived original vendor versions are the November 21 real five-asset
and six-asset HPR Package Boundary Inspector packages. A genuine Unity
native Editor author project and an **independent newly created buyer**
project each parse those archives without changing their SHA-256, report the
one added GUID and the two observed source changes, and refuse a deliberately
changed old GUID, metadata disagreement, path traversal, truncated gzip,
and TAR symbolic-link payload. The QA also requires cancellation to fail
closed, create-only JSON, zero C# compile errors, exact real Unity export and
byte-for-byte original vendor source/GUID identity. Fixtures and private
scripts are never customer archive contents.

Current test evidence lives under
`/data/var/marketplace-account-setup/unity-20261121-wave50/`. Actual native
results must be checked per installed Unity version before filling the
release acceptance ledger; a unit test alone is not proof of buyer import.
Prior failed QA outputs are retained as negative evidence. GUI real screenshot
acceptance remains an independent gate due the earlier Unity Software Terms
consent dialog and isolated Editor crash; do not fake images or bypass consent.

The most important next action after engineering is market validation of
actual budget-owning Unity publishers and measured buyer time saved versus
available free tools; no unapproved outreach, listing or sale is authorized.

## Actual native results and negative regression, November 21 later wave

The original Unity project contained a parser regression at its first native
run: real Unity `ExportPackage` stores the root TAR directory as `./`, which
was not initially accepted after path normalization. That was repaired. A
second native negative input proved that stopping at the two TAR zero blocks
could incorrectly accept a gzip stream truncated after the TAR marker. The
reader now consumes the complete decoded stream and independently verifies
the **CRC32** and **ISIZE** values from the actual final GZIP trailer. Both
failed first-run diagnostic logs are preserved, not disguised as passes.

Fresh, **independent real** Unity author/export and buyer-import acceptances
using the corrected exact source passed in installed Unity 2022.3.22f1 and
Unity 6000.6.8f1. Each version had **eleven real native PASS checks**:
reading the original five/six-asset release archives; identifying one new
asset and two changes to original source bytes under preserved GUIDs;
identifying a deliberately changed original GUID as potential serialized
reference breakage; refusing forged metadata GUID, path traversal,
truncated GZIP, symbolic link and canceled scan; create-only JSON export;
unchanged input package SHA-256s; and presence of the actual original Editor
window and scanner in the imported buyer project.

The exact real Unity-created customer archives have **six vendor paths and
two original Editor C# scripts** with unchanged byte-for-byte original
source and GUID metadata. Verified private immutable artifacts:

* `.../unity-20261121-wave50/native-2022-3-22f1-final1/`
* `.../unity-20261121-wave50/native-6000-6-8f1-final1/`

Each directory contains the actual `hpr-unitypackage-archive-preflight-candidate.unitypackage`,
source-scope verifier receipt, separate native author/buyer Editor logs,
create-only JSON comparison and matching eleven-check QA receipts. The
`negative-archive-fixtures/` directory contains original isolated malformed
archive fixtures, not copied customer content. The source regression suite
for all current Unity Python tests returned **four hundred forty-six PASS**.

Despite these genuine imports, **normal graphical Editor screenshots are not
approved**: prior isolated Unity 2022 GUI crashed before displaying the
product, and Unity 6000.6 displayed owner Software Terms consent. Neither
incident was bypassed. The new tool is intentionally offline, limited to
classic `.unitypackage`, and has no automatic repair or entitlement migration
support. All marketplace, legal, pricing, rights and buyer interview gates
remain open; no external publication was performed.

## Final documented buyer archive and official local validator evidence

The customer-facing README was expanded with genuine **documentation**: the
order of previous/current release selection, how to interpret each warning,
create-only JSON export, `INCOMPLETE` cases, and why the user must prove
compatibility in a populated disposable Unity buyer project. The buyer
archive source changed only in its first-party documentation; the C# scanner
and window source remained the same real Unity-tested implementation.

The exact revised documentation package then completed **fresh Unity author,
export, independent buyer import and eleven native checks** in installed Unity
2022.3.22f1 and Unity 6000.6.8f1, without source/metadata GUID mismatches.
Actual two-version buyer receipts and source byte checks are saved privately:
`/data/var/marketplace-account-setup/unity-20261121-wave50/native-2022-3-22f1-docs2/`
and `native-6000-6-8f1-docs2/`. Earlier `final1` native results remain separate,
and initial parser-negative cases are not overwritten.

The producer additionally installed the **same revised 2022-compiled package**
into a brand-new disposable Unity 2022.3.22f1 project with locally installed
Unity Asset Store Tools 12.0.0. Its actual counted validator receipt is:

* `status: RanToCompletion`, `hadCompilationErrors: False`
* `testsReturned: 34`, `testsPassed: 33`, `testsWithIssues: 1`
* The sole warning is **Check Demo Scenes**: no valid demo scene under the
  package's Editor-only root. The earlier documentation-content warning is
  resolved. No file was uploaded or Publisher Portal action performed.

The AST test's missing-scene check expects a scene containing game objects
or a designated UPM sample. A standalone archive file comparer does not use
scenes. Adding an unrelated primitive scene to game the validator would be
misleading to customers; the author intentionally preserved the honest warning
for seller/marketplace review. Therefore **do not describe the product as
validator-clean or approved**. The actual machine result is retained at
`/data/var/marketplace-account-setup/unity-20261121-wave50/archive-official-ast-2022-docs2/asset-store-tools-results.txt`.
The official installed AST version had earlier failed to compile in Unity
6000.6 due obsolete AST APIs; the new tool itself completed independent
Unity 6000.6 author and buyer compilation, which is different evidence.

A materially stronger new competitor check: the Unity Asset Store's actual
**PackageLens - Package Import Review Tool** is listed as **FREE**, version
1.0.0, dated June 4, 2026; it specifically previews incoming `.unitypackage`
changes and conflicts versus an existing project. This undermines the paid
standalone business case more than a generic feature-overlap claim. The new
HPR tool compares two actual archives rather than incoming archive vs active
project, but no seller demand, premium price or paid conversion data has been
obtained: https://assetstore.unity.com/packages/tools/utilities/packagelens-package-import-review-tool-375592

A recently published $14.99 promotional/regular $29.99 generic Build &
Dependency Analyzer illustrates the low-dollar utility category, **not
verified purchases**. Unity's official publisher FAQ states the developer
retains 70% of gross Asset Store sales, before taxes/support/marketing; this
does not predict sales. Self-reported November 15 small-publisher results
include zero-sale and low-visibility experiences, while some established
publishers report better outcomes. These anecdotes are nonrepresentative and
should not be multiplied into fabricated revenue forecasts:
https://assetstore.unity.com/packages/tools/utilities/build-dependency-analyzer-413664
https://marketplace.unity.com/publishing/publish-and-sell-assets
https://www.reddit.com/r/Unity3D/comments/1xwpb73/

Current technical opportunity is to **combine genuinely tested archive
upgrade, installed-asset boundary and buyer-preservation capabilities** into
a high-quality publisher preflight bundle if a paying budget owner is later
verified. Avoid creating more low-value overlapping SKUs and avoid product
publication until legal/AI provenance, UI screenshots, compatibility, existing
seller standing and actual buyer willingness are independently supported.

## First-run example and larger production archive acceptance — wave fifty-one

The initial private Archive Preflight buyer source had a first-run obstacle:
customers were required to find or export **two outside `.unitypackage` files**
before seeing any result, despite the Editor window compiling and passing
negative parser tests. The producer corrected this with a **three-archive
first-party instructional example**, created as real Unity 2022.3.22f1
exports of original plain-text assets, NOT synthetic TAR files, not third-party
product content, and not a reported Unity engine defect. It now ships under
`Assets/HPRArchivePreflight/Samples/` with stable original vendor `.meta`
GUIDs and two clearly labeled one-click Editor actions.

A buyer can choose **Try example: additions only** to compare the original
three-asset demo package against a Unity-exported four-asset additive revision,
which preserves all prior paths, GUIDs and asset source bytes. The result is
`ADDITIONS_ONLY`. **Try example: replaced GUID** compares the original demo
against an intentionally altered source `.meta` GUID for one README file;
result `REVIEW_POTENTIAL_REFERENCE_BREAKAGE`. The sample is a human-readable
teaching case and should never be advertised as spontaneous Unity corruption.
Both actions invoke only the existing read-only archive scanner. No sample
import, project change, network request or automatic repair occurs.

The original private exporter had a test-fixture scope error on the first
baseline export, before creating any archive. The failed log was retained;
a corrected asset inventory check resumed that precise failed private phase
without overwriting a prior effect. The two remaining archive variants were
created in fresh disposable Unity author projects. Exact SHA-256 values of
the three immutable real exports (pinned by source regressions):

* baseline: `cfce8257e52bb4cc393ee5fb6f09214efbe75a4a5cba537e0e2389340b9fae61`
* additive: `08d66b07a8555e578f42d0f1fe5774a8d9c1f1117d5cc7c792ee31c33cf2df63`
* intentional GUID change: `1fadaab248f09c68585c5268cca03050803e3008d349ed03f8c3a81769b00dec`

Original deterministic sample sources, actual Unity export logs and output
manifest are preserved privately under
`/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring/`.
A private installer verified original author asset hashes and meta GUIDs
before create-only copying to the owned product source. The entire source
pipeline and original byte hashes are also covered in the repository tests.

**Two separate real native acceptances passed** in Unity 2022.3.22f1 and
Unity 6000.6.8f1: each fresh author/export and newly created independent
buyer import passed **fifteen checks**, including parsing the three imported
training archives, expected addition/changed-GUID behavior, untouched
embedded sample SHA-256s, deliberately malformed original release fixtures,
and source metadata integrity. The real Unity-created buyer archives contain
**ten intended vendor paths**, two original C# Editor sources and three small
original Unity archive examples, with exact `.meta` and file bytes verified.
Private final source-stable receipts are under
`/data/var/marketplace-account-setup/unity-20261121-wave51/native-2022-3-22f1-examples-final1/`
and `native-6000-6-8f1-examples-final1/`.

A separate real-product stress exercise used the exact original **161-asset
HPR Gameplay Systems Suite** distribution (SHA-256
`28481398f239c6900511c96ad40f9b6f9be4f87ee143546384ce52478b41cb0b`).
Both installed Unity versions parsed all its source assets with strict TAR,
GUID, metadata and CRC checks, and identical-source self-comparison returned
`IDENTICAL_ASSET_IDENTITIES_AND_BYTES`. The archive was unchanged afterward.
Those private native receipts live under each preceding buyer QA directory's
`large-real-archive-evidence/`. This demonstrates one larger, realistic
package's compatibility, not all supported Unity archive variants.

**Graphical state:** an isolated Unity 2022 virtual display with new
`XDG_CONFIG_HOME` prevented the prior incompatible saved Editor layout
from reaching the same crash, but Unity instead showed a real **No valid
Unity Editor license found; please activate your license** prompt. The
three original unedited captures are stored privately under
`.../unity-20261121-wave51/gui-2022-isolated-preferences/`.
The first capture was independently inspected visually and shows the license
prompt above Unity's splash, not the HPR tool. No license state, terms,
account, publisher portal or owner preferences were changed or bypassed;
the producer's isolated display/process ended. Older GUI attempts remain
Unity 2022 startup crash and Unity 6.6 unaccepted Software Terms. **No true
product GUI image or buyer retail visual acceptance exists.** The vendor
screenshots cannot be fabricated, and a splash/terms dialog is not listing art.

Submission rules: Unity's current 1.1.f explicitly requests demonstration
sample assets for tools interacting with external assets. Section 2.2.a
restricts nested `.unitypackage` files that obscure most content; these
three tiny originals are clearly supplemental demonstration inputs for an
archive inspector and do not conceal its source, but publisher acceptance
has **not** been obtained. Section 1.6.a requires truthful AI assistance
disclosure for any functional part of the package generated with AI. This
project's new C# code and instructional source were drafted with ChatGPT
assistance, integrated into the owner's first-party repository, and tested
in actual installed Unity. The single seller must disclose that assistance
accurately and verify ownership, third-party IP, business/legal and license
terms before any public submission. A private source release is not an
Asset Store sales authorization.

Primary current official rules:
https://assetstore.unity.com/publishing/submission-guidelines

### Final exact sample-equipped package: official validator results and limitations

After adding the genuine first-party nested `.unitypackage` training inputs,
installed Asset Store Tools 12.0.0 was run **offline** against the actual
new, independent Unity 2022 buyer import. The counted result is
`RanToCompletion`, `hadCompilationErrors: False`, **32/34 PASS**, two warnings:
**Check Compressed Files** detects the three transparent nested Unity
training archives and requires explicit adherence to the official nested
archive policy, and **Check Demo Scenes** reports no scene (now also lists
nested package files). Neither result has been suppressed or renamed, and no
sham demo scene was introduced for a tool that reads files. The exact
nonpassing receipt is private at
`/data/var/marketplace-account-setup/unity-20261121-wave51/archive-official-ast-2022-examples-final1/asset-store-tools-results.txt`.

Previously the archive preflight without training inputs returned **33/34**,
with only the scene warning. The extra warning is a real tradeoff against
improved buyer onboarding, not a change to the scanner's source integrity.
The three original compressed training files total only **2,419 bytes**,
far less than a fifth of the original C# functionality bytes, and are
plainly documented as samples rather than hiding the product implementation.
Still, section 2.2.a is assessed by Unity's human reviewers; **this does
not establish approval or a legal exception**. The sole seller should
present a truthful supplementary-file rationale or distribute samples
separately if the actual reviewer rejects bundling them. Do not silently
convert them into a hidden misleading file type to game a validator warning.

The final product screenshot gate is also **unresolved**. A fresh, isolated
Unity 2022 GUI startup with new owner-private XDG configuration was unable
to open the product: the actual screenshot shows Unity's splash plus the
modal **"No valid Unity Editor license found. Please activate your license"**.
This differs from the earlier real crash when the owner's regular layout
contained Unity 6000 settings, and from the separate Unity 6000.6 Software
Terms dialog. The isolated GUI worker made no license activation, software
terms decision, account change or actual Unity Editor tool screenshot.
The original screen captures are private at
`/data/var/marketplace-account-setup/unity-20261121-wave51/gui-2022-isolated-preferences/`.
The visible preview derivative, if present, is solely for private inspection
and is NOT approved marketing artwork.

An additional genuine safety acceptance checked the same reader on the real
161-path flagship HPR Gameplay Systems Suite archive under both installed
Unity Editors. Each returned strict readable status, an identical same-file
GUID/path/source comparison, and unchanged input archive SHA256, with
independent native logs. This closes only that larger-file fixture's
compatibility gap, not Universal TAR/UPM support or GUI usability.

The latest source and test improvements were generated with assistance from
ChatGPT and must be disclosed in the eventual Unity Asset Store AI description
field, identifying functional generated source and substantial real native QA
work. The source is not based on third-party private commercial code, but
first-party status is not a complete IP/legal clearance. No external account,
customer, royalty, software-terms or marketplace effects were performed.

## Independent-package coexistence — new technical scope, November 21 later

A credible user problem is independent Unity Asset Store packages overriding
one another despite distinct store SKUs or renamed folders. One developer's
August/September 2025 discussion described different asset packs from one
publisher importing under colliding GUIDs, where both apparent pack roots
existed but content references resolved to the wrong pack. The participants
warned that renaming a folder does not change the GUIDs, and changing GUIDs
can break existing prefab references. This is directly relevant to buyers,
but the discussion is **anecdotal**, not evidence of a paying market:
https://discussions.unity.com/t/asset-packs-from-the-same-publisher-all-override-each-other-any-ideas/1682115

The first HPR Archive Upgrade Preflight implementation had only a
**replacement-version** comparison. If an original asset moves to a new path
with the SAME GUID, an *upgrade* can be a legitimate migration with separate
path-based loading risk. If two independently sold packages both claim that
GUID at different paths, installing both risks a shared-GUID collision. The
same input therefore requires **different semantics** depending on the
customer's actual workflow. Treating upgrade results as generic
multi-package compatibility would be misleading.

The original Editor candidate now offers two clearly distinct read-only
modes in the same window. **Review an UPGRADE** retains its existing
old/new replacement identity, source and importer behavior. New **Check
COEXISTENCE** checks two independent packages expected in the same project.
Its three explicit finding categories are
`GUID_REUSED_AT_DIFFERENT_PATH`, `PATH_REUSED_WITH_DIFFERENT_GUID`, and
`SHARED_GUID_PATH_DIFFERENT_BYTES`. Exactly identical shared asset identities,
paths, source bytes and importer settings are counted as shared overlap,
not falsely reported as collisions. Every incomplete/malformed archive,
invalid serialized caller snapshot, truncated finding cap or canceled scan
remains `INCOMPLETE`, never a positive pass. Each mode uses create-only JSON
export and never imports, rewrites, remaps or downloads any asset.

The user's three original Unity-exported educational examples now include
a **third one-click coexistence demonstration**, using the same baseline and
intentionally changed-GUID sample at the same asset path. That example is
clearly labeled as educational, not a Unity engine bug or third-party pack
evidence. No new nested sample archives were added to the customer package.

A *different* private test fixture was created as a genuinely exported Unity
2022.3 package, with one original first-party text file renamed while
retaining its original `.meta` GUID, contents and metadata bytes. The actual
Unity `AssetDatabase.ExportPackage` output has three strictly verified assets;
its private independent SHA256 and original source identity checks are at
`/data/var/marketplace-account-setup/unity-20261121-wave52/real-moved-guid-fixture/verified-original-move.json`.
This real fixture discriminates a path migration in upgrade mode from a GUID
collision in independent-package coexistence mode. Testing a moved path does
not establish how the Unity importer would resolve the collision if a buyer
actually installs both; separate disposable buyer import observation is an
appropriate follow-up.

Competing commercial tools remain a risk: the free PackageLens already checks
incoming packages against a project's installed assets, while Odin Validator
and Asset Validator offer more general package/project validation. A
publisher-targeted two-archive comparison is narrower and somewhat distinct,
but it cannot justify a new standalone paid SKU without credible buyer
willingness-to-pay evidence. The feasible strategic choice is to improve the
existing first-party preflight bundle, not multiply thin listings, and to
retain the one shared seller's authority over storefronts and price. Official
Unity 6000.3 publisher instructions continue to say paid UPM products are
not yet supported, so a paid offer may need classic `.unitypackage` while
the platform evolves; this is not evidence the user's seller account was
approved or is currently eligible.

Sources:
https://assetstore.unity.com/packages/tools/utilities/packagelens-package-import-review-tool-375592
https://assetstore.unity.com/packages/tools/utilities/odin-validator-227861
https://assetstore.unity.com/packages/tools/utilities/asset-validator-271338
https://docs.unity.com/en-us/engine/6000.3/manual/assets-and-media/asset-store/publishing/upm/submit

An adjacent future research candidate is Unity's manually edited FBX
Animation import settings not updating new source clips, reported in a
2026 developer discussion. The official manual describes why this occurs;
Unity's issue tracker may eventually add an import-refresh UI. This is an
interesting **technical** lead for the existing FBX inspector but currently
has insufficient independent buyer/payment evidence for another SKU:
https://www.reddit.com/r/Unity3D/comments/1o41nb5/

Any real GUI screenshots remain owner-consent gated by the earlier genuine
Unity activation/terms state; do not infer real visualization from batch
compilation or manufacture a screenshot. No external publication, product
sale, customer contact, software terms action, or irreversible external effect
was performed.

### Case-only asset-path false-negative and actual disposable buyer observation

Unity's documented `AssetDatabase.LoadAssetAtPath` API explicitly states
that its asset path argument is **not case-sensitive**, regardless of the
underlying host filesystem:
https://docs.unity.cn/6000.4/Documentation/ScriptReference/AssetDatabase.LoadAssetAtPath.html

An early independent-package coexistence implementation used ordinal,
case-sensitive asset-path keys. That was a potential **false negative**:
`Assets/HPRUpgradeExample/Example.txt` and
`Assets/HPRUpgradeExample/example.TXT` could be treated as unrelated,
even though Unity's lookup sees case-equivalent asset paths. The revised
independent comparer now catches `CASE_ONLY_ASSET_PATH_COLLISION` for case-only
paths with different GUIDs, while full-archive inspection and the
public comparer reject case-only duplicate paths *within* an individual
candidate archive as `INCOMPLETE`. This does not imply every such collision
will destroy data, only that simultaneous installation needs buyer QA.

A genuinely **Unity 2022 Editor-exported first-party case-only test archive**
with two files and one folder was created under private
`/data/var/marketplace-account-setup/unity-20261121-wave52/real-case-only-path-fixture/`.
It contains exactly one different-cased example filename, one original README,
one folder and a distinct documented GUID for the cased file. The QA
independently compared source text bytes, metadata GUIDs and path strings
against the earlier immutable original Unity-exported baseline. Its verified
SHA-256 is `2cb0d056bb76860a5030a22205c5d3ab2a79caadfe32f2fc35721426e6b06bfe`.
In native unit acceptance the case-only different-GUID collision is required
to flag exactly once, and malformed caller arrays with case-folded duplicate
paths are rejected. Such private fixture files are **not** nested into the
customer product; there is no added retail Asset Store compressed-file warning
from them.

Actual Unity 2022.3.22f1 observed buyer behavior was also captured, rather
than simply trusting the predicted warning. An original baseline sample
and the independent first-party *moved same-GUID path* export were imported
sequentially into a brand-new disposable real Unity project. Both filenames
were present after import, but Unity auto-assigned a **new GUID to the
incoming moved asset**, leaving the original GUID resolving to the original
filename. The exact observed GUID values and original input archive
SHA-256 equality receipts are private under
`/data/var/marketplace-account-setup/unity-20261121-wave52/actual-buyer-guid-collision-2022-3-22f1/`.
This independently demonstrates that a pre-import identity collision is real,
while also demonstrating that **a collision warning must not be described
as proof of customer data loss**. The precise outcome may vary with Unity
version, import conditions and existing project references; the tool never
changes customer identities automatically.

At the time of this source checkpoint the updated Unity 2022.3 native
**author/export and independent buyer** package completed **26/26 checks**
with exact 11 approved vendor paths, 3 Editor scripts and three original
small instructional archives. Its immutable QA is under
`/data/var/marketplace-account-setup/unity-20261121-wave52/native-2022-3-22f1-coexistence-case2/`.
The matching final Unity 6000.6 independent buyer result, last final Asset
Store Tools run and consolidated Git publication need their own actual
observed receipts before being reported as complete.

### Corrected dual-package coexistence release: two native buyer acceptances

The final source for the coexistence and case-insensitive path correction was
exported as a genuine native `.unitypackage` and imported into independent
buyer projects with Unity **2022.3.22f1 and Unity 6000.6.8f1**. Both installed
Editors passed **26/26 real native checks** each, including existing strict
archive/upgrade negative cases, the three original instructional archive
samples, independent overlapping package comparison, the actual first-party
Unity-exported moved-GUID and case-only-path fixtures, fail-closed malformed
caller arrays, create-only JSON reports and immutable input SHA-256s. The
archive source verifier found exactly **11 intended vendor paths, three
original C# Editor scripts and three original sample archives** with exact
byte and metadata GUID preservation. Native author, buyer import, exact
source verifier and private receipts are stored under
`/data/var/marketplace-account-setup/unity-20261121-wave52/native-2022-3-22f1-coexistence-case2/`
and `native-6000-6-8f1-coexistence-case2/`, with earlier 24-check native
receipts retained separately. Do not describe a Python test or a local Git
commit as substitute evidence for these actual independent Unity imports.

The **actual final Unity 2022 buyer package** was then imported into another
isolated project with installed Asset Store Tools 12.0.0 and checked offline.
Official counted result: `RanToCompletion`, `hadCompilationErrors: False`,
`testsReturned: 34`, `testsPassed: 32`, `testsWithIssues: 2`.
The two warnings remain **Check Compressed Files** (three truthful small
nested original Unity sample archives) and **Check Demo Scenes** (the
archive-reading Editor-only utility has no scene demo). They were not
suppressed. There were no reported C# compile errors, no Publisher Portal
submission and no retail review. The validator deliberately exits nonzero
when it finds warnings. Exact receipt:
`/data/var/marketplace-account-setup/unity-20261121-wave52/archive-official-ast-2022-coexistence-case2/asset-store-tools-results.txt`.

The original pre-import identity scanner, both explicit workflow modes,
and the case-insensitive asset collision detector remain **read-only**.
Publisher approval, real GUI screenshots, third-party rights and legal
licenses, actual buyer willingness-to-pay and authorized marketplace
submission remain separate open gates. The sole shared seller owns those
actions. The project producer has not fabricated screenshots or issued a
new owner-facing narrated report for routine internal engineering QA.

### Independent actual case-only import observed in both supported installed Editors

The publisher/purchaser compatibility question was independently observed in
**fresh actual Unity Editor buyer projects** by importing the original
baseline first-party `.unitypackage` and then the original real Unity-exported
case-only-path package, both in strict sequence. Unity 2022.3.22f1 **and**
Unity 6000.6.8f1 produced the same result in this particular controlled
example: `Assets/HPRUpgradeExample/Example.txt` was **absent from the physical
buyer project after the second import**, while the incoming lowercase
`example.TXT` file existed. Both `AssetDatabase.AssetPathToGUID` calls,
even when given the earlier filename capitalization, resolved to the
**incoming different GUID**, not the original. The actual AssetDatabase
listed the README and new lowercase example, not both filename variants.

The source input archive SHA-256s were checked before and after both test
runs, and the originals remained unchanged. This is **real Unity importer
behavior**, not a claim that any customer's project was tested or harmed.
Both observed receipts, actual logs and archive hash proofs are private under
`/data/var/marketplace-account-setup/unity-20261121-wave52/actual-case-only-coexistence-buyer-2022-3-22f1/`
and `actual-case-only-coexistence-buyer-6000-6-8f1/`. This confirms the
casefold preflight warning is useful in real Unity buyers; it does *not* by
itself establish that a prefab or saved asset reference was broken. A separate
first-party disposable **serialized buyer reference** experiment is needed
before asserting actual reference loss. Never advertise the tool as an
automatic repair for this collision, and do not conflate the file identity
result with guaranteed runtime correctness.

### Buyer-owned serialized-reference failure reproduced in two Unity generations

A strictly first-party, disposable buyer-project experiment **independently
reproduced a missing saved asset reference** in both the installed Unity
2022.3.22f1 and Unity 6000.6.8f1 Editors. This strengthens the case for
warn-before-import checking beyond a naming or cosmetic issue.

For **each** real Editor generation, an empty project was created; the
original baseline `.unitypackage` was imported; a private QA-only C#
`ScriptableObject` holding a `TextAsset` reference was created and saved
under `Assets/BuyerOwned/ExistingReference.asset`; its original target and
GUID were confirmed by `AssetDatabase`; and then a separately Unity-exported
first-party archive containing the **same path except for letter case** and
**a different GUID** was imported. A new independent Unity process loaded
the existing buyer-owned reference again. Before the second import the
saved reference was alive and resolved to `Example.txt`; afterward the
holder survived but its saved `referenced` field was **missing/null**.
The `AssetDatabase` mapped both capitalization variants to the incoming
asset GUID, while the first file was absent and the second existed.
Both original packages and the serialized buyer-owned holder retained
identical SHA-256 bytes before and after the test. The runtime meaning
changed **without any source-file bytes changing in the holder**.

The actual immutable input/evidence records are privately under:

- `/data/var/marketplace-account-setup/unity-20261121-wave52/serialized-reference-case-only-2022-3-22f1/`
- `/data/var/marketplace-account-setup/unity-20261121-wave52/serialized-reference-case-only-6000-6-8f1/`

The independently observed behavior is limited to these exact Unity
versions and intentionally conflicting first-party demo archives. It does
not assert that a specific third-party pack is defective or that every
GUID collision causes reference loss. It establishes a concrete compatible
failure mode which a buyer can check in advance using the archive-preflight
coexistence mode, without touching the buyer's actual project.

Additional public user evidence was located in the August 27, **2026**
Unity 3D community: an avatar user reported that importing a modified
third-party avatar `.unitypackage` overrides the existing project; a
suggested automatic re-export did not fix their situation. The account is
anecdotal and does not demonstrate payment demand for an inspector product:
https://www.reddit.com/r/Unity3D/comments/1vzslbx/importing_edited_project_overrides_existing/

Unity's current submission rules still leave the two warnings unchanged:
transparent nested training packages and no demo scene. Code and sample
inputs remain fully available, and no terms or Marketplace publication
occurred. Native **26-check author+independent buyer** verifications for
both Editors were completed, exact included paths/GUID/meta/source bytes
verified, with the larger archive tests retained from the preceding wave.
The entire current Unity source regression run passed **455 tests**.
The graphical preview gate is still unresolved due earlier real Editor
license/terms prompts. This is not an accepted retail listing or an
actual customer screenshot.

### November 21, 2026: competitive alternatives and next-product triage

Current public user pain is real but **payment conversion is not established**.
A September 2025 Unity buyer reported multiple purchased packs overriding one
another when imported together. An August 27, 2026 Unity3D user described a
modified avatar `.unitypackage` overwriting an existing project; their stated
re-export attempt did not solve the problem. Our *separate controlled Unity
buyer test* goes further on technical causality: in both installed Editors,
case-only path collisions produced a missing saved reference. None of these
facts establish actual willingness to purchase our tool.

The competition imposes a meaningful commercial constraint:

* **PackageLens** (June 2026) is **FREE**, and claims incoming-package vs
  current-project conflicts, selected imports, text/YAML diffs, snapshots and
  a demo/tutorial scene. This is a substantial free alternative to HPR's
  narrower **two independent archives** / **two versions of one product**
  comparisons. Its seven favourites are neither verified sales nor a revenue
  signal; do not describe the HPR product as the first or only solution.
  https://assetstore.unity.com/packages/tools/utilities/packagelens-package-import-review-tool-375592
* **Generic missing-reference fixers** are a crowded cheap category rather
  than a clear new high-margin independent product. The 2026 Smashy Tech
  Missing Reference & None Field Finder is advertised at **$4.99**, with
  two favourites and insufficient ratings; Missing Reference Fixer is
  advertised at **$9.99**, eight favourites, insufficient ratings. Multiple
  further competitors sell or give away similar reference/scene/prefab scans,
  including Asset Validator, Project Verification (free) and ProjectDoctor.
  Unity itself documents a hierarchy-search filter for missing asset,
  script and prefab references. Favourites, dates and listed prices do
  **not** imply paid transactions, demand volume or owner earnings.
  https://assetstore.unity.com/packages/tools/utilities/missing-reference-none-field-finder-384684
  https://assetstore.unity.com/packages/tools/utilities/missing-reference-fixer-316285
  https://assetstore.unity.com/packages/tools/utilities/project-verification-free-find-errors-in-your-project-333900
  https://docs.unity.com/en-us/engine/6000.7/manual/unity-editor/editor-navigating-managing/editor-searching/search-overview/search-by-provider/search-project-scenes/search-scene
* **Animation binding repair** has recent visible discussion: a September
  2026 Unity3D thread about low-framerate animation tangents has substantial
  engagement, and Blender-to-Unity FBX incompatibility appears in separate
  questions. However mature-looking competing tools already advertise
  automatic editable `.anim` binding path repairs, backups and recovery,
  including **AnimBinder** and **Animation Tools**. FBX-embedded read-only
  clips require a different workflow, and fixing generic animation behavior
  requires genuine engine/rig examples and much greater support exposure.
  These examples are **technical research leads**, not a verified new SKU.
  https://www.reddit.com/r/Unity3D/comments/1we75ar/
  https://assetstore.unity.com/packages/tools/animation/animbinder-368186
  https://assetstore.unity.com/packages/tools/animation/animation-tools-324462

**Priority ordered by evidence, expected owner workload and differentiation:**
(1) Preserve and harden the now independently tested **first-party archive
upgrade/coexistence tool** as part of an existing publisher safety suite,
with no speculative storefront sale claims; its concrete unique evidence is
pre-import two-archive comparison and the reproducer that destroys a saved
reference. (2) Investigate a differentiated **publisher release CI gate** for
repeatable archive-to-archive migration QA only after finding a publisher
budget/payment signal and comparing free CI/asset-validator alternatives.
(3) Retain FBX animation import diagnostic as a lower-priority technical
candidate requiring genuine Blender-generated reproductions and buyer proof.
(4) **Do not produce yet another generic missing-reference fixer**: free
built-in/editor alternatives and cheap competitors make an isolated small SKU
a weak use of production time. No defensible net revenue or owner-hours
estimate is currently possible because actual paid buyer numbers, fees,
support needs and conversion evidence are absent.

The single shared seller receives **authentic tested packages and open
retail warnings**, not approval to publish. A native test passes C# and
package import, but authentic GUI screenshots remain blocked by the actual
licence/terms state; no screenshot should be invented. Exact sources and
private test receipts are in the owning producer's private evidence path
rather than copied into public listings.
