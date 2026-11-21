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
