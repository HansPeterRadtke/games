# Authentic Unity Editor key-image capture source — QA-only

Date: November 2, 2026. Nitro. **Source-only proposal,
not a rendered, compiled or approved Asset Store image set.**

The private Unity 6.6 capture log for the previously tested v14 URP
training arena already established that the real Editor rendered two
honest 1600-by-900 gameplay screenshots after the shader-warmup fix.
The objective pixel QA rejected the old nearly black first frame
and accepted the corrected arena/encounter images. This does not
supply the current publisher key images, nor does it validate
the new selected-installer package's incomplete URP matrix.

Unity's official Publisher Manual lists icon 160×160,
card 420×280, cover 1950×1300 and social 1200×630. The current
October 23, 2026 Submission Guidelines and Content Transparency
rules require authentic Unity visuals, clearly identified AI-assisted
functional content and marketing that does not obscure or misstate
the actual product. These source documents must be rechecked at
submission:
https://docs.unity.cn/Manual/AssetStorePkgDetails.html
https://marketplace.unity.com/publishing/submission-guidelines
https://unity.com/legal/asset-store-content-transparency

## Newly written source, not yet an image

The new private Editor-only QA source is
`unity/tools/release/gameplay_suite/qa/HprGameplaySuiteStoreKeyCapture.cs`.
It opens the actual imported
`Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity`,
requires a live Main Camera, and plans four separate Unity
RenderTexture/Texture2D/EncodeToPNG captures at the exact current
historical role dimensions. For each view it warms the initial
URP shader frame with two Camera.Render calls because the first
actual prior Unity capture was demonstrably black. It restores
the camera transform, aspect and previous RenderTexture on exit,
and does **not** save the imported scene or mutate customer assets.

Only a **new private QA output folder outside the Unity project**
is permitted, with explicit filename collision checks. The
post-test source correction adds a strict new-directory rule,
guards existing symlink/reparse-point ancestors, requires the
receipt to reside under that private folder, and uses create-only
FileMode.CreateNew for each screenshot and receipt to avoid
overwrites and dangling-symlink races. It refuses existing files
and does not delete or rewrite any prior captured media on failure.

Five source-level Python regression tests now pass. They verify
the four role dimensions and filenames, genuine Unity scene/camera
APIs, Shader warmup, render-target restoration, refusal of
preexisting outputs, restricted private destinations and create-only
writes. These are **not** real Unity Editor executions.

An independent offline C# compilation attempt for this new
capture helper was explicitly denied by platform safety controls.
That particular action was **not retried by another route**, and
no subsequent Unity Editor compilation or PNG generation has
been claimed. Existing genuine v14 image QA and positive/negative
log evidence were preserved.

## Acceptance before artwork use or product sale

A later owner-approved QA window with admitted CPU/GPU resources must
compile this Editor-only helper in an actual installed Unity version,
run the renderer in a disposable imported-scene project, and verify
real process exit codes, all four saved PNG hashes, key dimensions,
no black frames, original source scene preservation and unique
per-role composition. A qualified human must review the actual
icon/card/cover/social graphics for legibility, branding,
honest feature depiction and compliance with the live portal.

Even if those media gates pass, the current frozen seller archive
remains **NO-GO** pending its exact URP/new-input-only test,
native Stats and targeted SaveAssetIfDirty real buyer tests,
dependent-game migration, publisher identity/AI disclosure and
measured experienced-developer value against competitors.

No pictures were fabricated, upscaled, generated or published.
No real customer file, original product worktree or existing
Unity package was modified by this source-only preparation.
