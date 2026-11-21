# Unity publisher dependency-boundary tool: evidence and differentiation (21 November 2026)

Owner direction: pursue NEW, commercially relevant editor products, not only repairs to
Gameplay Suite. Candidate: **HPR Package Boundary Inspector** — one-folder
export and dependency disclosure preflight for Asset Store package authors.

Sources verified 21 November 2026:

* Unity's current submission guidelines (updated 23 October 2026) require
  external-package disclosure, accurate Unity Registry dependencies and, for
  UPM packages, correct manifest dependencies and metadata:
  https://assetstore.unity.com/publishing/submission-guidelines
* Unity's publishing workflow instructs authors to use a single top-level
  package folder and to run the official Asset Store validator, whose role
  is complementary to dependency boundary inspection:
  https://docs.unity.com/en-us/asset-store/publishing/asset-packages/upload
* Unity developer discussions on 4 October 2026 specifically request
  advice on optional FBX export and Input System dependencies; experienced
  authors recommend a blank-project import before each upload:
  https://discussions.unity.com/t/first-editor-tool-submission-what-should-i-expect-from-review/1738236
* The Asset Store now supports UPM alongside legacy asset packages, allowing
  versioned installations. Publisher enrollment may require identity
  verification and specific legal/business fields; eligibility unverified:
  https://docs.unity.com/en-us/asset-store/publishing/introduction
* Buyers and publishers discussed paid UPM in November 2026, including an
  unresolved built-in migration path from legacy Asset Store assets:
  https://www.reddit.com/r/Unity3D/comments/1xrox60/

Competition: RefSafe Pro already offers broad broken-reference detection,
used-by graphs and project cleaners. An additional general reference finder
would overlap strongly; this tool instead targets export *scope* and what
must be included/disclosed in a single-root package. Competitor evidence:
https://assetstore.unity.com/packages/tools/utilities/refsafe-pro-project-validator-cleaner-363422

Initial qualitative candidate ranking for **net return per owner hour**, not
sales or verified demand quantities: (1) focused package-boundary inspector
and preflight bundle extension: good automation feasibility, moderate
competition, limited need for content updates; (2) generic inspector
customization: observable community demand but entrenched established
competitors and high support burden; (3) general-purpose broken reference
finder/asset cleaner: severe overlap with feature-rich existing products,
including destructive operations and potential support liability.
Actual order counts, paid conversion and revenue remain **unverified**.

Release acceptance: native Editor compilation on Unity 2022 LTS and Unity 6,
real disposable imported .unitypackage, two positive external-dependency
fixtures and inside-root negative control, fail-closed caps, create-only JSON,
identity-manifest verification, Editor GUI inspection and truthful screenshots.
Do not submit externally before all tests and seller/rights approval.

Limitation: Unity AssetDatabase resolves only actual known references. This
scan is not a missing-GUID detector and cannot infer dynamic load paths,
package manifests, code runtime dependencies, or resource-rights clearance.
A "clean" scan never authorizes release without independent installation QA.

### Competitive reassessment after broader search, same date

An especially close competitor is **Build & Dependency Analyzer** (Basit),
released 9 November 2026, with selected-folder dependency analysis and JSON
reports, advertised at **$14.99** on temporary 50-percent promotion from
$29.99. The listing shows insufficient ratings to infer sales volume:
https://assetstore.unity.com/packages/tools/utilities/build-dependency-analyzer-413664

Several established free and paid products also offer reference inspection:

* Free Reference Finder (PixeLabs), 2 April 2026:
  https://marketplace.unity.com/packages/tools/utilities/reference-finder-asset-dependency-link-scanner-359938
* Dependency Inspector Pro, advertised September 2026 at launch pricing
  $12.50 versus $25: https://discussions.unity.com/t/release-dependency-inspector-pro-instant-reference-scanner-pre-build-guard-launch-sale-12-50/1737057

This substantially lowers confidence in a **standalone** dependency scanner
at a meaningful price. Commercial recommendation: treat the first version as
a native-tested prototype and seek a distinct publisher-specific upgrade
path: single-folder manifest declaration guidance, exact export identity,
CI fail-closed checks and clean-project import receipts. Do not direct the
shared seller to create a listing until that differentiation, GUI/screenshot
quality, buyer rights/license and economic value are independently validated.
Attribution: prices are listing observations, not confirmed transaction or
net-owner revenue evidence.

### Additional independent competition / buyer evidence on 21 November

An especially important direct competitor is **Release Check Pro - Game &
Asset Validator** (Unity Asset Store, October 2026). Its author explicitly
advertises asset-folder *external dependency* detection, missing serialized
references, scene/prefab inspection, read-only Editor analysis, responsive
UI, progress, configurable thresholds, and release-readiness reporting.
This overlaps almost entirely with a simple package-boundary checker:
https://assetstore.unity.com/packages/tools/utilities/release-check-pro-game-asset-validator-401728

Another **Project Validator** launched in October 2026 with twenty-one rules,
JSON/CSV export, progress/cancellation, optional fixes and asset-quality
inspection, limited to Unity 6000.3 or newer:
https://assetstore.unity.com/packages/tools/utilities/project-validator-410282

In the dated November 15 Unity publisher discussion, self-reported low sales
for new generic systems and buyer concerns over bloated/non-extensible or
AI-assisted code reinforce the need for durable verified differentiated
software rather than a basic replacement for existing inspectors. This is
**anecdotal, not representative market volume or revenue**:
https://www.reddit.com/r/Unity3D/comments/1xwpb73/

Therefore the basic standalone product has a **poor current revenue case**.
The differentiating follow-on is exact old/new version GUID identity
preflight, fail-closed CI-friendly reports, reproducible clean-buyer imports
across editor generations, and a documented upgrade safety workflow.
Even this enhanced prototype needs sales-side pricing and buyer-demand
validation; neither feature count nor source tests demonstrate purchases.

### Wider Unity product opportunity review, same day

Real developer posts and current competition change the relative ranking:

1. **Version-aware publisher preflight with verified clean-project and populated-project upgrades**: the existing HPR audit/Inspector code reduces development cost and exact old/new GUID changes have reproducible value. Commercial potential relative to our codebase is **first among observed near-term options**, but a standalone check is clearly saturated; revenue and buyer conversion remain **unknown**. Buyer interest has to be verified by the shared seller before spending substantial further development effort.
2. **Targeted FBX animation-import identity audit/diagnostics**: Unity users reported duplicate imported clip internal IDs that break assigning clips, plus order-of-operation bugs when merging model clips. A safe read-only diagnostics utility might offer a sharper problem focus than a general animation toolkit. **Research/prototype only**: data fixtures, Unity API coverage, rights and breadth of demand unverified. Source:
   https://discussions.unity.com/t/duplicated-internalid-when-creating-animation-clips-on-an-imported-fbx/1716388
   https://discussions.unity.com/t/how-to-automatically-combine-animation-clips-after-model-import/1730293
3. **Complex project-specific game systems with built-in migration, samples and long-term guarantees**: higher possible selling price but higher engineering/maintenance burden; low confidence until buyer willingness and uniquely superior gameplay are established. Concrete threads report poor sales/discoverability for generic system packs and demand mature, proven systems.
4. **Generic dependency validators, editor shortcuts, hierarchy/inspector enhancers, animation-event timelines and lightmap batch tools**: poor greenfield opportunity due to many established free or advanced commercial competitors. A November 2026 Editor utility listing already offers a 21-rule project validator with progress and JSON export. For animation events, Animation Event Studio already provides timeline edit, persisted imported-model events, batch application, validation and extensive native tests:
   https://assetstore.unity.com/packages/tools/animation/animation-event-studio-383238
   https://discussions.unity.com/t/released-batch-lightmap-baker-bake-all-your-scenes-in-one-unattended-run-validation-changed-only-rebakes-ci-support/1731834
   https://www.reddit.com/r/Unity3D/comments/1vrslwk/

This is a **feasibility and competitive-intensity ordering**, not a revenue forecast. No listing conversion data, paying beta buyers, operating margin, or measured market size was found. Importer-internal ID editing is potentially destructive and would require independent owner approval before any real project mutation; begin with read-only verification if explored.
