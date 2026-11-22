# HPR Publisher Version Matrix — original Unity Editor candidate

## Documentation and purpose

This is a **read-only, Editor-only** tool for Unity asset publishers who need to compare what happened when the *same original package* was imported into two different Unity Editor versions. It records existing imported asset paths, stable Unity GUID identities, direct asset dependencies and the version of the Editor that performed the scan. It does **not** import, resave, upgrade, rewrite or repair any package or project asset. Its purpose is to expose specific differences that warrant follow-up, not to certify that every serialized field, scene, animation or runtime behavior is compatible.

## Prepare two independent buyer-like test projects

Use two disposable Unity projects, one created by each Editor version you need to support. Do not perform package upgrade experiments on a real customer's working project. In each project, import the same original `.unitypackage` by the normal Unity workflow. Confirm any compilation errors and ordinary warnings independently. Keep the original `.unitypackage` and its source files unchanged so both projects really examine the same vendor release.

Install this tool in both disposable projects. It is accessible from **Tools > HPR > Publisher Version Matrix**. No external Python runtime, network account, optional render pipeline, plugin, or game assembly is required for this source-only Editor workflow.

## Scan imported vendor assets and export evidence

In each project, copy the actual package root path from Unity's Project window, such as `Assets/YourPublisherAssets`, into **Original Assets root(s)**. For several top-level vendor folders, separate them with semicolons, for example `Assets/YourGameplay;Assets/YourSamples`. Use real paths; the placeholder is not an installed folder. Nested and duplicate folders are not accepted. Click **Scan imported publisher assets**. Missing roots, invalid paths, unsupported scan cases and too many assets must be treated as **INCOMPLETE**, never as a successful clean result. There is an upper limit of four thousand asset paths per scan. You can filter the visible list with **Find imported asset**, while the exported report retains the full scanned asset list.

When a complete, nonempty scan succeeds, click **Export NEW JSON compatibility receipt**. Choose a new filename and preserve it alongside your test logs. The tool refuses to overwrite an existing report. Repeat in the other Unity Editor and save a second JSON receipt under a different name.

## Compare the two saved receipts inside Unity

Choose **Tools > HPR > Compare Publisher Version Receipts**, or use the compare button in the scan window. Select the two existing JSON reports, then click **Compare imported paths, GUIDs and direct dependencies**. The read-only comparison requires the same exact vendor root set and two different recorded Unity versions. It refuses incomplete, malformed, duplicate or incompatible evidence. It identifies assets present in only one import, changed Unity GUID identities and changed direct dependency paths. Use **Find affected asset** to locate individual findings, or export the complete result to a **new** JSON file. Even when no metadata differences are detected, the verdict is only **MATCHED_IMPORT_METADATA**, not complete compatibility.

The separate `qa/compare_version_receipts.py` tool in the producer source tree is **private test infrastructure**, not a buyer dependency and not included in the first-party Unity archive. Buyer operation stays entirely inside Unity.

## How to interpret a finding, and what remains out of scope

A changed Unity GUID or missing imported file is a reason to investigate the exact source package, `.meta` files, cross-version serialization and any affected prefabs. The tool never guesses a correct replacement GUID or performs a mass resave. A changed direct dependency is a *signal for review*, not proof that a reference is broken. Confirm results against a separate real Player build and important scenes or assets in each supported Editor version before accepting a release. Internal serialized field values, script type identity, native plugins, animation playback, shader/URP behavior, Play Mode, future Unity versions and graphics are not fully tested by this metadata comparison.

The code and original first-party sources are supplied with a separate internal licensing-status file. No live customer assets, third-party packages, secret receipts or non-buyer QA fixtures should be redistributed. This remains a **private commercial candidate**, not an authorized Asset Store product: actual normal graphical Editor usability, truthful original screenshots, licensing rights, AI-assisted code disclosure, evidence of buyer demand and seller approval still have to be established. A generic optional demonstration scene is not bundled because this tool has no runtime scene behavior; its absence may produce a generic Asset Store Tools warning and is not disguised as a passing check.
