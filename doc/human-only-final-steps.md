# Human-Only Final Steps

## EventBus current state

The first product, HPR Typed Event Bus, no longer needs a manual package upload.

Verified on 2026-10-07 against the authenticated Unity Hub / Asset Store session:

- Unity account: multiverse3dhpr@gmail.com
- Publisher account linked: yes (publisher id 161382)
- Publisher Portal draft: package 414626, version 1506320, status draft
- Server category: Tools/Utilities
- Uploaded package size: 11477 bytes
- Server icon present: yes
- Official Asset Store Tools validation: clean (RanToCompletion, no compilation errors, zero validation issues)
- Package upload: completed successfully

The repository now contains authenticated upload and read-only publisher-audit runners under
unity/tools/release/. They use the Unity Hub session and must never log or persist the Hub
access token or Asset Store session secret.

## Remaining EventBus portal work

- Review the draft's Product Information against the generated listing draft and enter/fix any missing fields.
- Confirm the final storefront price. The current release recommendation is $9.99.
- Confirm the support email or support URL that should be used consistently across listings.
- Review the existing icon, marketing images, and screenshots in the Publisher Portal preview.
- Complete any publisher-account legal, tax, payout, or provider-agreement steps that the portal still marks incomplete.
- Use Publisher Portal Preview for the final storefront check.
- Submit package 414626 for Asset Store review, choosing auto-publish or manual publish deliberately.

Do not create another Unity ID, publisher profile, or duplicate EventBus draft. Do not re-upload
the package merely to advance the portal workflow unless the package itself changes.

## Later packages

For the remaining prepared packages, use the same validated Hub-authenticated upload workflow.
A browser login and manual .unitypackage upload are no longer assumed to be required. Human
review is still required for commercial/legal choices, storefront presentation, and the final
submission/publish decision.
