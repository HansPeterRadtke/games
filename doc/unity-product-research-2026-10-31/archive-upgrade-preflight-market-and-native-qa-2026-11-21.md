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
