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
