# HPR Unity candidate: actual Asset Store supply evidence, November 2

## Purpose and evidence limits

The current HPR Gameplay Systems Suite is still a **commercial NO-GO**
despite genuine Unity customer integration and QA progress. The aim of
this small, independently gathered research update is to test whether
"add a healing ability to an existing Unity game without replacing
controller/input/save assets" is a feature buyers cannot already obtain.

Only **original Unity Asset Store product listings, review pages and
official Unity publisher requirements** were used for the feature and
current listed-price evidence below. These are NOT purchased competitor
packages, verified installed customer workflows, official unit sales,
market-size estimates, conversions or user willingness to pay.

All values are page observations on November 2, 2026. Temporary sale
prices and review/favourite counts can change at any time.

## Direct competing supply

**Ability & Combat Toolkit (ABC), AT ABC Toolkit**

Primary URL:
https://assetstore.unity.com/packages/tools/game-toolkits/ability-combat-toolkit-155168

The listing reports **83 rating entries** in its overview, **1,225
favourites**, current sale **USD 39.12** from **USD 78.25**,
version **2.4.1**, released May 1, 2025. The vendor describes
**9 preconfigured weapons, over 50 abilities and 40 effects**, optional
own camera/controller integration, ScriptableObjects, attacks, buffs,
heal effects, advanced targeting, animation and AI. The description
asserts low/no-code startup for a variety of games. Those are seller
claims and have NOT been verified by importing ABC into our fixture.
This is nonetheless a serious already established functional
substitute for HPR's simple ability editor and handful of effects.
Do NOT claim HPR is unique in working beside a customer's controller.

**Game Creator 2, CW Catsoft Works**

Listing:
https://assetstore.unity.com/packages/tools/game-toolkits/game-creator-2-203069
Actual individual reviews:
https://assetstore.unity.com/packages/tools/game-toolkits/game-creator-2-203069/reviews

The listing gives **USD 79.99**, 418 summary ratings and about
2,400 favourites in a recent cached page. The separate reviews tab
reports **352 individual reviews**. These denominators are different
and not reconciled, and neither is a sales number. The seller offers
controller, camera, save, visual actions, conditions and extensions.
One actual review describes Game Creator 2 as enabling no-code scene
creation; another reviewer with ten years' Unity experience describes
substantial frustration customizing prebuilt modules and connecting
animations and inputs after initial example success. These are
**individual qualitative experiences**, not representative findings.

Review-specific source:
https://assetstore.unity.com/packages/tools/game-toolkits/game-creator-2-203069/reviews

**Ability System Kit, FG Faven Games**

Original listing:
https://assetstore.unity.com/packages/tools/game-toolkits/ability-system-kit-385772

The observed page reports **EUR 32.19**, **one favourite**,
"not enough ratings", version 1.0 and an original release date
June 10, 2026. It identifies ability cooldowns, attributes,
status effects and modifiers in its keywords. This demonstrates
another small/specialized competitor exists at a modest paid
price. One favourite cannot establish sales, lack of buyer demand
or quality, especially for a new listing.

**PackageLens — Package Import Review Tool**

Original listing:
https://assetstore.unity.com/packages/tools/utilities/packagelens-package-import-review-tool-375592

The observed listing reports **FREE**, version 1.0.0 released
June 4, 2026, six favourites and insufficient ratings. It is
marketed specifically for Unity package identity and conflict
reviews. Accordingly, packaging/asset-preservation checking
alone is a weak justification for a paid HPR SKU. It may be a
complement rather than a runtime gameplay substitute.

## Real current submission policies

Unity original publishing rules, last recorded update May 20, 2026:
https://marketplace.unity.com/publishing/submission-guidelines

Relevant hard gates:
- 1.3.c: packages submitted using Unity **6.5 or later** must support
  **URP or HDRP**. The current new archive's exact URP/new-only-input
  compile still lacks successful Unity Editor acceptance; v14 evidence
  alone is not enough for our internal QA signoff.
- 1.6.a-d: functional AI-assisted product development must be
  disclosed accurately, with specific tools and genuine added value;
  Unity may reject mass-produced insufficiently differentiated assets.
  The nine earlier weak rejections must never be bypassed.
- 2.5.g-i: no editor internal reflection, domain-reload-disabled
  Play mode support from Unity **6.6**, and no obsolete API warnings.
- 2.5.1.d/e: no unsolicited external redirection or unrelated
  package mutation.
- 3.1.a: marketing must disclose significant dependencies
  and limitations accurately. We cannot claim complete arbitrary
  controller/health integration or safe full uninstall.

## Verified current HPR value and gaps against supply

What our private QA actually proves is narrower and real:
the customer-owned ability can be copied independently, a single
AbilityRunner can be added to an existing scene player and later
removed with Undo/Redo, the original controller and many customer
assets/ProjectSettings stay byte-identical, and one healing effect
works in real Unity six point six Play mode. A newer proposal
serializes the native ActorStatsComponent binding and refuses
an inactive pool. Another proposed fix avoids globally saving
unrelated dirty customer assets when copying an ability.

However, **the latest two fixes are not in a newly compiled Unity
buyer archive** and the native-Stats integration still needs
actual new-scene save/reopen and Play-mode acceptance. No human
buyer has compared this experience against ABC or an equivalent
tool under the *same* real Unity project constraints. We have not
measured developer time, support cost, net value, failure rates
or willingness to purchase.

## Falsifiable benchmark before any commercial GO

Prepare one common realistic existing Unity game with its own
controller, input system, prefabs, save settings and unrelated
unsaved ScriptableObjects. Ask an experienced developer to add
a single configurable healing ability, preserve all original data,
then change, undo and remove it after a simulated package update.

Compare HPR with one direct paid ability-tool competitor using
the same clean initial project, equivalent functional behaviour,
and a repeatable QA recording. Record actual human installation
time, C# source edits, manual Inspector configuration steps,
unexpected user-data/GUID changes, Undo and uninstall failures
and need for vendor support. Without a competitor installation
and independent human tester, report **NOT MEASURED**, not zero.

**Decision remains NO-GO.** The current technical development
improves integrity, but no defensible incremental buyer benefit
per euro has yet been established. No product was purchased,
submitted, advertised, or publicly published for this research.
