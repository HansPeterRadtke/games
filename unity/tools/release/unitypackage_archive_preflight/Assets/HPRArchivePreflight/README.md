# HPR Unitypackage Upgrade Preflight — original, unpublished Editor utility

This standalone **read-only** Unity Editor utility compares two existing
Unity `.unitypackage` archives **before** importing an update. Use
**Tools > HPR > Unitypackage Upgrade Preflight**, choose the previous and
proposed archive files, then click **Compare without importing**. The result
shows assets added, removed, moved or assigned different GUIDs, and separately
shows importer metadata and source byte changes where identity stayed stable.
Detailed warnings can be exported as a **new** JSON file, never overwriting
an existing receipt. No archive is imported, uncompressed to disk, rewritten,
uploaded or otherwise modified. No project settings are changed.

## Customer documentation: using the result before installing updates

This README is the user documentation for the first-party Editor utility.
You need two original `.unitypackage` files already on your own computer.
The tool does not download them or obtain any new Asset Store entitlements.

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
