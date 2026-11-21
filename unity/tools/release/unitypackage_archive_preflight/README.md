# Unitypackage Archive Upgrade Preflight — private original product candidate

An isolated Editor-only publisher/buyer pre-import safety preview: two actual
`.unitypackage` archives, strictly bounded read-only TAR.GZIP inspection,
metadata GUID/path/content comparison, fail-closed warnings and create-only
JSON export. No Unity AssetDatabase import operation or guessed references.

The existing `package_boundary_audit` checks currently installed package
assets; this product instead checks **raw archived releases before import**.
It complements but does not replace existing buyer-package regression QA.
The strict archive interpreter intentionally refuses unusual/huge packages.
Only real native Editor and independent buyer installation receipts can
support compatibility. The package is not approved for retail or publishing.

Producer private QA belongs in `qa/` and never inside `Assets/`.
