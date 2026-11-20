# Authentic Unity camera screenshots and Asset Store key-art acceptance

Date: November 2, 2026. Nitro. **Independent quality audit;
not a publication, screenshot generation or AI marketing render.**

## Authentic evidence and prior black capture

The earlier Unity 6000.6.7f1 actual Editor process log from
November 1, 2026 was independently found and inspected under
/data/var/marketplace-account-setup/unity-consolidated-20261101-v14-urp-fixed-media/release/media-capture.unity.log`.

It contains both `HPR_MEDIA_SAVED` events with exact source
PNG paths and bytes, the real `HprGameplaySuiteMediaCapture.Run`
callstack, and an explicit `HPR_MEDIA_CAPTURE_PASS` describing
camera rendering from an imported Unity scene. The Editor ended batch
mode successfully with exit status zero and no C# compile errors or
warnings found in that log. The two image SHA-256 identities are:
- Arena: 68ef41f20ccd1f94758797cc5d0ace94711078911ad15733738f42dad2daf405.
- Encounter: d335ae6e0f50ce7811b767bf7a7df7677de1d3887b1ced32d8ee0392a36bd463.

The original, pre-fix v14 URP arena screenshot was dramatically dark
with 45.8 percent of pixels nearly black, central luminance variation
near zero, mean luminance 0.071 and extremely low edge detail. The
independent pixel gate correctly classified it **FAIL**, while the
corresponding older encounter image had an acceptable dynamic range.
The subsequently fixed real Unity camera captures both passed basic
pixel-detail QA: resolution **1600 by 900**, mean luminance **0.17760**
and **0.18088**, center variation **0.13040** and **0.14321**,
zero near-black pixel fraction at the chosen threshold, and distinct
views (35.17 percent of pixels materially changed between captures).
This is actual objective pixel evidence for the corrected camera,
not human approval of professional composition.

The previous v7 fixed pipeline images also passed the same objective
gate. The Python image check and historical negative/positive receipts
were saved separately in the owner's private Unity QA evidence folder.

## Independent non-black image and gallery safety checker

Source:
`unity/tools/release/gameplay_suite/qa/hpr_unity_media_audit.py`.

Seven deterministic tests first failed without the implementation and
then passed. These include a black image, uniform low-detail frame,
meaningful geometric scene, exact duplicate screenshot pair, two
independent views, undersized capture, and the **real earlier broken vs
fixed URP camera files**. The checker loads existing PNG pixels
read-only and evaluates brightness, contrast, center detail, near-black
coverage, pixel edges and pairwise differences.

It never generates images, modifies originals, or claims that passing
pixel metrics proves the source was rendered by Unity. The separate
real Unity process log supplies source/capture provenance for the
v14 images. A human must still review composition, readability,
shader correctness, relevance and whether the image honestly
represents the exact proposed product.

## Exact Unity Asset Store key-art sizes

Unity's official historical publisher manual identifies the key
artwork roles and exact pixel sizes:
- Icon: **160 x 160**.
- Card: **420 x 280**.
- Cover: **1950 x 1300**.
- Social: **1200 x 630**.

Official primary reference:
https://docs.unity.cn/Manual/AssetStorePkgDetails.html

The live publisher portal must be checked again at actual submission,
as a historical manual page is not a guarantee about current UI.
The icon, card, cover, and social image roles are distinct from ordinary
screenshot galleries. Unity Content Transparency section **2.7.2** explicitly requires
marketing artwork/screenshots/videos to contain actual Unity Editor
rendered visuals; its section **2.7.6** prohibits marketing/showcase
images that are entirely AI-generated other than supporting/background
material. This is a hard provenance gate, not simply an image-size check.
The current publisher submission guidelines were updated October 23,
2026 according to the official page observed November 2.
https://unity.com/legal/asset-store-content-transparency

A separate read-only key-image gate,
`hpr_unity_store_key_image_gate.py`, has five passing unit
tests for exact role/dimension mapping, missing roles, wrong dimensions,
invalid role and the **actual v14 store cover**. That historical
`01-store-cover.png` measures **1600 x 900**. It may serve as
a gameplay gallery slide, but it is **not** a ready **1950 x 1300**
official key cover. On the observed prior internal gallery, separate
icon/card/social key images were also absent. The actual suite therefore
**fails required key-art preparation**. The private QA result explicitly
identifies wrong cover dimensions and all three missing other roles.

No marketing art was upscaled, generated, uploaded, published or
silently substituted to disguise the gap. A future owner-approved
production pass must create true professionally designed key images
at the required sizes, using honest product visuals and distinct
layouts for each format, and validate them against the live publisher
portal. Previous v14 Unity screenshots cannot prove the newly built
selected-installer archive has passed its own URP/new-input-only test.

## Release implications

The current frozen private 161-asset selected-installer package is
still **NO-GO**. Even with the fixed previous URP images, the exact
archive's Unity 6.6 URP/new-input acceptance is incomplete under
Nitro's CPU/Bee compilation issue. Buyer integration/edit/detach
and unsaved-asset fixes also remain partially source-only.
Human marketing/user-experience review and a direct competing-tool
buyer benchmark are outstanding.

The Unity Store's current asset rules separately require URP or HDRP
support when publishing with Unity 6.5 or later, AI-functional-content
disclosure, and transparent material limitations:
https://marketplace.unity.com/publishing/submission-guidelines

**No file or source from another agent was changed in this audit.**
