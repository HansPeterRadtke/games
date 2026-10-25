# PRSE: object-count gains fail to reconstruct original physical scene relationships

25 October 2026 — continuation of original owner PRSE semantic/literary world ↔ authoritative 3D ↔ semantic/literary world research.

## Original owner research priority and constraints

The preserved August 13 and October 9 original PRSE recordings and current Infra games/world_and_generation.md and games/semantic_physics_text_loop.md define the core requirement: ordinary literary descriptions are the persistent world; they must become real positioned/scaled, interacting three-dimensional entities near the player, undergo actual physical and semantic events, and translate back into truthful persistent story state. Object identity, damage, offscreen causal continuation, later rematerialization and observer knowledge must agree. Optional learned player habits and scripted jumps are secondary. The historical working acronym expansion was explicitly forgotten and is UNKNOWN.

Read Nitro Infra AGENTS.md first. Verified prior research commit 42c609a was already at the intended origin remote and the research worktree clean. Canonical Games main still had 83 other agents' dirty entries. Live PRSE, Nitro inference/financial/Chrome/commercial Blender workloads were protected. New analysis used only low-priority CPU in an isolated Games research worktree. No model training, GPU inference, live service change, calendar event or original recording modification.

## Why this test matters

The immediately previous source-quantity audit found that the original GameCore scene compiler satisfied only 565/1,237 independent author-annotated SceneEval object-count clauses, despite internally matching 844/844 counts proposed by its own parser. The CPU pretrained English noun chunk model found many missing types. Adding 1,110 real native Rapier but tiny generic collision-box placeholders in 197 previously accepted source scenes increased independent source type-count satisfaction to 972/1,237. A strict existing physics-size catalog added only 17 physical bodies and improved counts to 571/1,237. Generic objects have no credible class-specific geometry, materials or affordances; counting them is not enough to call a scene correct.

This follow-up measures the outstanding spatial/causal problem: do these newly created real bodies also satisfy the ORIGINAL literary descriptions' physical relationships, particularly support and actual interobject contact?

Independent reference: SceneEval, Tam et al., WACV 2026, https://openaccess.thecvf.com/content/WACV2026/html/Tam_SceneEval_Evaluating_Semantic_Coherence_in_Text-Conditioned_3D_Indoor_Scene_Synthesis_WACV_2026_paper.html, explicitly separates prompt object counts, attributes and relations from support, collision and navigability. Holodeck, Yang et al., CVPR 2024, https://openaccess.thecvf.com/content/CVPR2024/html/Yang_Holodeck_Language_Guided_Generation_of_3D_Embodied_AI_Environments_CVPR_2024_paper.html, uses explicit layout constraints plus real 3D asset retrieval. PhyScene, Yang et al., CVPR 2024, https://openaccess.thecvf.com/content/CVPR2024/html/Yang_PhyScene_Physically_Interactable_3D_Scene_Synthesis_for_Embodied_AI_CVPR_2024_paper.html, addresses physical constraints and interactive scenes. None of these systems was reproduced locally here.

## Frozen input and actual GameCore/Rapier scene comparison

Exactly the SAME external source description IDs were used: first 100 human-authored SceneEval prompts and every fourth of the remaining 400 assisted descriptions. Three real native GameCore/Rapier world methods were independently reconstructed from their previously frozen source, class counts, instance IDs and placement algorithms WITHOUT reading SceneEval relation annotations:

- Original baseline: pre-existing recognized nouns, class-size approximations and bounded spatial optimizer.
- Open-vocabulary generic: original plus the exact previously frozen 1,110 new source-linked candidate bodies using small 0.24 x 0.28 x 0.24 metre dynamic generic collision boxes in empty floor positions.
- Existing catalog only: original plus the 17 source-linked categories with existing dimension/rigid-body definitions; no unknown-size fallback.

All valid worlds ran through the SAME native GameCore/Rapier simulation. This replay captured their actual post-tick three-dimensional positions, physical sizes, orientations, source instance IDs and real object-to-object Rapier collider contact manifolds in owner-private files. Zero annotation-derived placement adjustments occurred.

There was a FIRST REPRODUCER ERROR, deliberately retained: the initial script checked sampled assisted-source spans against the sampling index, not their actual SceneEval IDs. This made 71 generic and four catalog replay rows fail source evidence validation; it was a script indexing error, NOT a physical scene failure. Its raw v1 was preserved untouched. Corrected v2 reads the actual IDs and independently reproduced all 197 previously accepted scenes for each arm without runtime/geometry failure. The original three geometrically rejected source scenes remained unverified and were not silently counted as successful.

| Recreated authoritative 3D scenes | Original | Generic new nouns | Strict catalog |
| --- | ---: | ---: | ---: |
| Physically accepted native GameCore scenes | 197 | 197 | 197 |
| Real native non-wall physical bodies | 938 | 2,048 | 955 |
| Newly materialized provisional bodies | 0 | 1,110 | 17 |
| Measured real interobject Rapier contact pairs | 11 | 11 | 11 |

This is a striking NEGATIVE: the extra bodies did not add physical support contacts. They were independently placed on the floor, not necessarily in the spatial arrangements the story described.

## Independent author SceneEval spatial annotations after native geometry freeze

After the exact version-two physical worlds and contact data were saved, a separate independent scorer opened official SceneEval-500 author OORel labels. The original author-provided SceneEval v250610 ZIP has unchanged SHA-256 2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676.

The 197 accepted descriptions contain 911 annotated object-to-object relationship requirements. Current credible physics predicates can evaluate only 512 of those kinds: a native contact and upright planar support for ON (author gold represented as substrate then supported object), and three-dimensional Euclidean AABB surface-distance checks for NEXT/NEAR/BESIDE/ADJACENT. The remaining 399 relation clauses involve directional camera frames, containment with absent real container cavities, object facing, multi-object arrangements or architecture not modeled with sufficient semantics. They are recorded as UNKNOWN/ABSTAIN, NOT declared false.

The evaluation intentionally uses a generous object-TYPE-pair existential matching rule with enough physical instances, rather than proving the source referred to a particular uniquely identified 3D body. It cannot certify full literary entailment. Physical ON needs native Rapier contact plus support-plane/footprint alignment; NEAR can accidentally match when floor-grid bodies happen to be close even if the source meant a very different location.

| Native GameCore versus original source relation | Original | Generic nouns | Catalog only |
| --- | ---: | ---: | ---: |
| Independently annotated source relationships | 911 | 911 | 911 |
| Relationship clauses of physically evaluable kinds | 512 | 512 | 512 |
| Both required source type categories physically present | 95 | 335 | 99 |
| Physically satisfied source-type relation, generous score | 18 | 33 | 18 |
| Those requiring real Rapier ON support/contact | 3 | 3 | 3 |
| Proximity-only matches | 15 | 30 | 15 |
| Unsupported source relation kinds, explicitly unverified | 399 | 399 | 399 |

The original human-source group had 334 official relations, 150 belonging to supported predicate families. Generic candidate insertion increased physical matches from 11 to 14. The sampled assisted-source group had 577 official relations, 362 of supported predicate families, and generic insertion increased physical matches from 7 to 19. The strict existing category-size materialization produced no source-relationship improvement at all.

The extra FIFTEEN matches in the generic arm were only loose proximity labels, not new physically supported ON placements. All three methods yielded exactly THREE source ON constraints with native contact evidence. This demonstrates that recovering noun types and increasing physical instance counts cannot be claimed to preserve a source literary scene's relational/causal meaning.

A separate paired 4,000-resample SOURCE-SCENE bootstrap on the same already inspected corpus gave generic-minus-original physically testable source-relation gain +2.0 percentage points in the human source subset (conditional 95 percent interval 0 to +4.5 points) and +3.31 points in the assisted subset (about +1.71 to +5.07). These are benchmark-conditional, not population generalization estimates; the gains can arise from incidental floor-grid proximity, and contact-supported author relations did NOT improve.

## Missing GAME assets beyond the noun parser

A read-only inventory of this isolated Games repository found no TRACKED renderable interactive 3D mesh files in common GLB, glTF, FBX, OBJ, STL, Blender or USD formats. Its existing generated semantic-asset-manifest is a CC0 PNG sprite selection, not a physical metric 3D asset catalog. This does NOT imply that the owner has no separate 3D assets in other production projects or machines; it is an audit of the assets currently present in this Games worktree.

The game's existing limited class dimension table is an approximation using simple rigid bodies. Even when a noun has a rough size, there is no general guarantee of a correctly shaped collision mesh, cavity/container, supportable shelf, door, usable lever, natural pose or correctly aligned visual artwork. Flat 2D sprite selection also cannot supply that physical meaning.

## Original owner conclusion and next valid experiment

A real PRSE general-purpose scene translator must connect these separately verified stages, without silently skipping any: source-aware discourse/quantification and persistent instance identity, validated category/shape/size and asset retrieval or generation, source-conditioned geometric relations and contact/containment optimization, ONE actual native 3D physics/event authority, observer-specific causality, and later semantic/literary continuation with consistent offscreen processes and save/re-entry.

This study finds not merely missing nouns but the absence of source-conditioned physically valid relationships. Generic placeholder generation satisfies some count constraints while providing almost no new scene-support constraints. Tightening class-geometry admission prevents fake objects but does not solve source relation fidelity. The correct next research target is a geometry/affordance-aware, source-span-linked relational instance representation that can **abstain when no suitable physical asset or constraint solution exists**, rather than silently inventing floor boxes. Then evaluate on genuinely fresh human source scenes with real supported objects and measure count, relationship, physical plausibility and returned observer/literary factual accuracy SEPARATELY. Compare model proposals with deterministic physical solver validation only when production inference is positively idle.

The source benchmark was previously examined during earlier work; this is NOT a pristine blind model-selection challenge. No capable generative LLM was run, no new physical 3D assets downloaded, no human language-quality rating, no production game deployment, and no general unrestricted literary-to-3D-to-literary solution was demonstrated. The owner objective remains PARTIAL.

## Reproducible artifacts and negative evidence preservation

All new owned source and public-safe aggregates belong in the existing browser_physics_prototype/research/2026-10-25 area:

- prse_post_asset_spatial_snapshot.mjs reconstructs prior frozen source-driven GameCore worlds and records authoritative post-tick rigid-body positions, dimensions and native interobject contact pairs WITHOUT opening official gold labels.
- prse_post_asset_relation_input_200_aggregate_v1.json and v2.json preserve the initial assisted-index research replay error and fully corrected v2 physical data source hashes separately.
- prse_post_asset_spatial_relation_gold_audit.py independently scores official SceneEval OORel source annotations only AFTER the new native physical outputs are frozen, with explicit unknown/unsupported labels and strong orientation/geometry limitations.
- prse_post_asset_spatial_paired_uncertainty.py records source-scene-level resampling uncertainty for the weak proximity-inclusive physical relation proxy.
- prse_post_asset_spatial_relation_evidence_verify.py independently verifies the exact source sets, v1 bug/v2 correct replay, actual body/contact counts, author source-label outcomes, 2D-only tracked Games assets, private data permissions and SHA-256 evidence.
- This dated project report and separate aggregate/manifest JSON contain no full copied third-party prompt corpus or per-source author gold snippets.

The complete per-source geometry, real native contact manifolds, individual gold source relation labels and the original negative v1 reproduction remain owner-private under /data/var/games/prse_semantic_research/runs/2026-10-25-source-relations-post-asset, directory mode 700 and files mode 600. Original owner recordings, other agents' dirty Games main, prior scientific negative findings and commercial GPU production remain untouched.

**Outcome: a substantial NEGATIVE real-physics finding about missing relational meaning. PRSE's desired literary ↔ authoritative 3D ↔ coherent changed literary world has necessary partial foundations but remains unproven.**
