# HPR Package Boundary Inspector

A read-only Unity Editor preflight tool for authors preparing a single-root
`.unitypackage` or considering a UPM migration. It reveals resolved asset
references that cross the chosen package folder boundary, explains where to
review dependencies, and exports an optional create-only JSON evidence report.

## Getting started

Open **Tools > HPR > Package Boundary Inspector**. Drag the package's own
folder (such as `Assets/MyTool`) to **Top-level package folder**, then click
**Scan dependency boundary**. Examine `EXTERNAL_ASSET`, `UNITY_PACKAGE`, and
`THIRD_PARTY_PACKAGE` findings before exporting. A report is not a validator
pass or a substitute for a clean-project install. The scan does not change
assets, project settings, package manifests, or runtime behavior.

## Dependency review

`EXTERNAL_ASSET` means an inspected asset references another asset under
`Assets` outside your export root. Bundle only content you own, or declare
and verify the external dependency. `UNITY_PACKAGE` means a built-in Unity
Registry package; check its declared version and fresh-project install.
`THIRD_PARTY_PACKAGE` needs explicit publisher and rights review. Unrealized
or dynamic loads and *missing* serialized references are **not detected** by
this tool. When a result says `INCOMPLETE`, it is never evidence of safety.

The scanner is intentionally limited to ten thousand assets and fifteen
hundred stored findings per scan and fails closed on truncation. It uses the
Editor `AssetDatabase.GetDependencies` API and does not claim those resolved
references are all runtime requirements. The report contains project asset
paths; consider sensitive project naming before sharing it.

## Compatibility and release scope

Editor-only C# and built-in Unity Editor APIs, no optional assemblies or
runtime components. Developer-native import and usability testing on targeted
Unity versions are required before sale. This independent product is *not*
the separately authored Input Readiness / Animator Contract preflight suite.

## Rights and support

Original HPR-authored source; see the accompanying LICENSE.md. No third-party
code or purchased Asset Store content is redistributed. There is no upload,
account access, automatic asset repair, destructive cleanup, or telemetry.

## Before/after upgrade identity review

First scan the **existing** version of your package and export a fresh JSON
snapshot containing the versioned stable asset-path and GUID inventory.
Then import or stage a proposed update in a separate disposable project, scan
its *same* top-level folder, and choose **Compare previous JSON scan for
safe-upgrade review**. The comparison distinguishes removed assets, same-path
GUID replacements, moved paths with preserved GUIDs, and additions. It refuses
to report a safe result when either scan is incomplete, snapshots are invalid,
paths are duplicated, or the previous/current top-level folder differs.
Upgrade comparison is also exportable to a separate, newly created JSON file.

A replaced GUID or removed asset can break serialized references in users'
existing projects even though a fresh installation compiles. Moved paths with
the same GUID often preserve Unity serialized references, but path-based
loading and code may still break. An unchanged GUID inventory is **not** a
compatible release guarantee: file bytes, public APIs, import settings,
missing serialized references, runtime behavior, and other asset-store
requirements still require independent real-project testing. Existing old
reports without a supported versioned GUID inventory are intentionally not
comparable, rather than silently guessed to be safe.

For large assets, the Editor shows a cancelable progress panel with the number
of assets processed. A canceled scan is marked incomplete, never clean.
The scan is capped at ten thousand assets and fifteen hundred dependency
findings; a comparison also caps stored changes at fifteen hundred. These
limitations are visible in the audit report.
