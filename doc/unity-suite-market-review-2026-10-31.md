# HPR Gameplay Suite — market and submission diligence (October 31, 2026)

Source: live public Unity Asset Store listings and the Unity publisher rules.
Prices in USD at page observation; promotional prices change. Review counts
are displayed listing counts, not independent buyer-productivity validation.
This assessment is separate from technical QA and is **not publisher approval**.

## Direct commercial comparison

| Offering / link | Store evidence | Buyer expectation | Comparison against HPR |
|---|---|---|---|
| Game Creator 2, https://assetstore.unity.com/packages/tools/game-toolkits/game-creator-2-203069 | $79.99 shown, 418 reviews, 26.9MB, detailed editor tools, character control, save/load, camera, examples and visual scripting | Low-code ready-made workflows, full documentation and sample material | HPR is a code-first modular source toolkit without visual authoring, navigation or comprehensive character controller; should NOT be priced as equivalent |
| Ability System Kit, https://assetstore.unity.com/packages/tools/game-toolkits/ability-system-kit-385772 | $34.99, few ratings, attribute modifiers, buffs/debuffs, status tags, ability UI, two demonstrations, saving seams | Buff, attribute, cooldown, UI and editor configuration | HPR's ability runner has a smaller effect catalogue; its value is typed integration across weapons/events/inventory/saves, not feature parity |
| Inventory And Crafting System, https://assetstore.unity.com/packages/tools/game-toolkits/inventory-and-crafting-system-308906 | $10, unrated, drag-and-drop inventory UI, equipment, crafting, resource collection and save examples | Ready-to-use inventory and crafting screens | HPR has a far thinner inventory UI and item workflow; bundling ten libraries does not replace complete features |
| Ultimate Inventory System, https://assetstore.unity.com/packages/tools/game-toolkits/ultimate-inventory-system-166053 | Large established commercial offering from Opsive; shops, crafting, equipment, save/load, localization, hotbars and controller integrations | Extensive production inventory + support ecosystem | HPR is not competitive as a full inventory platform |
| Quest Machine, https://assetstore.unity.com/packages/tools/game-toolkits/quest-machine-39834 | $65, 73 reviews, source included, no-code UI and template examples, saves, mature integration ecosystem | Feature-rich questing, authoring and support | HPR does not provide quests, editor authoring or equivalent ready-made UX |
| WagSave, https://assetstore.unity.com/packages/tools/game-toolkits/wagsave-save-game-system-362364 | Supports save slots, autosave, format options, Editor toolset, compression, optional cloud; discloses its AI assistance | Independent save system suitable for many games | HPR adds only one explicitly opt-in, validated JSON example. It cannot be marketed as a full alternative to a save SDK |

## Actual product differentiation after v0.2 engineering

The previous 75-kilobyte suite candidate simply showcased six systems
with memory-only partial restoration and only a few buttons. The new
v0.2 candidate deliberately demonstrates all ten runtime modules in a
single coherent training arena: interactable medkit and key, inventory-
locked gate, stamina-dependent healing, area-damage ability wired through
physics overlap and typed events, deterministic enemy and weapon states,
metadata registry and composition root, complete snapshot with both memory
and opt-in local JSON save/load. A fresh Unity project must still verify
the buyer archive before any claims about its readiness.

This is **original cross-module integration work**, not ten identical
packages disguised as one. The technical niche is independent source-level
systems for experienced Unity C# developers who want documented, adaptable
contracts without large third-party dependencies, not beginners seeking
a complete drag-and-drop RPG engine.

The current demo still lacks professional character movement/aiming,
visual authoring, advanced inventory UI, complex combat behavior, enemy
navigation, multiplayer and serious game-ready persistence. Its value
and quality are probably below mature full toolkits. These limits must
remain visible in any description. An initial price in the low-teens
(USD) could be evaluated after completing media and quality gates; that
is a positioning hypothesis, **not a proven willingness-to-pay estimate**.
No real buyer conversions or customer reviews exist for our suite.

## Official rules verified October 31

https://assetstore.unity.com/publishing/submission-guidelines (last updated
October 23, 2026):

* Section 1.1.a requires professional technical **and marketing/visual**
  quality. Compilation alone does not satisfy this.
* Section 1.1.m limits publishers under six months old to **five**
  submissions per month, and older publishers to twenty, unless in the
  accelerated category. Check whether a new submission is quota-eligible
  in the live account rather than assume that rejected submissions do
  not count. The October nine were already submitted.
* Section 1.6.a requires truthful AI assistance disclosures in the specific
  AI description field, including actual tool names, content, modifications
  and additional value. Confirm the original module tool provenance.
* Section 1.6.d allows Unity to reject mass-produced AI content without
  substantial differentiation.
* Section 2.1.a requires one root folder; 2.1.f and 2.1.h prohibit
  duplicate offerings or unmodified resubmission of rejected packages.
* Section 2.3.a calls for comprehensive local documentation for code.
* Sections 3.1.a and 4.1 require truthful functional/limitation claims and
  active publisher contact information.
* Approval is discretionary. None of the above guarantees a new listing.

Commercial release gate: finished original code and runtime QA, genuine
Unity-captured screenshots and playable walkthrough, verified buyer archive,
nonmisleading description/AI disclosure, and known publisher quota/session
status. Do not upload a new draft to bypass prior rejection or to consume
limited quota before it is actually competitive.
