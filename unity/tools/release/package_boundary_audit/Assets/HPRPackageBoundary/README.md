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
