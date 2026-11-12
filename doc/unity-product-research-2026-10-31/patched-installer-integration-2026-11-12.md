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
