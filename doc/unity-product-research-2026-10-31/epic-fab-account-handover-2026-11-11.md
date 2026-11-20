# Epic/Fab publisher account — owner handover, November 11, 2026

## Separate accounts, separate work

Unity Asset Store publisher and Epic/Fab publisher are unrelated
account systems. Unity support was successfully submitted via the
official Help Center; its existing case is tracked in the separate
publisher support note. Do not create another Unity account.

The owner wants a NEW Epic Games identity using dedicated Multiverse
Gmail, then a new Fab publisher account, rather than restoring the
old Epic/Fab publisher profile. The old account must not be deleted,
unlinked or closed: entitlements, licenses, buyer assets and account
data may not transfer to any new identity.

## Verified Epic account state

- Dedicated Multiverse Gmail contains Epic/Fab support correspondence,
  but no Epic registration confirmation for a new identity.
- Official Epic self-service email lookup at
  https://www.epicgames.com/help/wizards/w5 found an existing older Epic
  identity using its historical display name. Epic reported it sent a
  confirmation email to that identity's registered address. No matching
  message reached dedicated Multiverse Gmail, including Spam or Trash.
  The older account's actual registered email remains UNVERIFIED.
- Google SSO with Multiverse Gmail was attempted, then retried while
  preserving the initiating Epic browser tab. Consent remained stuck.
  Official Epic account-settings readback still redirected to login.
  No authenticated Epic login or new account was verified.
- The direct new Epic signup presents a required date-of-birth gate
  before collecting login credentials. No authentic date of birth was
  found in the known account and personal notes; one was not invented.
- A separate recovery check for the desired Gmail was attempted once
  with an inconclusive result and no subsequent Epic Gmail message.
- NO new Epic account, NO new Fab publisher, NO generated password,
  NO agreement, identity documents, tax details, payout data or
  seller submissions.

Private account names, identity records, credentials and action
receipts are maintained outside Git under:
 /data/infra/secrets/epic-fab-account-status-20261111.txt
 /data/var/marketplace-account-setup/epic-*/

## Owner input needed for new registration

The account holder's REAL date of birth must be entered on Epic's
official registration form, either by the owner directly or provided
for this one account registration. We cannot invent an age or submit
a false identity. If provider CAPTCHA, 2FA or real identity evidence
appears, the owner must complete the direct verification. Normal
confirmation messages sent to connected Multiverse Gmail can be read
with the existing authorized Gmail integration.

The new Multiverse Gmail address must be available/unique for new
registration. The previous unknown Epic linkage must not be guessed.
Success requires server-side confirmation of the new Epic account
and accessible authenticated account settings.

## Fab onboarding after Epic login

Fab first-party onboarding steps:
1. Sign in to Fab using the new Epic account and accept Fab's
   Distribution Agreement under the owner's legal authority.
2. Create a publisher profile and a unique Creator Code. The old
   historical code was reserved; do not presume it is reusable.
3. Complete trader verification, tax information and payout details,
   accurately, with genuine owner identity.
4. Prepare high-quality listings/media in the separately owned 3D
   product project and submit only approved products for review.

Official reference:
https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab

Once a new account is genuinely created and verified, store its actual
login, generated password and verified publisher identity in a
permission-0600 private text file in /data/infra/secrets, excluded
from Git. Never fabricate credentials for a nonexistent account.

No live 3D asset publication was part of this account repair.
