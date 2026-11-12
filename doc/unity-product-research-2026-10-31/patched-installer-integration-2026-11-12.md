# Patched Unity Editor and ability installer integration

On November 12, the current commercial archive built with Unity 6000.6.8f1 contained 160 asset paths and omitted the ability installer. The separate installer archive contained the tool, but its builder still defaulted to an older Editor. An automatic Git merge of the two branches succeeded, yet the combined builder crashed on startup because it used `sys.path` without importing `sys`.

Commit `f9f01607dc5c9adf32a11c984f0a8fee273fcfcf` combines both histories and fixes the startup error. The source manifest records the Editor version verified by the build and records a null value when the historical QA override bypasses that check. The buyer quick start now names both components for HPR Stats and identifies `HprSuiteAbilityPool` as the component to select.

## Results on Unity 6000.6.8f1

| Check | Observed result |
| --- | --- |
| Default build and fresh import | The installed Editor exported and imported 161 asset paths. All 133 file payloads matched the committed sources. The fresh import matched all 161 metadata files and GUIDs. |
| Existing archive comparison | The commercial archive failed validation on the missing installer. The integrated package kept all 160 original GUIDs and metadata files. Against the previous installer archive, all 161 GUIDs and metadata files matched. Only the README and quick start changed contents. |
| Showcase and installer | The imported installer compiled, all thirteen showcase bindings resolved and eleven runtime integration checks passed, including save-slot integrity. |
| Buyer’s existing player | Copying the ability and effect created independent identities. The guide refused to overwrite a copy at an occupied destination. Attach, Undo, Redo and scene reload retained the controller and its native Stats binding. Healing changed health from 40 to 60, spent twenty stamina and blocked an immediate second cast. |
| Upgrade from the previous patched commercial archive | The same project passed six Play checks before and after the upgrade with domain reload disabled and a customer resource provider. All fifty protected files matched their baseline after the first Play run, immediately after the upgrade, and again after the final Play run. |
| Regression suites | All 365 branch tests passed. A disposable copy with the pending commercial changes passed 367. The native Unity Test Runner passed all 56 EditMode cases across ten assemblies on this exact archive. |

Immediate Play on the native Stats fixture logged an `ArgumentOutOfRangeException` from Unity Search startup indexing. The six gameplay assertions passed. The upgrade tests waited for Editor startup to settle. Both of their Play logs were free of that exception. The rendered installer workflow, URP appearance and final Unity 6.4 NUnit coverage remain open.

## Commercial checkout

The original checkout retained its fourteen pending files at `2a0e5a3`. A separate rehearsal applied the previously reconciled changes to this integration commit. Comparing all buyer file sources found three documentation differences in the rehearsal. All runtime sources, serialized assets and editor tools matched the tested archive. The private `commercial-local-edits.patch` reproduces the reconciled local work against the integration commit. A clean apply reproduced all fourteen expected files byte for byte. Thirteen paths needed changes. One already matched the branch.

The build, import, upgrade, NUnit XML, protected-file hashes and patch verification are on Nitro under `/data/var/marketplace-account-setup/hpr-patched-installer-20261112`. The internal archive SHA-256 is `d87f2d5e6e68e6c460aed87fc976984434a738e9d11c8fe4cba961095a568c10`. The specific checks are recorded in `archive-comparison.json`, `import-identity.json`, `prior-customer-results/`, `nunit/RESULT.json` and `verified-run.json`.

## Running the showcase against an exact release

Run `validate_cleanroom.sh` and then `validate_playmode.sh` from `unity/tools/release/gameplay_suite/`. Set `HPR_SUITE_RELEASE_ROOT` to the directory holding the candidate archive and its builder receipt, and `HPR_SUITE_CLEANROOM_PROJECT` to a fresh project path. Keep both settings for the two commands. The Play receipt identifies the tested archive by SHA-256 and records the Editor version, project and native log. The runner preserves previous receipts.

The old scripts defaulted to different imports. The import runner selected v2 with 151 asset paths. The Play runner selected v6 with 156 paths. Nineteen shared files differed. In a separate test on the current package, replacing just the imported README with its previous version preserved every GUID. The old runner still reported all eight Play checks as passed in Unity 6000.6.8f1. Commit `f50c761363a14a3ce3c968910e31a2d748220250` rejected that same project before starting Unity or writing its QA helper.

A fresh import of the archive identified above passed eleven runtime checks and all eight native showcase Play checks. After Play, all 133 package files, all 161 metadata files and their GUIDs matched the archive. The customer-project test also passed all eight checks and retained all 46 protected files. The old immediate-start control logged a Unity Search startup exception. Both successful runs that waited for Editor startup were free of that exception.

All 375 branch tests passed. The rehearsal with the pending commercial edits passed 377. The private logs and machine-readable results for this increment are on Nitro under `/data/var/marketplace-account-setup/hpr-playmode-identity-20261112`, including `verified.json` and `fresh-release/actual-playmode-receipt.txt`.

## Commercial branch acceptance for the revised buyer package

The old NUnit template check matched all 55 C# files in an earlier import even though its README, quick start and architecture guide differed from the selected release. The revised driver checks every archived file, complete importer metadata and GUID in the template, again in the disposable project before starting Unity, and once more after NUnit exits. The identity check reads and hashes the same archive bytes even if a concurrent writer replaces the file. The earlier import now fails before the driver creates a test directory. In a separate regression, a passing NUnit fixture with a newly introduced vendor asset correctly produces a failed package result.

On Unity 6000.6.8f1 the real Test Runner passed all 56 EditMode cases across ten assemblies on the revised archive. The XML case names and their assembly memberships matched the previous native run. After Unity exited, all 161 asset paths, GUIDs and metadata files and all 133 payloads matched the selected archive. All 133 payloads were independently compared with the product source, including the release builder's documented transformation of the ten module READMEs.

The source suite passed 383 tests. The commercial rehearsal passed 385 with all fourteen pending local files overlaid from the verified patch. The previous commercial tip `209c33a708c55fd21f7aff462cb6b6eed5bfe243` is a direct ancestor of this integration. All intervening file changes are confined to the Unity suite, its ability module, tests and project QA documentation. The original checkout at `2a0e5a3` retains its original fourteen local files.

The tested internal archive SHA-256 is `d948a746850d4c45bffa4617fc8a704c7b1ed73f5c80865fe5a3bc9cbb3934bb`. Nitro retains the native XML, package identity report, previous-template rejection and source test logs under `/data/var/marketplace-account-setup/hpr-commercial-nunit-20261112`. Rendered installer and URP acceptance and the final Unity 6.4 NUnit run remain open.

## Removing a runner required by an existing player controller

On Unity `6000.6.8f1`, the previous package offered to detach the runner from a player whose controller inherited a `RequireComponent` attribute naming the runner in its third slot. Unity logged that the controller depended on it and kept both components. The installer nevertheless returned success.

The installer now names the dependent component during preview and rejects explicit removal before opening an Undo group. The fixed package preserved the disabled controller, its runner, the clean scene and the original Undo group. On a second player, removal preserved its collider, Undo restored the runner's configured effect origin, and Redo removed only the runner. The scene file stayed byte-identical until explicitly saved. Reloading that save retained both players' intended component sets.

To reproduce in a disposable imported project, place `qa/RunnerDependency/BuyerCastingController.cs` in a runtime Assets folder and `qa/RunnerDependency/RunnerDependencyVerifier.cs` in an Editor folder. Run `HPR.Qa.RunnerDependency.RunnerDependencyVerifier.Run` with the Editor in batch mode. It creates its own scene and refuses an existing fixture path.

The private archive built from `1fe25583a806d95aa1225dc7d86054d156998e7e` has SHA-256 `9640f2a08a0b3e4db3e6abd68fdcdbc6ccc51134e7cc9c3c5bdeb717f2aea533`. Clean import, the runtime smoke test, showcase Play Mode, all 56 native Edit Mode cases and the packaged dependency fixture passed. The installer and quickstart were the only changed asset payloads. All 161 paths retained their GUIDs. The branch passed 383 source tests. A disposable copy with the owner's existing changes passed 385. Nitro stores the paired native logs and archive identity receipts in `/data/var/marketplace-account-setup/hpr-runner-dependency-20261112`.
