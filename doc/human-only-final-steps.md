# Human-Only Final Steps

## EventBus current state

The first product, HPR Typed Event Bus, no longer needs a manual package upload.

Verified on 2026-10-07 against the authenticated Unity Hub / Asset Store session:

- Unity account: multiverse3dhpr@gmail.com
- Publisher account linked: yes (publisher id 161382)
- Publisher Portal version: package 414626, version 1506320, status pendingReview
- Server category: Tools/Utilities
- Uploaded package size: 11477 bytes
- Storefront price: $9.99
- Uploaded package: 21 files, Unity 6000.4.0f1, server upload status finished
- Vetting status: submitted; auto-publish: enabled
- Server icon present: yes
- Official Asset Store Tools validation: clean (RanToCompletion, no compilation errors, zero validation issues)
- Package upload: completed successfully

The repository now contains authenticated upload and read-only publisher-audit runners under
unity/tools/release/. They use the Unity Hub session and must never log or persist the Hub
access token or Asset Store session secret.

## Remaining EventBus work

- No package edit, upload, draft creation, or resubmission is currently required while the package is in review.
- Wait for Unity's curation result and act only if the review status changes or Unity requests a package/listing correction.
- The dedicated `Multiverse3d AS Publisher` organization currently has no payout profile. Unity states that a payout profile is required only to receive payouts; this does not block the current package review.
- Creating that payout profile requires activating TFA on the Unity account first, then entering the payout/tax/payment information. Those security, tax, and banking declarations remain human-only.

The authenticated Asset Store preview currently renders `File size 0 Bytes` and does not show the price while this submitted version is in preview/review mode. This is a preview rendering issue, not missing source data: the embedded preview payload reports `downloadSize: 31.0 kB`, while the Publisher Portal package-version API reports price `9.99`, package size `11477`, upload status `finished`, 21 files, vetting status `submitted`, and auto-publish enabled. Do not create a new draft or re-upload solely to address the preview's `0 Bytes` or hidden-price display.

Do not create another Unity ID, publisher profile, or duplicate EventBus draft. Do not re-upload
the package while it is in review unless Unity rejects it with a package-level issue or the package itself changes.


## Current Asset Store review queue (verified 2026-10-08)

- HPR Typed Event Bus — package 414626 / version 1506320 — pendingReview — $9.99 — auto-publish enabled.
- HPR Inventory Core — package 415296 / version 1508780 — pendingReview — $14.99 — auto-publish enabled.
- HPR Composition Root — package 415312 / version 1508798 — pendingReview — $9.99 — auto-publish enabled.
- HPR Save Snapshots — package 415314 / version 1508802 — pendingReview — $9.99 — auto-publish enabled.
- HPR Stats & Damage — package 415320 / version 1508814 — pendingReview — $14.99 — auto-publish enabled.

All four have current Unity 6000.4.0f1 uploads, current publisher terms accepted, storefront metadata, screenshots, key images, and AI-use disclosure. Do not create duplicate drafts for these products while they are under review.

## Later packages

For the remaining prepared packages, use the same validated Hub-authenticated upload workflow.
A browser login and manual .unitypackage upload are no longer assumed to be required. Human
review is still required for commercial/legal choices, storefront presentation, and the final
submission/publish decision.
