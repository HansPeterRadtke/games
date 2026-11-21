# HPR FBX Clip Identity Audit — unpublished technical candidate

This read-only Unity Editor extension checks model-importer metadata for
**repeated class seventy-four AnimationClip mapping IDs and custom clipAnimations internal IDs**, a problem reported by
Unity developers when split FBX animation clips become unselectable.

Use **Tools > HPR > FBX Clip Identity Audit** to scan FBX assets in the
project. The first view displays the overall state, number of checked FBX
models, affected models and confirmed duplicate local IDs. Review the model
paths and details. Optionally export a create-only JSON report.

The scan never edits or reimports FBX or `.meta` files, never modifies scene
references, never uploads anything and never attempts to guess replacement IDs.
An empty project displays NO_FBX_MODELS_SCANNED, not a clean verdict. An incomplete scan is explicitly not a pass. A scan with no duplicate table
entries is not a full validation of animation clips or an assurance that
future imports are safe. Confirm any issue in a disposable clone of the buyer
project before making manual changes.

Editor-only first-party source. No runtime components or optional packages.
Unity 2022 LTS and Unity six native validation is required before publication.
The attached legal text is an internal placeholder, not buyer-approved license.
