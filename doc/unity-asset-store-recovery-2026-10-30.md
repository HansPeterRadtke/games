# Unity Asset Store publisher — October 30 technical recovery

## Original facts and policy

The existing publisher is Multiverse3d. Original rejection emails dated
October 8 confirm nine distinct HPR submissions were **declined**, each with
exactly the same reviewer rationale: volume of similar AI-related packages
could oversaturate the market and dilute the unique value of other work.
Review requested consolidation/refinement into fewer, more impactful products.
This is not an ordinary per-package compilation, quality validator, missing
icon, missing payment, or absence-of-identity rejection; the curator rejected
publication strategy and differentiation.

Unity's official submission guidelines updated October 23, 2026, require
strong independent value of generative-AI-assisted assets (1.6), and prohibit
mass-produced packages without differentiation (1.6.d). Further rules say a
publisher cannot resubmit identical rejected content to evade curation
(2.1.h), prohibit multiple largely identical packages (2.1.f) and impose a
monthly submission cap based on publisher age (1.1.m). The already-rejected
nine products must not be blindly resubmitted or split across new accounts.

Official guidance: https://assetstore.unity.com/publishing/submission-guidelines

## Exact live tests on Nitro — no provider writes

The existing private credentials matched the dedicated Multiverse Unity login.
On October 30 the official Unity 6000.4 Asset Store Tools uploader in dry-run
mode authenticated through `CredentialsAuthentication` successfully. The
read-only `GetPackages` response contained **zero packages**, and exact lookup
of HPR Typed Event Bus failed. The previous nine package/version IDs and
actual rejection notices remain valid historical evidence. Neither deleting
those drafts nor creating a new account was authorized or performed.

The Unity Publisher Portal route showed a sign-in form. The existing account
email was entered through the approved private local credential file without
printing it. The field was syntactically valid but the page returned
`Invalid email`; no publisher session was established. Automated support
request routes redirected back to support home or did not load a usable form.
Do not misdescribe a valid Unity Editor API authentication as successful
Publisher Portal login.

An independent old asset submission support email was redirected to Unity's
new Help Center on October 27, whose response said replying to the old
support thread would not be received. An additional publisher-specific,
nonsecret clarification request was sent on October 30 to the historically
published Asset Store address, asking about a single genuinely integrated
rework and the empty package list. Gmail confirmed send and **Unity replied
at 19:37 CET that the mailbox is no longer monitored**. This email did not
open a support ticket. The official Unity Help Center offers publisher
submission and portal-issue routes, but its actual ticket form currently
returns `Your organization has reached the ticket concurrent limit` even
before an authenticated submission. Do not try alternate old email aliases
or claim a current support ticket exists until provider acceptance is observed. Do not repeat
this same message or invent a case from a send receipt.

## Agent work and release plan

Original packages: eventbus, composition, save, stats, inventory,
interaction, abilities, weapons, enemy AI, and world registry. The ten source
modules are original; source unit-test assemblies and third-party assets
are deliberately excluded from the buyer package. A new integrated
Play-mode demo explicitly connects weapon runtime, enemy runtime, EventBus,
stats, inventory and memory-only save data. The packaging script produces
one legal Unity `Assets/HPRGameplaySuite` root with no vendor submission.

Run isolated ten-module Unity compilation and EditMode tests. Run the new
single-root integrated demo build and export. Then test import of the actual
archive into an independent disposable Unity project and inspect all assets,
assemblies, demo scene, source documentation and licensing. Any failure is a
real blocker, not a cosmetic log warning. Verify that this actually delivers
more new buyer utility than simply putting ten old rejected drafts into one
archive; if not, keep as an internal candidate and improve integration.

Only once the new integrated product is differentiated and technically
verified, and the original account and vendor approval constraints are
resolved, should one legitimate submission be considered. Never create
multiple new packages or accounts to sidestep the existing rejection.

## Human-only boundaries

If the legitimate Unity login demands a visual CAPTCHA, two-factor approval,
ID proof or a contractual account declaration, only the account owner may
complete that step. Agents can and should still handle all source engineering,
package validation, safe support communications, and post-verification QA.
Human participation is not warranted for downloading manuals, inspecting
source, running tests or ordinary nonsecret technical support correspondence.
