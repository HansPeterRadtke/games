# Unity six point six: actual rendered URP acceptance on the current buyer archive

**Date:** 13 November 2026. **Scope:** private reproducible buyer-package QA, no publication.

The earlier night-three URP checks were valid for a different candidate and used null graphics; they did not prove rendered frames for the current commercial package. This experiment uses the latest exact commercial buyer archive (the duplicate-ability-ID-corrected release) built with patched Unity `6000.6.8f1`, against the independently configured URP `17.6.0` / Input System `1.20.1` host. The host started with no HPR package files. Only the existing verified private URP renderer and asset configuration, `Packages` and `ProjectSettings` were copied into a new, disposable Unity project. Original customer and repository project trees were never modified.

## Verified results

- Actual Unity batch import exited zero; `unity_imported_archive_identity.py` matched **161 of 161 asset paths and GUIDs** and **55 C# scripts** against the exact archive, with zero issues.
- Patched Unity running **real OpenGL Core on NVIDIA RTX 3060 Laptop GPU** selected the actual URP asset and imported live arena scene. The existing independent `HprSuiteUrpValidator` passed: all **11 training materials** converted to the installed supported `Universal Render Pipeline/Lit` shader and the demo camera was present.
- A separate native Unity run of the existing `HprGameplaySuiteStoreKeyCapture` rendered the real imported arena camera twice per frame to warm URP Lit shaders and produced four PNGs at **160×160, 420×280, 1950×1300 and 1200×630**, all with native exit zero. No scene-save API was invoked. The images contain visible geometry, colored materials and text. The four frames were checked with the new read-only `check_rendered_urp_frames.py` utility: correct dimensions, non-flat pixel variation, no nearly black frames, and no large missing-shader magenta regions. This is not a test of physical keyboard or mouse interaction.
- Before the opt-in materials adaptation, a private file-hash baseline covered **330** files in `Assets`, `Packages` and `ProjectSettings`. After adapting and capturing, exactly **11 original HPR sample material files** changed, five private QA script/meta files were added, and **zero original files** were removed. No original buyer project settings, input settings, asset GUIDs, or other customer files changed.
- The actual small rendered image was visually inspected. It depicts a dark blue-grey top-down technical training arena made of simple primitive geometry, blue/cyan and amber accents, a blue player capsule, orange enemy and labels. It does **not** yet demonstrate polished, distinctive commercial art or independent human-buyer approval. Successful functional rendering does not change the suite's release **NO-GO** status.

## Source and private reproduction evidence

The read-only PNG checker is `unity/tools/release/gameplay_suite/qa/check_rendered_urp_frames.py`, with five offline regressions in `tests/test_unity_rendered_urp_frames.py`. It requires Pillow in the private QA environment only; it is not part of the `.unitypackage`. Re-run it on the new private capture directory with an unused optional `--receipt` path. The checker explicitly reports `human_artistic_approval=NOT_PERFORMED`.

Private runtime evidence is under `/data/var/marketplace-account-setup/hpr-current-urp-visual-20261113/`:

- `import.unity.log` and `exact-import.json` — real native import and exact package match.
- `urp-materials.unity.log`, `urp-acceptance-receipt.txt` — real OpenGL URP pipeline and the eleven Lit materials.
- `actual-render.unity.log`, `captured-frames/` — four real camera PNGs and capture receipt.
- `before-urp-adapt.json` — pre-adaptation hash inventory; each changed original confirmed against post-capture hashes.
- `automatic-image-qa.json` — quantitative frame-content and dimension checks, still not visual/marketing approval.

## Open gates

Manual rendered Editor installer controls (attach/remove/Undo and disabled-button states), buyer-panel accessibility, independent developer/buyer comparison, and package-readiness review still require separate evidence. The scene is technically readable but visually basic. No marketplace publication, art approval, external outreach, or other owner-only effect took place. The main seller worktree retains its pre-existing fourteen local changes.
