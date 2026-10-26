# PRSE independent literary-to-native-3D evaluation — follow-up round 1, 26 October 2026

## Direct answer to original owner problem

PRSE **can run real authoritative Rapier three-dimensional physics with persistent IDs**, and can preserve source/native state through save and reentry on a bounded previously studied SceneEval sample. It **cannot yet reconstruct arbitrary human-described indoor worlds** with correct instance/category inventory, architectural topology, object-specific dimensions/geometry, support positions and faithful observer-limited literary updates.

This round obtains **an entirely separate, independently human-written/annotated corpus**, runs **actual GameCore/Rapier simulation** for all source texts under a **same-native-body/ID/dimension/size controlled comparison** and uses independent reference scene JSON and human constraint labels **after predictions were immutable**. Previous denied random-feasible-parent placebo is not rerun or emulated. Player habit/macro work was not performed.

Source: [LEGO-Bench public Apache-2.0 dataset](https://huggingface.co/datasets/LEGO-Eval/LEGO_Bench), by Hwangbo et al. and updated Kang et al., *Apples on the Table?* (EMNLP 2026). It contains 130 human-authored complex natural-language instructions, 1,250 independently segmented/typed constraints and 130 manually constructed reference 3D environments. Paper Appendix B.2 reports trained human annotators individually writing instructions, annotating constraints and building reference scenes. The actual dataset reference JSON is much richer than SceneEval in room topology and named instance positions and rotations; it does **not** supply the object mesh geometry and calibrated object dimensions without an additional separate 3D asset corpus.

## Source and immutable evidence chain

Research owner: Nitro. Isolated Games branch: `research/game-skills-hidden-20261024`, prior remote-verified head `43c52f9`. Original August 13 and October 9 source recordings and current Infra/game guidelines checked, as were the prior new-chat research reports, earlier invalid v1/v2/v3 and good v4/v5 controls, the prior extra 300 SceneEval assisted-only result, live project worktree state, and other worktree pointers before changes.

Download origin: exact official LEGO-Bench repository (Apache-2.0 data), official `data/full_data.json` plus `data/data_0/data_0.json` through `data/data_129/data_129.json`; complete bytes and per-scene SHA checksums preserved owner-private on Nitro. The official annotation JSON is 504,231 bytes, SHA-256 `c4cab948b923b522b9ba4991e167e1c5c7d503786f2b2e5c11a64dab89113c21`. All 130 reference scene JSONs were captured as released (about 6.87 MB, mode 0600).

SOURCE-ONLY proposer reuses unchanged earlier Games lexical parser, its pre-existing category/quantifier mapping, downloaded spaCy English 3.8 general syntactic dependency model and the original LEGO instruction strings. Its Python file accesses only the `instruction` field, **not** the `constraints`, `labels`, or any reference objects. Input paths and source SHA for each of 130 examples are stored in an owner-private frozen raw file. Proposals are frozen **before** any native author score or reference scene lookup; 392 recognized scene-local lexical object kinds, 33 deterministic lexical ON candidate relations, but the existing pretrained ON grammar obtained only **2 proposals across 2 descriptions**, with 123 syntax/mention abstentions.

The original PRSE `compileProposal` and `repairScene` generated **real native GameCore/Rapier worlds** with the already frozen catalog/class dimension approximations, not imaginary AABB slots. Each scene is compared with:
1. **CONTROL:** neutral original source-linked category/quantity objects at deterministic floor-grid positions; source relations suppressed for layout only.
2. **LEXICAL:** exact same scene and bodies with prior deterministic source lexical relation compiler/repair.
3. **PRETRAINED ADDITION:** exact lexical scene plus pre-frozen pretrained ON proposals subject to the unchanged support-feasibility and non-overlap rules.

All arms use exactly the same original source text, native GameCore physics, initial underlying object IDs, types and collision dimensions; only independently sourced relative placement proposals can move existing objects. Each arm executes 38 true native physics ticks and validates save/reentry against real rigid-body IDs and Rapier collider contact pairs. The same-body preflight checks source, types, shape, size, IDs and all unproposed positions before the alternatives. No generated body or extra contact is counted merely because a nominal `supportId` says it should exist. This is an honest frozen **same-body grid negative control**, **not** the previously denied random-feasible-support placebo. No author annotation enters layout or selects an object, position or candidate.

### Full native physics comparison

| Measure | Neutral grid | Source lexical placement | Lexical + pretrained |
|---|---:|---:|---:|
| Physically accepted/saved human-source scenes | 130 | 130 | 130 |
| Native nonwall bodies across scenes | 575 | 575 | 575 |
| Actual nonwall Rapier contact pairs | 0 | 4 | 4 |
| Additional pretrained physical supports | — | — | **0** |
| Original author source/history and native contact save preserved | yes | yes | yes |

Lexical layout moved 67 source-linked physical objects; four pairs genuinely contacted. The pretrained proposals made no further physical placement, because one encountered an already existing support and the other a fixed/nonmovable supported child. The pretrained and lexical native contact sets were exactly identical in **all 130 scenes**, an unambiguous negative control. Total CPU test including 390 true physical scene executions and 390 save/restores was **40.88 seconds**, nice-19, with no GPU or production service changes. End-to-end linguistic LLM inference latency was **not** measured.

### Independent human annotations and separately authored reference worlds

After native outputs were frozen, a second scorer opened all 130 original author-labeled constraint sets, with exactly:
- 494 Object Placement clauses;
- 291 Object Selection clauses;
- 272 Floor Layout clauses;
- 193 Material Selection clauses (total 1,250).

Official reference scenes contain **295 different rooms**. The existing PRSE compiler always constructs a single provisional room. **95 of 130 source scenes** therefore have an *independently established multi-room topology mismatch*. A source-relational parser limited to furniture within one generic box-shaped room cannot repair this by increasing object-object contacts.

Reference JSON has **6,844 objects in total**: **3,894 named instance labels** and **2,950 without usable `object_name` category**, plus room/wall entities. Actual PRSE source-linked nonwall native body inventory is **575**. Under the **frozen exact canonical category normalization** (not exhaustive semantic synonyms), only **239 of 3,894 named reference instances** can be paired with an actual body of the same scene/category, even before checking individual instance identity, room membership, scale, shape or pose. Thus **3,655 named instances are unmatched under this exact-name metric**, while **336 instantiated native bodies have no corresponding explicitly named category**. Those 336 are **not proven false positives**: there are 2,950 unnamed reference instances, category synonyms and unspecified decor. The 239 are likewise **not automatically true positives** for exact instance identity or physical shape. The fixed-name same-category count ceiling is a useful upper bound under this particular restrictive evaluator, not universal semantic correspondence.

Of 2,050 scene/category groups with independently named reference instances, only 149 have at least one PRSE native body of the same canonical kind. This shows dramatic inventory failure without relying on the unreliable assumption that all source objects have perfect explicit instance IDs.

The human-curated gold has **86 Object Placement clauses containing “on”**. Only **16** meet our independently post-frozen *mechanical* requirement for an extractable child and parent of two distinct named physical-object types; the remaining 70 are UNKNOWN for exact directed contact evaluation, including walls/floors, unsupported nouns and ambiguous instances. On those 16 cases, a stricter independent native geometry scorer requires a directional child/support pair, real Rapier contact manifold, upright collision boxes, an enclosed X/Z footprint and a small actual top-face Y gap. Results are **0 of 16 neutral**, **4 of 16 lexical**, and **4 of 16 lexical plus pretrained**. In all four supported cases, reversing parent and child correctly fails. The other **12 mechanically extracted author ON clauses are not physically supported**, conditional on automated type-pair parsing. Author-annotated **individual** referent linkage is still unavailable; these are *type-pair* matches rather than proven exact-reference correctness.

The preliminary v1 scorer counted unordered collider type pairs, which was inadequate for “on” truth; **v2 adds actual directional top-face geometry and independently verifies the reversal negative**. Preserve v1 and v2 evidence separately rather than silently replacing prior consumed results.

## What is known, unknown, and next defensible choice

**Known false negatives and failures:** the multiroom failure is independently certain for 95 of 130 sources. Strict top-support evaluation fails 12 of 16 mechanically extractable positive author examples. Named-instance exact-type/count mismatch is at least 3,655 of 3,894 named reference instances under the explicitly limited frozen normalization (not necessarily literal source-entailed false negatives). The pretrained source parser added **no** correctly supported new relations versus the lexical arm on this independent corpus, despite two source-only ON candidates.

**True false-positive contact rate cannot be established** from these data because the official human constraint set is *positive*, not an exhaustive per-object ON negative list; most scene asset names are missing, exact referent/coreference labels are incomplete, and unknown or arbitrary extra geometry should not be scored as independently false. It would be scientifically wrong to call 336 unmatched bodies false positives or to declare the four correct type-pair contacts definitively correct unique referents. Likewise, reference scene world coordinates and rotations exist but correct metric-scale/shape validation needs the matching Objathor 3D mesh and collider inventory and room-level alignment; these were not downloaded or fabricated. No new human reference for updated observer-limited prose, physical event recall or offscreen literary style exists here. Earlier validated 13-scene save/offscreen experiments remain useful but are not a substitute for this external benchmark's source fidelity.

**Decisive obstacle:** the **semantic extraction and actual 3D construction of the author-described scene**. Changing physics engines or running more save/load tests will not fix missing rooms, unrecognized objects, missing referents or incorrect physical geometry. A near-term architecture should retain native Rapier authority, exact source provenance, explicit unknown source interpretation and observer scopes, but replace primitive lexical category extraction and single-room placeholder layout with a validated **multi-room scene/instance plan** and a sourced 3D asset catalog with dimensions/colliders. Only then independently evaluate full per-constraint source fidelity, native support/placement, physical events, observer semantic updates and offscreen continuity. Do not deploy arbitrary literary materialization as source truth yet.

## Reproduction and status

New owned research scripts and safe aggregate JSON in `browser_physics_prototype/research/2026-10-25`:
- `prse_lego_source_only_frozen_proposals.py`: only instruction input; source-only lexical + pretrained parser.
- `prse_lego_human_matched_native.mjs`: actual matched native GameCore/Rapier worlds and contacts.
- `prse_lego_independent_reference_gold_audit.py` and `prse_lego_independent_reference_gold_audit_v2.py`: independent post-frozen human official reference audit, including corrected strict directed 3D support.
- `prse_lego_independent_source_native_readonly_evidence_verify.py`: read-only source/body/reference/hashes and strict positive/negative checks.
- Versioned safe aggregates with complete counts, hashes and explicit unavailable true-negative/asset information.

All full source instructions and annotated/reference scene metadata, per-case native 3D body positions, current original source and auditor details are private under `/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent` (owner mode 0700; raw JSON mode 0600). Do not rerun experimental scripts into existing outputs: they exclusively create raw files for preservation. Use the **read-only verifier** to check prior evidence. The private case-level reference snapshots and full third-party text are not committed. The separate source dataset can be retrieved from its official Apache-2.0 repository using the documented public URLs.

**Research status: PARTIAL**. This independent human-authored+gold native-physics experiment is finished. Robust category/instance and metric 3D asset parsing, multiroom topology, a separate permitted feasibility-matched placebo, genuine observed physical-to-literary quality and offscreen causal generalization remain unproved.
