# Private HDRP and URP co-installation validation — executable fixture, NOT YET RUN

Private test source: `HprSuiteDualPipelineHdrpMaterialValidator.cs`. This file is **not** in the buyer `.unitypackage`. It is a future Unity Editor acceptance fixture, not an Editor test that has already succeeded.

## Why this specific negative test matters

The former first-time authored demo material code chose the first discoverable URP Lit shader whenever any Scriptable Render Pipeline was active. When both URP and HDRP were installed, that could create wrong or pink sample materials inside a project using **HDRP**, even if the correct HDRP Lit shader was installed. The existing explicit adaptation action used a separate pipeline classifier; the corrected first-time creation path and conversion action now share the active-pipeline resolver and color adapter.

The new source helper uses the actual class name `UniversalRenderPipelineAsset` or `HDRenderPipelineAsset`, selects only matching Lit shaders, checks that the selected shader exists and is supported, and maps first-party demo colors to either/both `_BaseColor` and `_Color`. It refuses an unknown render pipeline or missing required shader instead of using the wrong installed renderer. A newly created material's color is validated before writing its asset into a Unity project.

The only completed tests so far are **offline C# source-method compilation and a Unity API stub**, with Roslyn syntax checks on the full original builder and the new private fixture. Those C# checks do not load Unity, render a scene, install URP/HDRP or prove visual compatibility.

## Future native acceptance, only after the current owner's existing Unity terms decision

Create a **fresh disposable** Unity 6000.6.8f1 host project, and intentionally install both URP and HDRP packages through the supported, authorized Editor workflow. Set the active Render Pipeline asset to HDRP using Unity's ordinary Graphics/Quality settings. Do not alter a customer's project, the owner's real baseline, shared caches or an existing foreign worker's active Editor session. Import the exact newly exported HPR Gameplay Systems Suite `.unitypackage` into the disposable host and confirm its first-party source identity, installer files and unique script GUIDs match the canonical current release source.

Copy the test fixture into a private `Assets/Editor` folder *outside the package* only after confirming that the selected project has HDRP active and the URP shader is discoverable. Set `HPR_SUITE_DUAL_PIPELINE_HDRP_RECEIPT` to a fresh **private, non-existing** receipt path. From the installed Editor, execute `HprSuiteDualPipelineHdrpMaterialValidator.Run`. It checks that there are at least nine original first-party materials, at least one actually needs conversion, and the active pipeline has not been changed. It executes the real explicit **Adapt Demo Materials** action and verifies that **every** first-party sample material uses supported HDRP Lit, retains authored base color, and that the example Unity scene and its metadata stay unchanged. It writes a receipt only after actual success and never uploads anything.

This fixture intentionally **fails** without an actual HDRP-active project and the additional URP shader. A successful offline C# compile is not the native acceptance receipt. After running the fixture, capture actual Unity Scene/Game/Player screenshots in a genuine HDRP target and inspect them for pink/black material artifacts, panel clarity, interaction availability and product usability. Also separately test a URP-active buyer project with the existing `HprSuiteUrpValidator.cs`. Confirm official Unity Asset Store validation and other submission requirements only with the one seller, subject to the owner's separate publication authority.

While the owner terms question `1f22d7f7fe0589d5cc83` is unresolved, **do not launch a new Unity Editor, bypass consent, install HDRP, claim this fixture passed or submit any product**.

## Producer evidence

Current source-level C# acceptance uses:
```sh
python3 -B qa/verify_pipeline_shader_offline.py /data/var/marketplace-account-setup/UNIQUE_PRIVATE_QA_DIRECTORY
```
The script reads **actual first-party C# method bodies**, compiles the extracted selector/resolver/color helper against local isolated C# simulated Unity types, and runs cases for Built-in, URP, HDRP, custom/near-match type names, missing/unsupported shaders and color properties. It parses the full current builder and this fixture under three Editor/preprocessor configurations using Roslyn. It also confirms that both creation and conversion call the shared selector and color helper, and that material color is validated before asset creation. It has no Unity Editor or network usage. Independent full Unity source tests must also pass before merging/pushing.

The prior, independently tested Built-in `.unitypackage` remains intentionally unchanged; the new source changes **are not packaged into it**. The canonical `validate_release.py` checks that an old archive differs from the new current Editor source and refuses to treat that old file as the corrected candidate. Only a newly exported exact-current package followed by true independent buyer import, native interaction and rendering tests can replace the prior private source artifact.
