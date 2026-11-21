# Unitypackage Archive Upgrade Preflight — private original product candidate

An isolated Editor-only publisher/buyer pre-import safety preview: two actual
`.unitypackage` archives, strictly bounded read-only TAR.GZIP inspection,
metadata GUID/path/content comparison, fail-closed warnings and create-only
JSON export. Choose **upgrade** if one archive replaces an older version, or
**coexistence** to check two independently installed packages for reused GUIDs,
clashing asset paths and silent overwrites. These are deliberately different
checks: a valid migration move can be an independent-product GUID collision. No Unity AssetDatabase import operation or guessed references.

The existing `package_boundary_audit` checks currently installed package
assets; this product instead checks **raw archived releases before import**.
It complements but does not replace existing buyer-package regression QA.
The strict archive interpreter intentionally refuses unusual/huge packages.
Only real native Editor and independent buyer installation receipts can
support compatibility. The package is not approved for retail or publishing.

Producer private QA belongs in `qa/` and never inside `Assets/`.

## Buyer first-run demonstration (native first-party sample archives)

The original version required two outside `.unitypackage` files before a
buyer could see how the Editor window worked. The current candidate includes
three small real Unity-exported original instructional archives under
`Assets/HPRArchivePreflight/Samples`. The window gives one-click previews of
`ADDITIONS_ONLY` and an intentionally replaced GUID; there is no import
operation and no assertion of a Unity engine defect. The reproducible
first-party authoring scripts and pre-export source manifests are under
`qa/` with unique immutable private original export receipts. The archive
contains only the product's Editor sources, documentation, licensing notice,
and supplemental original training files.

Unity submission rules section 2.2.a restrict archives that obscure most
product content. Here the nested files serve directly as small, transparent
example input for an archive-comparison tool, but **official retailer review
is still required** and no legal or sales clearance is implied. Do not ship
a nested-archive approach if the official reviewer rejects it.
