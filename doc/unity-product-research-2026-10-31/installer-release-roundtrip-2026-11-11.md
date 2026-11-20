# Gameplay Suite installer export and buyer upgrade, November 11, 2026

The release builder at `4fb0f2e` exported 160 paths and passed its own release check while omitting **Attach Ability to Selected Object**. The previous private gameplay package had 161 paths. The missing script had GUID `72050056e79458319827a82105e509c8`.

The release branch now stages the tested installer with that GUID, its same-object Stats binding, the guide’s independent ability and effect copies, and scoped saves for demo materials. A builder project from before the installer can acquire the new pair on explicit reuse. A conflicting GUID, modified script or orphaned half of the pair stops the build.

## Native results on Nitro

| Package and case | Observed result |
| --- | --- |
| Unity 6.6 source export, imported separately into Unity 6.4.0f1 and 6.6.7f1 | Both imports matched all 133 file payloads, all 161 metadata files and all 161 GUIDs. |
| Existing-player healing on each Editor | The guide assigned independent ability and effect identities and rejected an occupied destination. Attach, Undo, Redo and scene reopen preserved the customer controller and native Stats reference. Health rose from 40 to 60, stamina fell from 100 to 80, and cooldown rejected the immediate second cast. Both processes exited successfully. |
| Unity 6.6 native EditMode tests | All 56 NUnit cases across ten module assemblies passed, with 55 packaged scripts matching the archive. The driver reported zero unexpected changes to its 387 protected files. |
| Native Unity 6.4 export and import over a working Unity 6.6 customer game | The original 160-path package and the new 161-path package each passed the same six Play-mode checks with the customer's own resource bridge and domain reload disabled. All 50 customer assets, metadata, packages and project settings held their original hashes after import and after Play. |
| Built-in material adaptation | Unity saved the changed vendor material. The unrelated customer ability retained its unsaved value in memory and its original bytes on disk. All 46 protected files matched afterwards. |
| Final Unity 6.6 export from a copy of the old staging project | The importer added the missing installer, preserved all 160 shared GUIDs and loaded the compiled tool. All thirteen showcase bindings resolved. A separate partial-import project with only the installer and its metadata omitted still compiled and reported the exact missing script. |

The first immediate-Play tests on both Editors logged an exception in Unity Search startup indexing. The paired before-and-after upgrade test waited for idle startup and its Play logs contained no such exception. These observations cover batch Editor workflows. Rendered installer use and URP presentation remain open.

## Release and source verification

A controlled zero-exit exporter produced no new file and the prior builder nevertheless issued a success receipt for an older archive. A second control substituted a module implementation inside an otherwise valid package. The corrected builder validates a fresh file before replacing the named artifact, source manifest and hash-bound receipt. It checks all expected asset identities, all 55 C# sources, ten assembly definitions and the authored sample YAML. Both negative controls preserve the previous release.

The Unity 6.4 exporter wrote GUID directories prefixed by `./` and eleven preview images. The older checker reported duplicate GUIDs. The updated reader accepts both genuine layouts and still rejects duplicate normalized records, unsafe entries and malformed previews. The independent API compiler then exposed broken project-relative paths for relative CLI arguments. The corrected twelve-project build succeeded with zero errors and fifteen serialized-field warnings.

All 357 repository Unity regression tests passed at source revision `5180092b519e20da0afcf79a2ccc5c46c261d395`. Every one of the final Unity 6.6 archive’s 133 payloads was independently reproduced from that revision, including the transformed module READMEs. Compared with the Unity 6.4 export tested during the customer upgrade, the final archive differed only in the two Editor diagnostics scripts and the buyer README.

The final archive contained 460 non-null references within its serialized files and 85 between packaged assets. All 545 resolved to the expected object identifiers. The 85 packaged links targeted 22 scripts, 13 data asset references and 50 material references, counting repeated uses. Another 68 references used Unity built-in identifiers. The isolated commercial checkout matched the archive bytes for all 55 C# sources and ten assembly definitions. The object-by-object findings are in `serialized-target-objects.json`.

## Commercial worktree and remaining checks

The commercial worktree stayed at `2a0e5a3` with its fourteen original local changes. An isolated integration test exposed an old assertion requiring deletion during a partial sample copy. Its architecture text also promised rollback. The [commercial integration patch](patches/hpr-customer-copy-validation-2026-11-11.patch) aligns those two pending edits with the implemented recovery behavior. The historical two-file correction reproduced the tracked guide implementation from the owner’s snapshot. The reconciled copy passed all 359 Unity repository tests. The patches were applied only in disposable copies.

The broker declined a further clean-commit Unity 6.4 build, fresh import and NUnit run because resources were insufficient. That combined job did not start. A native Unity 6.4 export and functional customer Play run had already completed. Final-revision Unity 6.4 NUnit and rendered buyer acceptance remain open. The branch is separate from the commercial worktree.

## Evidence

Private Nitro evidence is under `/data/var/marketplace-account-setup/hpr-installer-release-20261111`. The final verified archive is `reused-staging66/release/hpr-gameplay-systems-suite-candidate.unitypackage`, SHA-256 `5e28470eff8110957fac46c903cbde682c5506f3d20052e331eefb859e941d7e`.

- `committed-payloads.json` maps every file to its Git source, payload hash and GUID.
- `customer64-results/`, `customer66-results/` and `nunit66/RESULT.json` contain native import, gameplay and NUnit evidence for the first corrected export.
- `prior-customer-results/` contains the before-and-after upgrade receipts, logs and protected-file hashes.
- `builtin-material-results/` and `layout-matrix/` contain material isolation and complete-versus-incomplete import results.
- `diagnostics-ci.log`, `commercial-final-ci.log` and `final-release64-broker.json` record the final source checks and the denied additional native run.
