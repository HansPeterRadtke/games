# Selected installer archive — incomplete URP 17.6 / new-input-only import

November 1, 2026. Actual private Nitro Unity Editor 6000.6.7f1.

**Status: TECHNICAL ACCEPTANCE FAILED FOR THIS DISPOSABLE URP IMPORT.** This cannot be presented as a passed exact-archive URP check.

## Setup and actual failure

A new isolated disposable project was copied from a historically verified Unity 6.6 URP 17.6 / Unity Input System 1.20.1 new-input-only customer project. Its ProjectSettings specified activeInputHandler 1. The current package is the real frozen **161-asset** selected-installer internal .unitypackage. Before attempting upgrade, an independent full original-data baseline captured **sixty** nonvendor Assets, ProjectSettings and Packages files with SHA-256 hashes.

A real Unity 6000.6.7f1 -batchmode import of this exact archive ran under an explicit **600-second limit**, but did not complete Unity's existing project ILPP/Bee compilation stage. The tool reported exit **124 (timeout)** after about **602 seconds**. The private Unity log ended with the Unity bee_backend and Unity.ILPP.Runner stages and internal duplicate-hint-path warnings. There were **no recorded HPR C# compiler errors**, but the archive was never successfully imported and those compiler results cannot be claimed as a pass.

After exit, the incoming Editor source, Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs, was **absent**. A separate complete read-only SHA-256 verification against the original customer baseline returned **CUSTOMER_INTEGRITY_PASS 60**, confirming no existing customer assets or project settings had been changed by this failed attempt. There was no force-retry, reset, deletion or re-import of this uncertain project.

Original log: /data/tmp/hpr-caltask2fb-selected-20261101/urp-newonly-exact-import.unity.log.
Prior version-fifteen internal URP import on another copied test project had similarly timed out during Unity ILPP before the new archive import. This is now repeated evidence of a **test-fixture/toolchain blocker**, not an established specific Unity engine root cause or a product bug.

## Related but weaker positive evidence

The exact selected-installer candidate **passed**:
- Real Unity 6.6 fresh cleanroom, thirteen scene refs, twelve supporting assets, and ten runtime/save integration checks.
- Real Unity 6.6 customer import with all fifty-nine original files preserved.
- Actual installed Editor installer UI and attach/Undo/Redo/Inspector persistence check.
- Unity 6.4 import, preserving twenty-seven pre-existing files.
- Unity 6.6 double Play-mode entry with domain reload disabled.

Earlier v14 URP 17.6 and new-input-only Unity gameplay tests passed when private test keyboard focus behavior was configured explicitly for headless Editor. An independent current tar audit verified **all eighty shared runtime, scene, material and ScriptableObject files byte-identical** between the last actually verified URP v14 and the new installer-enabled archive. The only changes were buyer guide/docs and the new Editor-only installer. These are useful continuity/provenance findings, **not** a substitute for the missing exact-archive URP test.

## Safe next check and commercial decision

Do not blindly repeat work against this potentially inconsistent copied Unity Library. A separate fresh URP project with a new project path and clean Library, or a fresh imported project that receives URP through its own configured package manifest, should be verified under a bounded resource budget. It should import the same frozen archive, then test the real pipeline activation, material adaptation, complete scene/camera rendering and the actual new-input-only gameplay transitions. Keep the original failed log, snapshot and archive immutable.

No provider accounts, uploads, publications, purchases or source changes were made. The product remains **commercial NO-GO** due missing independent buyer-value validation, even if this technical gate is later passed.
