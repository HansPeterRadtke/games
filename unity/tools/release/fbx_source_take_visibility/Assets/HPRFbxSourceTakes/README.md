# HPR FBX Source Take Visibility — read-only Editor candidate

## Documentation and first-use guide

This is the complete usage documentation for the first-party Editor window,
its bundled real FBX examples, its detection limits, its non-mutating export
workflow and manual troubleshooting of missing animation source takes.

When an FBX animation's clip list has been manually customized, Unity may not
add new animations automatically after the source FBX changes. This Editor-only
preflight compares source take names reported by `ModelImporter.defaultClipAnimations`
with take names referenced by the current `ModelImporter.clipAnimations` list.
It warns when a source take is not covered by the customized list, without
changing imported assets, Unity project settings or animation clip timing.

Open **Tools > HPR > FBX Source Take Visibility**. Try the included original
two-take Blender animated cube, then select an FBX model or scan your own
models under `Assets`. The whole-project scan does not count the included demo
as your source content. The UI distinguishes an empty custom list (Unity's
automatic default behavior) from a manually customized list. If a take appears
missing, inspect the FBX **Animation** tab. Newer Unity six releases
already offer an **Import Unreferenced Takes** information message and button
in the built-in Inspector; use that first if available. In older Editors,
manually add the source take with the `+` button and **Source Take** dropdown.
This read-only tool does not repair imports or guarantee animation playback.
The native warning may be sufficient for a single FBX; this candidate's
possible advantage is a **project-wide audit of many source FBX files**.

The sample FBX geometry and original actions are exported from Blender using
**baked axis transforms**, so the model imports into Unity with identity mesh
rotation and scale one instead of a hidden ninety-degree rotation and a
hundredfold scale. This makes the sample easier to inspect and avoids a
misleading model-orientation warning; the two real animation takes and
original Unity asset GUIDs are preserved. The sample still is not a
photorealistic production model and does not prove any animation actually
plays correctly in a buyer game.

The package ships TWO first-party animated cubes: **HPRTwoTakeCube.fbx**
illustrates normal automatic importing and should report no missing source
names; **HPRTwoTakeCustomMissing.fbx** uses the SAME originally Blender-exported
source motion but deliberately stores a real Unity 2022 ModelImporter custom
clip list containing only one of its two takes. The second example must flag
one missing source take. Both are educational fixtures, never evidence of a
third-party bug or a real customer model. Neither sample is counted in
whole-project customer results; use the two labeled example buttons.
When the separate first-party HPR FBX Clip Identity Audit tool is installed,
its exact bundled `Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx`
is likewise excluded from this scan. No unrelated third-party or buyer FBX
files are excluded.

The real original Unity-authored `Samples/Prefabs/` folder contains two
prefabs, one wrapping each included FBX, and `Samples/Scenes/SourceTakeVisibilityDemo.unity`
places them side by side under a camera and light. The scene is a static
first-party example for comparing the two imported source models; it is
**not** a screenshot or visualization of the FBX scanner window, and it
does not certify animation playback or a customer project. Open the two
respective FBX assets in the Inspector's Animation tab to compare their
importer clip settings, and use the two one-click tool checks to see the
actual result. Do not confuse the absence of a configured clip on the
second model with an engine crash or an intentionally missing mesh.

The positive sample was constructed from a genuine Unity private test
importer created by customizing one of two source takes and reimporting.
Only its first-party source GUID was changed to a new stable identity for
separate installation. Do not automatically repair it or assume other
customer models should be rewritten this way. No third-party models or textures ship.

Limitations: source take names are only a heuristic for visible custom clips;
it cannot guarantee imported clip availability, playback, clip identity,
rename/retarget, event binding, Unity bugs or future reimports. Identical
source take names and unknown importer metadata fail closed; large project
scans are capped and cancelable. An empty project or an FBX with animation
import disabled does not count as a passed animation test.

Test first in a **disposable** copy of your own project. Full graphical
Editor usability and approved authentic screenshots remain unverified due
Unity's existing software license/terms prompts. Packaging, author/buyer
Unity 2022 and Unity 6 tests, official store validation, commercial rights,
price, buyer support expectations and any publication are separate gates.
