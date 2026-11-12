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
