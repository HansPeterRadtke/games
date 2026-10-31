# Unity commercial programming product — predevelopment research decision

Snapshot: October 31, 2026; owner-approved research scope; Unity integration worktree on Nitro.

**Current recommendation:** Do not submit the HPR Gameplay Systems Suite as a generic ten-module gameplay framework. It currently reproduces existing functionality and does not meet the owner's quality/configurability/editor-usability requirements. Independent cleanroom compilation and functional smoke tests are real, but insufficient. Deep software quality/UX and market comparison are now documented in linked companion files.

The owner explicitly requested substantive research, original-book reading, first-party Unity 6 materials, review of authoritative Infra programming/configuration/GUI/testing rules, Unity Editor integration study, rigorous competitor comparison and differentiation analysis **before further coding**. No production C# source was modified in this research round. Previous uncommitted Unity implementation changes in the worktree remain preserved.

## Documents

- [Knowledge and standards](knowledge-and-standards.md) — seven new legal publisher PDF reference files, their actual editions/publisher rights/original PDF page references; O'Reilly book access limit; native Raspi KnowMoreDiRT status and coverage gap; first-party Unity code/editor/Asset Store validation; trace to Infra policy.
- [Code, configuration and Editor audit](code-editor-usability-audit.md) — specific source locations, confirmed compatibility defect, suspected API/lifecycle bugs clearly labeled as untested, configurable parameter contract and code-quality release gates.
- [Market and positioning](market-and-positioning.md) — direct overlapping framework, system, Editor, replay and industrial-simulation competitors; verified descriptions/prices/reviews where available, customer complaints, differentiated hypotheses, no-sale-data caution and commercial stop/go.
- [Buyer workflow and evaluation](buyer-workflow-validation-plan.md) — concrete experienced-developer Unity Editor tasks, configurability, non-destructive authoring and compatibility tests, feedback, source APIs, UX acceptance and empirical study proposal.

## Decision gates before another implementation sprint

First, verify that at least one narrowly defined experienced-developer problem is inadequately solved by competing products. Preferred HPR-adjacent experiment is **non-destructive integration of one or two systems into an existing game** without replacing controller, source assets, serialization, input stack or editor settings. This is a hypothesis, not a proven differentiation. A separate industrial-simulation integration niche may leverage the owner's domain experience, but existing $600–$1,440 enterprise tools, free forklift controllers and $10 conveyors already compete and require direct scope/user verification.

Second, correct critical source-code and Editor behavior identified by the audit, with failing tests first, verified against real imported buyer archives, new/old input, Unity 6.6, domain reload off, Built-in/URP, existing modified scenes and user configuration. Tests must prove user-owned files are unchanged on cancel/update/failure, avoid unauthorized downloads and side effects, and report actual screen usability.

Third, test actual onboarding/configuration tasks with competent target developers, compare to at least one direct competitor in the same target project and record time, successful completion, errors and willingness to pay; no marketing claim may imply parity with bigger engines or claim AI/visual support not actually delivered. Only then decide whether a product should be submitted.

**Current external state:** Unity rejected the former nine small AI-related submissions on October 8; the consolidated product has not been resubmitted, approved or published. Recover the original publisher account after the product is genuinely defensible. Do not create an alternate account or republish unchanged drafts.

## Important corpus caveat

Raspi's downloader now reports all **12,372** curated original files present, including seven newly added first-party Unity PDFs. The old native FileDB snapshot still has 12,365 of those originals while existing semantic vectors remain protected. The new seven are available directly from the original corpus and the fresh full-byte source catalogue, but are **not yet admitted into the original native FileDB metadata**. Do not run its replacement refresh, which correctly refuses to discard populated vectors. A source-preserving incremental KMD admission path must be verified separately; current native semantic search is not complete merely because its top-k returns a result.
