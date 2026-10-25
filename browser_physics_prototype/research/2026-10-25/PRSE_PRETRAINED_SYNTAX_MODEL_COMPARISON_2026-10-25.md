# PRSE — matched pretrained syntax model versus deterministic semantic scene interpretation

> **Later source/physical truth audit:** The [grounded current-fact and re-entry study](PRSE_GROUNDED_FACTUAL_WORLD_RESEARCH_2026-10-25.md) deliberately refuses unverified relations in factual narration, separately scores independent source annotations, and preserves a one-frame restored contact-manifold failure. The earlier text/physics model comparison remains unchanged.

25 October 2026 · Existing Nitro Games research branch

The owner’s **primary** PRSE research objective remains the bidirectional transformation of a persistent literary/semantic world into one authoritative three-dimensional physical world and back: source-grounded object identities and relations, real physical events, truthful observer-relevant changed prose, economic offscreen causal evolution, and consistent rematerialization. Habit learning, scripted walking and fence jumps are lower-priority separate work. Preserve the original PRSE acronym expansion as **UNKNOWN**: the August 13 recording explicitly says the speaker forgot it.

## Why this study was necessary

The prior fixed scene parser could create stable physically valid worlds but hardly preserve external source relationships. A bounded coordinate optimizer increased independently annotated object-relation matches from **22 to 30 of 478** in the original one hundred human SceneEval descriptions, and from **17 to 22 of 743** in one hundred systematically sampled, partly machine-authored descriptions. That left uncertain whether better NLP, rather than better 3D placement, was the immediate bottleneck.

The primary scientific reference is **SceneEval**, Tam et al., WACV 2026, https://doi.org/10.1109/WACV61042.2026.00710 and https://github.com/3dlg-hcvc/SceneEval. Its original SceneEval-500_v250610 ZIP has SHA-256 **2948037f497c81cb2ce8241010c8d93250248217ca9961aa33e59092196b3676**, verified against the official author release. SceneEval distinguishes explicit source object counts/attributes/relationships from physical plausibility such as collisions/support/navigability. The first 100 source descriptions are manually authored; the additional 400 are semi-automatically generated or extended with a vision-language model.

For a low-cost actual pretrained semantic-syntax alternative, used the official CPU-oriented **spaCy en_core_web_sm version 3.8.0** with its real pretrained English dependency parser, compatible with the shared installed spaCy 3.8.4 runtime. Official model license MIT and meta: https://github.com/explosion/spacy-models/blob/master/meta/en_core_web_sm-3.8.0.json . The exact official 12,806,118-byte model wheel has SHA-256 **1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85**. It was stored and extracted under owner-private Nitro research data, loaded by explicit path with one CPU thread; **no shared Python package installation, model training, GPU, Torch generation or production LLM call occurred**. The model parse stage processed the 500 descriptions in about **8.7 seconds after initialization**, measured once on a busy Nitro host. Do not present this as a generative language model or production latency.

## Controlled comparison and source separation

First rechecked /data/infra/AGENTS.md, existing research branch and upstream HEAD, canonical Games main with 83 unrelated dirty entries, active PRSE and busy other workloads. Reread current Infra games/world_and_generation.md and semantic_physics_text_loop.md and the original owner-recording excerpts from August 13 and October 9. No prior external effects were repeated.

The deterministic baseline was the **unchanged, frozen** text-only parser from prior research. Three arms shared **identical entity mentions, categories, quantities, attributes, source IDs and entire source text**:

- Deterministic lexical parser, original candidate relationships.
- Pretrained spaCy dependency parser plus conservative transparent mapping from syntax arcs to spatial relationships; no annotation-trained relation classifier.
- Union of unique deterministic and spaCy-proposed relationships, without a gold-based selector.

The model-based interpreter could propose a different set of relationships, but did **not** change noun taxonomy, infer novel object dimensions, receive SceneEval gold annotations, execute player moves or override authoritative physics. Complete frozen 500-scene proposals were saved privately **before** any new gold scoring.

Independent scorer opened SceneEval annotation labels after proposals were frozen. Its relation scoring accepts an unordered object-type pair and relation name, matching the earlier study’s **optimistic** convention; it does not establish exact argument direction, per-instance support, image fidelity or full narrative entailment. A separate strict-as-encoded-field comparison was recorded, but the dataset's annotation relation order cannot safely be equated with ordinary English subject/object semantics, so it is **not treated as definitive directional accuracy**. Prior aggregate baseline evaluation and inspection of some source examples mean this is exploratory, not a pristine blind holdout.

Next, all three arms were evaluated through the **same frozen bounded geometry search**, native PRSE GameCore/Rapier 3D steps (18 per scene), typed relation grounding, full saved entity identity and original prose preservation. Same source IDs and solver limits: two repair sweeps, up to 150 proposed candidate placements. Physically unvalid proposals were rejected, not teleported into validity. Reused the old deterministic physical results unchanged, and ran **four new physical batches**: dependency and union for human IDs 0–99, and dependency and union for assisted IDs 100,104,...,496. The official SceneEval gold labels were not available to the interpreter, geometry optimizer or physics code.

## Results: model helps selectively but **general understanding is still very weak**

First, the **text-only object-relation extraction** correct against gold (still direction-insensitive), before physics:

| Source group | Deterministic | Dependency-only | Union |
|---|---:|---:|---:|
| 100 human-authored | 40 / 478 | 37 / 478 | 49 / 478 |
| 100 assisted sample | 24 / 743 | 31 / 743 | 32 / 743 |

The combined parser generally recovers more source relations but produces more proposals that are not credited by the official labels. It is not calibrated to abstain on uncertain implicit relationships or coreference, and no general textual entailment oracle has been built.

The more important measurement is **gold object relations that remain satisfied in actual physical GameCore scenes after the complete transformation**:

| Source group | Deterministic | Dependency-only | Union |
|---|---:|---:|---:|
| Human-authored scenes | **30 / 478** | **33 / 478** | **35 / 478** |
| Assisted source scenes | **22 / 743** | **21 / 743** | **23 / 743** |

The improvement is **5 extra matches out of 478** human annotated claims and just **1 extra out of 743** assisted annotations. Human optimistic grounded recall went from **6.28% to 7.32%**; assisted from **2.96% to 3.10%**. Despite many additional self-consistent proposed spatial relations, they generally do **not** match more source meaning. Syntactic dependencies do not solve coreference, multi-object scope, nested relations such as *inside vs on*, or general room/asset semantics.

The number of **physically valid and correctly saveable scenes** also matters:

| Source group | Deterministic | Dependency-only | Union |
|---|---:|---:|---:|
| Human-authored | 97 / 100 | 98 / 100 | 97 / 100 |
| Assisted sample | 99 / 100 | 99 / 100 | **97 / 100** |

Thus the union interpretation actually causes **two additional rejected assisted layouts** despite increasing the number of candidate relations. No save failures occurred in the accepted cases, and their source prose and object IDs were retained. This shows the danger of accepting all model-generated relationships without confidence/calibration and conflict resolution.

Some annotated **room** relationships improved: 39→45→49 in the human sample, and 21→22→25 in assisted scenes across deterministic→dependency→union. These still do not verify actual architectural walls, doors, appearance or observer viewpoints. The existing renderer and physical layout dimensions remain provisional.

A paired 4,000-resample **scene-level bootstrap** was run with fixed seeds, resampling scenes rather than individual correlated annotations. Union minus deterministic grounded *object* recall was **+1.05 percentage points** on human descriptions, with a conditional 95% bootstrap interval approximately **0 to +2.23 points**. In the assisted sample it was **+0.135 points**, interval approximately **−0.45 to +0.76 points**. Dependency-only sometimes made the score worse. These intervals include no improvement, and because SceneEval is curated, not a random sample from future PRSE stories, they cannot establish general statistical superiority.

The new syntactic model’s source interpretation therefore offers **narrow positive cases and substantive negative generalization evidence**. The most important research conclusion is that adopting a lightweight neural syntactic parser is **not** enough to make PRSE's literary-space↔physical-space conversion faithful.

## Limitations and what is next

The syntax model knows general English grammar but not true object/coreference identity, affordances, material properties, room topology, scaled physical dimensions, semantic negation scope, or the difference between a book *inside* a bookshelf and *on* one. It also cannot guarantee that the language it might later generate is physically true. No trained LLM scene interpreter, native audio model, human usability study or production deployment was evaluated in this continuation. The earlier observer-specific causal raycasting, event-time witness tests, native offscreen clock synchronization and rematerialized-ash studies remain valid but are different stages.

Published **Holodeck**, Yang et al., CVPR 2024, https://openaccess.thecvf.com/content/CVPR2024/html/Yang_Holodeck_Language_Guided_Generation_of_3D_Embodied_AI_Environments_CVPR_2024_paper.html , demonstrates a stronger architecture: language-based structured relational proposals followed by spatial optimization. **PAT3D**, Lin et al., ICLR 2026, https://proceedings.iclr.cc/paper_files/paper/2026/hash/f35d2be7bc4da374557da1f5ef06eeeb-Abstract-Conference.html , similarly combines scene construction with physics-guided improvement. Neither was reproduced on the PRSE dataset here. A proper next test is a **genuine constrained scene-semantic model** that outputs typed entities, attributes, relative spatial relationships, negation, reference IDs and source spans on a fixed source-blind benchmark, then passes exactly the same GameCore/physics/saving/observer checks. It should be run only when spare production model slots are positively verified or on a dedicated CPU-only allocation.

Other unresolved original owner questions still include source-grounded *literary quality* after physical collisions, visible versus offscreen physics interpolation, persistent realistic damage/fracture/fire, occlusion and observer-specific knowledge integrated into all text/2D/3D presentation modes, multi-region clock consistency with active actors, and safe integration with the concurrent dirty Games main checkout. The correct status is **PARTIAL**.

## Reproduction, source and artifact privacy

All source code and aggregate metrics live under existing browser_physics_prototype/research/2026-10-25:

- prse_spacy_relation_interpreter.py — pretrained syntactic arcs → conservative scene relations.
- prse_syntax_model_proposals.py — freezes the exact 500-scene proposals using private official model data and the prior fixed source inputs.
- prse_syntax_model_relation_score.py — independent gold scoring and direction-sensitive caution.
- prse_syntax_model_physics_comparison.mjs — same GameCore spatial search, physics and save/re-entry as previous deterministic experiment, with isolated method/source options.
- prse_syntax_physics_gold_audit.py — independent physical source-relation gold comparison.
- prse_syntax_model_paired_uncertainty.py — scene-level resampling uncertainty.
- prse_syntax_model_evidence_verify.py — read-only verification of source ZIP and spaCy model digests, exact source ID sets, unchanged nouns/counts, physical save/reentry, raw SHA files and reported metrics.
- versioned public-safe aggregate JSON results and the earlier independently committed deterministic baseline.

Complete raw original descriptions, model proposal JSON, annotated per-case scores and full physics traces reside in owner-private Nitro research directories with mode 700 folders/600 files and exact SHA in public-safe manifests. Do **not** commit model wheel files or redistribute full SceneEval descriptions. Old source datasets, earlier negative fixture results and the concurrently dirty Games main stay untouched.
