# HPR FBX Clip Identity Audit — unpublished technical candidate

This read-only Unity Editor extension checks model-importer metadata for
**repeated class seventy-four AnimationClip mapping IDs and custom clipAnimations internal IDs**, a problem reported by
Unity developers when split FBX animation clips become unselectable.

Use **Tools > HPR > FBX Clip Identity Audit**. For your first run, click
**Check included animated FBX** to scan the first-party, animated cube example
at `Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx`; it should have no
known duplicated ID in its default importer settings. To scan your own file,
choose the FBX model in **Selected model asset** and click **Check selected FBX**.
To audit every customer FBX in `Assets`, click **Scan all FBX models (read only)**.
The project-wide scan explicitly excludes this tool's own included
`Samples/OriginalMotion.fbx`, so a fresh buyer project containing only the
example correctly reports `NO_FBX_MODELS_SCANNED`. Use the separate example
button to inspect the sample itself. A clean example is not a clean project.
The result displays the overall state, checked-model and affected-model counts,
confirmed duplicated IDs, and explanatory model paths. Optionally export a
create-only JSON report. Never interpret the bundled example's clean result as
proof the entire buyer project is safe. The example's animation was created in
Blender by the package author and does not include third-party models.

The scan never edits or reimports FBX or `.meta` files, never modifies scene
references, never uploads anything and never attempts to guess replacement IDs.
An empty project displays NO_FBX_MODELS_SCANNED, not a clean verdict. A scan of
one or more FBX models that import no AnimationClips displays
NO_ANIMATION_CLIPS_IN_CHECKED_MODELS. An incomplete scan is explicitly not a pass. A scan with no duplicate table
entries is not a full validation of animation clips or an assurance that
future imports are safe. Confirm any issue in a disposable clone of the buyer
project before making manual changes.

Editor-only first-party source. No runtime components or optional packages.
Unity 2022 LTS and Unity six native validation is required before publication.
The attached legal text is an internal placeholder, not buyer-approved license.
