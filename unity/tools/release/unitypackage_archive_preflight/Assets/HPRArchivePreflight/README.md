# HPR Unitypackage Upgrade Preflight — original, unpublished Editor utility

This standalone **read-only** Unity Editor utility compares two existing
Unity `.unitypackage` archives **before** importing an update, and can
independently check whether two unrelated packages have colliding asset
identities if both would be installed in the same project. Use
**Tools > HPR > Unitypackage Upgrade Preflight**, choose the previous and
proposed archive files, then click **Compare without importing**. The result
shows assets added, removed, moved or assigned different GUIDs, and separately
shows importer metadata and source byte changes where identity stayed stable.
Detailed warnings can be exported as a **new** JSON file, never overwriting
an existing receipt. No archive is imported, uncompressed to disk, rewritten,
uploaded or otherwise modified. No project settings are changed.

## Two different workflows — do not confuse version upgrades with coexistence

**Review an UPGRADE** means the second archive is a replacement version of the
first. The scanner checks whether old GUIDs and asset references survive, and
warns of changed source/importer data or removed assets. An old asset moving
under the **same GUID** can be an ordinary migration, though path-based code
may break.

**Check COEXISTENCE** means you want to install two *independent products*
**together**. The tool checks for **GUID_REUSED_AT_DIFFERENT_PATH** (two
unrelated paths claiming one GUID), **PATH_REUSED_WITH_DIFFERENT_GUID** (two
vendors claiming the same path with different GUIDs), and
**SHARED_GUID_PATH_DIFFERENT_BYTES** (the same GUID and path but incompatible
source or importer metadata). Exact shared identity, path, and all source bytes
are counted as identical overlap rather than reported as a conflict.
`NO_OVERLAP_CONFLICTS_IN_CHECKED_ARCHIVES` is a narrowly scoped identity check,
**not** a promise that the two packages safely import or run together. Always
verify in a disposable combined buyer project. A finding is not proof of a
Unity engine defect, and the tool never changes GUIDs or automatically
repairs third-party content.

A third teaching button, **Try coexistence: competing packages use the same
path**, compares the original baseline example with the deliberately changed-
GUID first-party sample. Its expected result is a path collision, **not** a
problem found in a purchased third-party product. Use the two separate buttons
for the actual selected archives rather than interpreting an upgrade review
as a simultaneous-install safety check.

## Customer documentation: using the result before installing updates

This README is the user documentation for the first-party Editor utility.
You need two original `.unitypackage` files already on your own computer.
The tool does not download them or obtain any new Asset Store entitlements.

### Try the included original examples first

You can also try the tool immediately without obtaining an outside asset.
Choose **Try example: additions only** to compare the included original
`Samples/HprExample-baseline.unitypackage` to
`Samples/HprExample-additions_only.unitypackage`. The expected result is
`ADDITIONS_ONLY`: one new example text asset, no changed existing path,
source data or GUID. Choose **Try example: replaced GUID** to compare the
baseline against `Samples/HprExample-changed_guid.unitypackage`; the result
should warn `REVIEW_POTENTIAL_REFERENCE_BREAKAGE` and name one intentionally
replaced GUID at a stable asset path. These three tiny archives were created
from original instructional text using the real Unity Editor ExportPackage
API. The GUID-change example is **deliberately constructed**; it does not
claim that Unity spontaneously changed GUIDs or prove a real Unity engine bug.
The sample archives are read only; the example buttons NEVER import them into
your active project. They are supplemental instructional files, not additional
sellable products or evidence that any arbitrary upgrade is safe.

First choose the **existing** archive currently represented in your game or
release history; then choose the **proposed updated** archive. The order
matters: removals and additions are counted relative to the older package.
Click **Compare without importing**. The overview separates historical
asset identities from additions, removals, GUID replacements, path moves,
full source-file changes and changes to the source `.meta` importer settings.
The detailed scroll area explains each affected path. Export a JSON report
to a NEW filename if you need a review receipt in CI or with a teammate.

`INCOMPLETE` means an archive is malformed, out of supported scope, too large,
truncated, unusual or the scan was canceled. It is NEVER a compatibility
pass. `REVIEW_POTENTIAL_REFERENCE_BREAKAGE` indicates an asset may disappear
or change its serialized GUID. `REVIEW_PATH_MIGRATION` indicates a stable GUID
but a changed asset path, which may break path-based code. `REVIEW_CONTENT_OR_IMPORT_CHANGES`
indicates unchanged identities with changed source or settings; investigate
whether APIs, internal fileIDs or import behavior changed. `ADDITIONS_ONLY`
indicates existing scanned asset bytes and importer settings were unchanged;
it is a limited identity preflight, not a runtime guarantee.

Before distributing a changed package, independently install the old version
into a disposable real buyer project with serialized references and customer
files. Then import the proposed version into that same clone, confirm that
reference targets and customer-owned bytes survive, and test actual play mode,
compilation, scene loading and declared render pipelines. Do not upgrade a
valuable live project solely on a green preflight screen.

Possible asset identity breakage is marked explicitly. Same GUIDs cannot prove
stable C# APIs, shader behavior, scene references to internal fileIDs, missing
third-party packages or safe runtime semantics. File changes need populated
buyer-project regression tests; this tool never auto-repairs GUIDs or
accepts software/storefront terms for you.

Strict safety: only standard Unity TAR.GZ format is accepted; nested or
unrecognized TAR paths, unusual member types, metadata GUID disagreement,
truncated TAR headers, invalid checksums, duplicated paths, and size or
asset-count caps result in `INCOMPLETE`, not a false clean result. The scanner
ignores `preview.png` content but limits its size. Archives above 512 MiB
compressed or 2 GiB decompressed are intentionally not supported by this
candidate; they need an independent, more scalable validator.

The private QA folder is not buyer content. The first-party source contains
no third-party implementation. Unity 2022.3 and Unity 6000.6 native
compilation, real-archive comparisons, and independent clean-import acceptance
are required before any retail claim. This is a technical candidate, not an
approved public Asset Store release.
