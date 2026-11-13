# Unity commercial programming product — predevelopment research decision

Snapshot: October 31, 2026; owner-approved research scope; Unity integration worktree on Nitro.

**Current recommendation:** Do not submit the HPR Gameplay Systems Suite as a generic ten-module gameplay framework. It currently reproduces existing functionality and does not meet the owner's quality/configurability/editor-usability requirements. Independent cleanroom compilation and functional smoke tests are real, but insufficient. Deep software quality/UX and market comparison are now documented in linked companion files.

The owner explicitly requested substantive research, original-book reading, first-party Unity 6 materials, review of authoritative Infra programming/configuration/GUI/testing rules, Unity Editor integration study, rigorous competitor comparison and differentiation analysis **before further coding**. No production C# source was modified in this research round. Previous uncommitted Unity implementation changes in the worktree remain preserved.

## Documents

- [Current exact-package Player and Play Mode acceptance, November 13](current-player-and-playmode-2026-11-13.md) confirms the refreshed runtime in real Editor Play Mode and across three standalone Linux Players, with explicit legacy-only input and consent-gate limits.

- [Patched Editor and ability installer integration](patched-installer-integration-2026-11-12.md) records the tested customer upgrade on Unity 6000.6.8f1 and the rehearsal with the pending commercial changes.
- [Knowledge and standards](knowledge-and-standards.md) — seven new legal publisher PDF reference files, their actual editions/publisher rights/original PDF page references; O'Reilly book access limit; native Raspi KnowMoreDiRT status and coverage gap; first-party Unity code/editor/Asset Store validation; trace to Infra policy.
- [Code, configuration and Editor audit](code-editor-usability-audit.md) — specific source locations, confirmed compatibility defect, suspected API/lifecycle bugs clearly labeled as untested, configurable parameter contract and code-quality release gates.
- [Market and positioning](market-and-positioning.md) — direct overlapping framework, system, Editor, replay and industrial-simulation competitors; verified descriptions/prices/reviews where available, customer complaints, differentiated hypotheses, no-sale-data caution and commercial stop/go.
- [Buyer workflow and evaluation](buyer-workflow-validation-plan.md) — concrete experienced-developer Unity Editor tasks, configurability, non-destructive authoring and compatibility tests, feedback, source APIs, UX acceptance and empirical study proposal.
- [Epic/Fab account handover](epic-fab-account-handover-2026-11-11.md) — independent publisher registration status, official account lookup, required identity step and private credential-storage rules.
- [Unity publisher support](publisher-help-center-2026-11-11.md) — submitted official Help Center inquiry for the existing Unity publisher account.

## November 1 independent Unity QA continuation (separate Git branch)

The [verified QA handover](QA_HANDOVER_2026-11-01.md) describes actual
Unity 6.4/6.6 cleanroom/customer import, a functional non-destructive
healing-ability integration prototype, combined URP/new-input testing,
independent preservation checks and remaining release gates. It references
[customer integration](customer-healing-integration-experiment-2026-11-01.md),
[URP and new input](combined-urp-new-input-2026-11-01.md), and a
[reproduced customer GUID overwrite defect](orphan-meta-safety-2026-11-01.md)
with its isolated, independently verified patch. This work lives on the
separate `qa/unity-customer-integrity-20261101` branch and has **not been
merged into the dirty commercial source or built as a new buyer archive**.
The conclusion remains **NO-GO** until commercial buyer value, full archive
QA and publisher approval are actually demonstrated.

A [separate installer-enabled internal archive engineering ledger](selected-installer-internal-archive-2026-11-01.md) records the actual Unity 6.4 and 6.6 archive build/import, Undo/Redo/Inspector customer acceptance, immutable private snapshot, market limits and pending final render-pipeline checks. The [reproducible private-archive patch](patches/add-selected-installer-to-private-archive-20261101.patch) is deliberately not applied to the original concurrent product worktree. This is independent QA, **not a seller submission or product launch**.

## Decision gates before another implementation sprint

First, verify that at least one narrowly defined experienced-developer problem is inadequately solved by competing products. Preferred HPR-adjacent experiment is **non-destructive integration of one or two systems into an existing game** without replacing controller, source assets, serialization, input stack or editor settings. This is a hypothesis, not a proven differentiation. A separate industrial-simulation integration niche may leverage the owner's domain experience, but existing $600–$1,440 enterprise tools, free forklift controllers and $10 conveyors already compete and require direct scope/user verification.

Second, correct critical source-code and Editor behavior identified by the audit, with failing tests first, verified against real imported buyer archives, new/old input, Unity 6.6, domain reload off, Built-in/URP, existing modified scenes and user configuration. Tests must prove user-owned files are unchanged on cancel/update/failure, avoid unauthorized downloads and side effects, and report actual screen usability.

Third, test actual onboarding/configuration tasks with competent target developers, compare to at least one direct competitor in the same target project and record time, successful completion, errors and willingness to pay; no marketing claim may imply parity with bigger engines or claim AI/visual support not actually delivered. Only then decide whether a product should be submitted.

**Current external state:** Unity rejected the former nine small AI-related submissions on October 8; the consolidated product has not been resubmitted, approved or published. Recover the original publisher account after the product is genuinely defensible. Do not create an alternate account or republish unchanged drafts.

## Important corpus caveat

Raspi's downloader now reports all **12,372** curated original files present, including seven newly added first-party Unity PDFs. The old native FileDB snapshot still has 12,365 of those originals while existing semantic vectors remain protected. The new seven are available directly from the original corpus and the fresh full-byte source catalogue, but are **not yet admitted into the original native FileDB metadata**. Do not run its replacement refresh, which correctly refuses to discard populated vectors. A source-preserving incremental KMD admission path must be verified separately; current native semantic search is not complete merely because its top-k returns a result.

The [exact selected-installer URP/new-input-only import failure](selected-urp-new-input-timeout-2026-11-01.md) is preserved separately: Unity timed out during existing-project ILPP compilation before the new archive imported, while sixty customer files remained byte-identical. Do not mark this compatibility gate complete based on earlier URP results.

The [late November first Unity QA continuation](late-unity-qa-continuation-2026-11-01.md) records a repeated cache-free and package-free URP compilation timeout under severe CPU congestion, a read-only capacity preflight, actual Editor UI state validation, and a separately verified reversible HPR ability detach prototype. The detach patch is **not in the existing immutable internal package** and is not publication approval.

The [read-only HPR uninstall reference audit](safe-uninstall-dependency-audit-2026-11-01.md) now identifies existing buyer-owned serialized GUIDs and source-level HPR dependencies, including after vendor files are removed. It never authorizes package deletion; a full dependency-aware migration remains open.

The [Unity first-party ILPP and CPU contention investigation](unity-ilpp-environment-investigation-2026-11-01.md) separately records the cache-free URP compile failures before HPR was installed, observed CPU saturation, and a related but **not yet proven equivalent** official Unity Bee issue in the tested Editor version. No test failure is silently reclassified as a passed URP acceptance.

The [original Asset Store listing claim audit](listing-claim-verification-2026-11-01.md) independently compares the uncommitted original seller draft against the actual 161-asset internal candidate, previous v14 URP media evidence, verified selected-installer workflow and missing dependent-game migration/buyer-market requirements. The owner listing itself remains untouched.

The November second [broker-supervised Unity URP CPU-admitted retry](urp-broker-retry-2026-11-02.md) uses the actual Raspi central resource broker and Nitro local job supervisor. It waits for measured CPU availability without touching other owners, creates only new projects, and never repeats a partially imported test in place. As of its first read-only check, CPU was too saturated and the exact archive URP gate remained incomplete.

The November second [selected-object detachment source-only provenance](selected-detach-source-provenance-2026-11-02.md) records a separately staged, uncompiled removal-button proposal, actual source-diff/GUID verification, a low-cost offline Unity six API compile, two pre-existing external helper-project symlinks, and the required new Unity archive acceptance gates. Neither the immutable buyer package nor the concurrently dirty owner worktree was changed.

The November second [scoped HPR sample-copy saving and dirty customer asset test](scoped-sample-save-2026-11-02.md) records a newly discovered global SaveAssets side-effect risk, the minimally staged clone-only save patch, preserved all 516 Unity metadata identities, the independent zero-error offline C# API compile, and the not-yet-executed genuine Unity Editor unsaved-asset adversarial test. The previous immutable buyer archive is unchanged.

The November second [HPR-native Stats resource binding and customer installer safety](native-stats-buyer-resource-2026-11-02.md) covers an existing runtime-only Stats adapter that a customer cannot save and reload from the Inspector, a narrow serialized native-provider source fix, the checked independent source snapshot and staged real Unity customer scene/save/Play-mode regression. This is not a general third-party health adapter or a shipped package.

The [Serial customer Unity Editor follow-up source (not activated)](serial-customer-editor-qa-2026-11-02.md) records independently verified technical and commercial limitations. None of these new QA outputs authorizes publishing.

The [First-party current competitor/pricing/feature supply comparison](market-competitive-proof-2026-11-02.md) records independently verified technical and commercial limitations. None of these new QA outputs authorizes publishing.

The [Genuine Unity media log/pixel checks and missing key artwork acceptance](unity-media-key-art-qa-2026-11-02.md) records independently verified technical and commercial limitations. None of these new QA outputs authorizes publishing.

The November second [new seven-source private archive and full GUID/assembly QA](seven-source-private-archive-2026-11-02.md) records a deterministic unpublished candidate with exactly seven source/doc payload updates, verified frozen GUID preservation, actual archive-policy checks, three offline C# API build results, and the remaining real Editor and commercial release blockers. A compiled commercial release is not implied.

The November second [exact new Unity package identity and post-Play-mode customer-data acceptance](exact-archive-editor-import-identity-2026-11-02.md) adds an explicit new archive SHA-256 selection, real 161-GUID/payload imported-project comparison, and a second preservation audit after Play mode. Its positive old-package and negative new-package receipts prevent reusing older Unity results to certify the seven-change release. The new archive still needs actual Editor import.

The [November 2 commercial differentiation and submission claim gate](commercial-claim-gate-2026-11-02.md) checks actual ABC/Game Creator 2 storefront features and developer reviews, the October 8 rejection theme, Unity's latest AI/technical policy, and the specific still-unmeasured experienced-developer workflow that would justify this product. The current commercial decision remains NO-GO.

The November 2 afternoon [buyer sample-copy partial-failure preservation](customer-copy-failure-preservation-2026-11-02.md) addresses the source-confirmed risk of deleting newly created customer assets by path when a later copy fails. Five test-first regression contracts passed. An offline compiled-code comparison confirms the old direct DeleteAsset call is absent in the revised method, and a separate deterministic private archive retains all earlier GUID identities. Real Unity Editor failure injection remains outstanding; commercial status is NO-GO.

The November 2 afternoon [copy-race and uncertain failure protection](copy-race-guard-2026-11-02.md) documents a test-first pre-CopyAsset collision check and the corrected buyer error showing confirmed and uncertain output paths. The exact HPR copier method body passed six low-priority standalone fake-Unity scenarios. These results are NOT real Unity AssetDatabase or concurrency acceptance.

The separate [exact archive C-sharp compiler matrix and existing-buyer upgrade staging](reviewed-package-api-upgrade-qa-2026-11-02.md) verifies the newest private 161-asset reviewed archive, all 55 actual packaged C-sharp files in three offline API configurations, and a preserved populated customer upgrade fixture with 63 original buyer files protected. No real Unity Editor import or store submission occurred.

The November three [HPR uninstall dependency blind spots in asmref and embedded customer UPM packages](uninstall-asmref-embedded-package-2026-11-03.md) records test-first fixes for missed assembly-reference, embedded customer C-sharp and package.json dependencies, independent real archived seller GUID evidence, and read-only positive/negative customer project preflight receipts. It does not authorize deleting customer packages or certify real Editor integration.

The November three [Read-only customer game upgrade safety preflight](buyer-upgrade-preflight-2026-11-03.md) combines the previous actual imported-vendor identity, old/new GUID preservation, complete customer and embedded package byte hashing, consumer references, and unknown/colliding metadata checks into a fail-closed source-level update review. It does not import or delete anything; the real Editor and buyer gates remain outstanding.

The November three [review-only two-file integration into the owner's current dirty Unity source](owner-uncommitted-copy-safety-merge-review-2026-11-03.md) documents a byte-matched, two-file safe-copy and demo-material patch against the original owner working files. The patch was checked without modifying those files and verified through a disposable private copy against the previously compiled exact private HPR candidate. It is not an approved merge or a Unity Editor acceptance.

The November three [Cross-platform Unity archive asset-path collision policy](portable-unity-archive-paths-2026-11-03.md) rejects duplicate case-insensitive, Unicode-normalized, Windows-reserved and trailing-space/dot asset names before a package is considered importable. Four test-first negative fixtures were corrected; both real 161-asset HPR packages still pass the stricter read-only policy. This is not a real Windows/macOS Unity Editor import.


## November 3 owner-authorized resumption — input and health boundary review

The [existing-game source comparison and acceptance correction](buyer-input-health-source-comparison-2026-11-03.md) distinguishes the genuine earlier Unity API/controller-retention passes from unproven integration with an existing customer health and input system. It checks the exact private archive, records the three-module/17-script ability dependency closure versus the delivered ten-module archive, adds a pinned MIT Flexi source comparator with its real dependency and UX limits, and defines the next fair input-to-health/save/removal task. Fourteen read-only source assertions passed; no new Editor/user benchmark or production C# change is claimed. Commercial NO-GO remains.


The [afternoon native existing-game input/health experiment](existing-game-native-input-health-2026-11-03.md) adds explicit independent game-state/input/save fixtures, a specific shadow-state negative control and strict receipt validation. It preserves actual native import and failed gameplay/staging evidence without treating compiler, import or unrelated failure as workflow completion. See the dated report and private native receipts for current verification limits.

The final fresh-database wired run in that report completed sixteen genuine Unity 6.6 Play-mode observations with domain reload enabled, preserving 67 protected files and all 55 exact packaged C# sources. The second continuation also completed the wired domain-reload-disabled case and the specifically rejected shadow-health control, with 76 protected files unchanged in each new project. Physical input, rendered usability, cold restart and commercial buyer proof remain open.

A test-first preservation correction now takes the customer-file baseline before
bootstrap import: two controlled overwrite/deletion cases reproduced false PASS
results before the fix, then all eleven focused tests passed. A new real Unity
Built-in archive-import plus sixteen-check gameplay run preserved forty original
files through import, forty-eight through the staged probe and all fifty-five
packaged scripts. This strengthens private QA and does not change commercial NO-GO.

The raw-log follow-up also found a UnityEditor.Search startup exception across the
new native copies, including functional Built-in passes. The first URP-configured
case imported the archive and wrote all gameplay checks, but the required native
exit timed out; its strict result is FAIL. Error-free Editor, rendered URP and
clean-project/cache acceptance remain open. See the dated report for the separate
retry, evidence boundaries and current outcome.

The fresh URP-configured probe retry subsequently exited zero with all sixteen
checks, eighty-nine protected files unchanged and all fifty-five exact packaged
scripts. The shared UnityEditor.Search exception recurred, so this is bounded
headless functional acceptance, not error-free Editor or rendered URP proof.
The final audit verified all five owned jobs stopped and all twenty-one original
dirty files across six worktrees unchanged. Commercial release remains NO-GO.

The third-continuation [clean Editor startup and Play control](clean-editor-startup-control-2026-11-03.md)
reproduces the same search-index exception in genuinely new no-HPR projects after
immediate Play entry, with legacy input, new input and actual software OpenGL.
Startup-only controls are clean; a measured Edit-mode startup interval before two
Play sessions avoids the error in the paired control. This is a private QA sequencing
finding, not an engine patch or commercial release approval. See the report for
the separately verified real-package follow-up and final source-preservation audit.

The real-package settled-startup follow-up then passed all sixteen native workflow
checks and exited zero, with no matching Search exception in either native phase.
It preserved twenty-seven original files across actual import, thirty-six across
the probe and all fifty-five exact archived C# sources. The correction is an opt-in
private QA sequencing change. The seven original worktrees and twenty-one dirty
files were unchanged, and all seven owned jobs were confirmed stopped. Rendered
usability and independent buyer/differentiation gates remain open; release is NO-GO.

The [November 3 night definition-safety and cold-restart milestone](night1-ability-definition-and-cold-restart-2026-11-03.md)
adds eleven real failing invalid-definition cases before a four-payload private
fix. The final candidate passes seventeen native configuration cases in Unity 6.6
and native 6.4/legacy input, the full sixteen-check existing-game workflow in 6.6
with domain reload both on/off, and fifteen fresh-process restore checks against
an older package's save. Runtime validation now precedes resource charging while
event-only compatibility is retained. All original source edits and save/package
identities were preserved. The normal graphical Editor stopped at software-terms
consent; no installer pixels or physical UI interaction is claimed. The private
candidate remains unapproved and commercial release remains NO-GO.


The [November 4 night-two native NUnit milestone](night2-native-nunit-2026-11-04.md)
runs the same 55 module EditMode cases against actual imported archives. The old
archive fails exactly 18 new malformed-definition assertions; the corrected
candidate passes all 55 in Unity 6.6 and 6.4 with their own bundled Test Frameworks.
A test-first copied-lock preservation correction rejects unrelated dependency
changes and deletion; all native results were independently rechecked. Existing
source edits, immutable archives and the save remain preserved. No new product
archive, graphical consent or commercial approval is implied.


The [November 4 night-three effective URP workflow milestone](night3-effective-urp-workflow-2026-11-04.md)
verifies the corrected archive through actual native import plus all sixteen
existing-game observations with domain reload on/off. Three native observations
confirm the same effective URP asset before/during/after Play. A Built-in run that
passes the full gameplay contract is correctly rejected when labelled URP. These
are headless configuration/functional results, with no rendered-frame proof.
An extra installed-but-inactive URP control was resource-denied and left unrun;
all earlier source edits remain preserved and commercial release remains NO-GO.


The [November 4 night-four resource-provider lifetime fix](night4-resource-provider-lifetime-2026-11-04.md)
reproduces actual activation through a destroyed provider in the previous candidate:
exactly one of 56 native NUnit cases fails. A one-payload runtime guard now passes
all 56 cases in Unity 6.6 and 6.4, plus the full Built-in existing-game workflow in
6.6 and configuration checks in 6.4. Original metadata, source edits and archives
remain preserved. The new lifetime archive has its own checksum; older URP/cold
results are not transferred to it. Its extra URP run was resource-denied and left
unrun. Rendered usability, source reconciliation and buyer validation remain open.


The [November 4 night-five ProjectSettings dependency correction](night5-project-settings-dependencies-2026-11-04.md)
closes a read-only preflight blind spot: native Unity-saved build settings contain a
real vendor-scene GUID that the old detector misses. The corrected bounded scanner
finds it without changing project bytes, and the composed source-upgrade preview
now requires dependency review. Forty uninstall tests, thirteen upgrade-preview
tests and four private-fixture routing tests pass. The current product/archive is
unchanged; no uninstall, new URP attempt, graphical consent or release is implied.


The [November 7 interrupted input-key fix recovery](input-key-validation-2026-11-07.md)
recovers actual completed red/green native Play-mode evidence without repeating
uncertain work. Undefined saved key values previously activated D or threw range
exceptions. The one-payload guard passes all twelve native input cases; a fresh
Unity 6.4 legacy-input import/configuration run passes seventeen cases, and both
positive imports retain all 161 package identities. Original source edits remain
preserved. This is focused input/package QA, not broader pipeline or commercial
acceptance of the changed archive.


The [November 7 corrected-input archive module regressions](input-key-module-regression-2026-11-07.md)
run all 56 canonical module NUnit cases against the changed archive itself in
Unity 6.6/new-input and 6.4/legacy-input projects. Both actual native runs pass,
with all 161 asset/GUID identities retained and original worktrees preserved.
This closes that archive-specific module-regression gap; rendered usability,
URP/Player/workflow coverage and independent buyer validation remain open.


The [November 7 corrected-input existing-game regressions](input-key-existing-game-regression-2026-11-07.md)
pass all sixteen native gameplay observations with domain reload on and off in
Unity 6.6/new input. Both runs verify effective Built-in selection through
Edit/Play/Edit, unchanged protected files and all 161 archive asset/GUID identities.
These fresh results apply to the corrected input archive itself; rendered UI,
URP/Player/cold-process coverage and independent buyer validation remain open.


The [November 7 corrected-input fresh-process save regression](input-key-cold-restart-2026-11-07.md)
passes all fifteen native observations in a new Unity 6.6 process, including
restored vitals/HUD, rejected invalid snapshot, cooldown expiry on the new game
clock and subsequent existing-input healing. Exact source save/scene/template
bytes and all 161 archive identities survive. This closes the changed archive's
bounded Editor cold-process gap; Player, URP, rendered usability and buyer gates
remain open.


The [November 7 corrected-input Linux Player probe](input-key-linux-player-2026-11-07.md)
completes a native Unity 6.6 Linux x86-64 build and executes the actual Player.
Four game-update input checks pass for ordinary keys, arrows, numeric/modifier/
numpad bindings, press transitions and release. Source/template bytes and full
archive identities survive. This is bounded new-input Player evidence; full
Player gameplay/save, other stacks/platforms, rendered pipelines and buyer gates
remain open.


The [November 7 Both-input Linux Player regression](input-key-both-input-player-2026-11-07.md)
passes all four native game-update input checks after an actual Player build with
both legacy/new compiler symbols and copied-project Both selection. The private
receipt wording now names the observed adapter rather than implying new-only
mode. Exact archive/template identities and the previous Player remain preserved.
Legacy-only Player behavior, full gameplay/save, rendered pipelines and buyer
validation remain open.


The [November 7 legacy-only Linux Player smoke](input-key-legacy-player-2026-11-07.md)
completes an actual Unity 6.4 build and Player startup without the Input System
package. The actual Player compiler selects only the legacy backend; three smoke
observations pass, including inactive unbound-key queries. New private fixtures
are unshipped and source/template/archive identities remain protected. Physical
legacy transitions, full gameplay/save, rendered pipelines and buyer validation
remain open.


The [November 7 actual existing-game input-fix upgrade](existing-game-input-upgrade-2026-11-07.md)
imports the corrected archive into a fresh clone of a verified older integrated
game. Exactly the input source changes; all 139 customer files and 161 package
identities survive. A further fresh process passes all fifteen existing-scene/save
checks after upgrade. This is one measured private transition; general migration,
rendered usability, URP and independent buyer gates remain open.


The [November 9 package-metadata migration preflight correction](package-metadata-preflight-2026-11-09.md)
requires review for malformed package metadata, bounds actual metadata reads and
finds transitive HPR lock references. Nineteen old failure observations are fixed;
58 regression methods pass. A saved Unity project remains byte-identical with its
47 dependency findings preserved. This changes read-only QA tooling, not the product
archive or native/rendered acceptance status.


The [November 9 full importer-metadata identity correction](importer-metadata-identity-2026-11-09.md)
closes a GUID-only preservation gap. An actual Unity-generated execution-order
edit kept every GUID but was incorrectly reported pristine; full metadata checking
now detects it and blocks the upgrade precondition. Seventy-one regression methods
pass, and untouched native projects retain all 161 metadata identities. This is
read-only QA protection, not importer migration or release approval.

[Save-slot integrity and native regression results](save-slot-integrity-2026-11-10.md) cover the private package tested in Unity 6.4 and 6.6.
