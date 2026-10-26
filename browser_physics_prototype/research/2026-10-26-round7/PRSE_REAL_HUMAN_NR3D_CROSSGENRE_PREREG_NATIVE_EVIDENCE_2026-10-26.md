# PRSE — independently human-authored Nr3D cross-genre holdout with preregistration, real Rapier arms and independent 3D phrase/instance labels
26 October 2026. Seventh owner-authorized follow-up in the SAME NEW research chat, isolated Nitro Games worktree.

## Exact original owner goal and bounded conclusion

The user's original August 13 and October 9 game recordings require a *persistent literary semantic world* converted into an authoritative, correctly instantiated THREE-DIMENSIONAL physical world: exact object types, identities, counts, positions, metric asset sizes, real support, contacts, forces, causes, events, offscreen evolution and source-grounded observer-specific prose that persists across save/reentry and rematerialization. The engine has to be modality-independent; habits/macros are strictly secondary.

**Round-seven preregistered cross-genre transfer FAILED its accuracy acceptance rule**, although the pretrained general-language noun method significantly improved over the previously frozen PRSE lexical baseline. A separate newly executed **actual GameCore/Rapier** same-body feasibility study also succeeded mechanically but **did not prove source-world geometry, individual target-ID, or vertical-support gold correctness**. The general original literary-to-true-3D-to-literary goal is therefore **PARTIAL / UNVERIFIED**. Keep unrestricted literary materialization disabled.

## Distinct previously untouched corpus and source/label separation

This round deliberately avoids another sample from SceneEval or LEGO-Bench. Downloaded the **public ScanEnts3D expansion of Nr3D**, human freeform 3D referential utterances independently annotated with target object type, target 3D ScanNet instance ID and phrase-to-3D object ID correspondences. Sources: [ReferIt3D (Achlioptas et al., ECCV 2020)](https://referit3d.github.io/) and [ScanEnts3D public dataset and annotation specification](https://scanents3d.github.io/dataset.html). This is **a cross-genre transfer to short 3D object referring expressions**, NOT full literary room descriptions. It is genuinely different from prior source corpora. The present public ScanEnts3D/Nr3D CSV contains **37,842 human expressions over 641 distinct ScanNet scene IDs**, with general spatial-language flags. The underlying ScanNet point clouds, 3D object meshes, measured bounding boxes, ground-truth gravity/support/contact geometry and independent after-event observer prose are **not available** on Nitro. Do not claim their availability or reverse engineer them from text.

Immutable source CSV SHA-256 is `f6b437e2bfc15c69c2b497c755e9a5b42eec110dccc25deb29594e3734a31f5b`. Data stays owner-private on Nitro under mode 0700 directory and individual mode 0600 files. All published source code, private frozen source, independent annotations and native evidence are linked by SHA hashes; copyrighted text and individual ScanNet IDs are NOT committed.

**Pre-registration was saved and copied into a separate private original file, then SHA-256 verified, BEFORE computing any source-only predictions or scoring the independent 3D human annotations.** It specified the deterministic scene split, pair comparison, strict object kind metric, abstentions, effect threshold, interval and negative controls. Original preregistration SHA-256 is `688fc6d8199b30617a481460386de87a329f8ceeea1f255d2774b7416d06076f`.

Sampling: from each original ScanNet scan ID, choose one expression by minimum SHA256(scan ID, official source index, utterance); choose **480 DISTINCT scan IDs** by independent SHA256 of scan ID. This is a scene-cluster-disjoint source holdout and prevents repeated descriptions of a single scene from inflating sample size. The source-only selector accesses strictly `index`, `scan_id`, `utterance`; it does not use target `instance_type`, `target_id`, `correct_guess`, gold `entities`, source `stimulus_id` or other label fields. The selected source texts and hashes were exclusively frozen first, followed by frozen predictions; **only then** did the independent scorer open original Nr3D phrase-to-3D instance annotations.

## Frozen matched source language comparison and explicit acceptance

Methods were not trained or changed based on Nr3D gold:

- **Previously frozen older PRSE lexicon:** first non-negated concrete source noun mention and kind from the existing SceneEval-trained lexical mapping.
- **General pretrained grammar:** spaCy English `en_core_web_sm` 3.8, taking first concrete nominal head and, where available, retaining the exact older lexicon source-span taxonomy instead of inventing new source categories. Explicitly abstains on absent/structural/nonphysical root. Neither predicts a specific individual ScanNet target ID or knows source room/metric geometry.

**Preregistered pass rule**: new all-input exact 3D target class correct rate at least **75%**, absolute gain over baseline at least **10 percentage points**, and scene-paired 95% confidence interval lower bound strictly positive. Abstention counts incorrect on the primary endpoint. Without all three, fail; secondary high-confidence precision is diagnostic. Unknown synonyms are not tuned to improve the final score. Confusion sources include `trashcan` vs ground-truth `trash_can`, `couch` vs `sofa`, and `toilet paper` vs `paper`, but relabeling after inspection would violate the preregistered strict score.

### Primary result: 480 independently human annotated 3D scenes

| Metric | Frozen existing lexical parser | General pretrained nominal parser |
|---|---:|---:|
| Source-only proposed target object types | 389/480 | 479/480 |
| Strict correct target object types, all inputs | **231/480 = 48.125%** | **309/480 = 64.375%** |
| 95% Wilson CI, all-input correctness | 43.69–52.59% | 59.99–68.53% |
| Conditional strict correctness among proposed | 59.38% | **64.51%** |
| Unique correct ScanNet object instance IDs returned | **0** | **0** |

Paired improvement **+78/480 = +16.25 percentage points**, 95% fixed-seed **scene-level paired bootstrap +11.67 to +20.83 points** (10,000 bootstrap resamples, sampled at scene not utterance level). Discordant pairs: **104** new-parser wins versus **26** losses; paired exact McNemar/binomial two-sided p approximately **3.03 × 10⁻¹²**. Statistically robust improvement on this corpus, **but the absolute target 75% FAILS** (64.375%). Reference to “480 gold-scored scenes” is valid; 446 of the reference experiments were also correctly guessed by the original human listener. Restricting secondarily to those 446 gives frozen baseline 213 and pretrained 291 correct, but the preregistered all-480 rate remains primary. Independent entity-span grounding of target 3D object ID is present in **478 of 480** samples. A correct kind is NOT an exact object ID. Because our method generates no unique target-instance ID, zero independent instance-grounding successes can be claimed.

Primary noun proposal took **6.912 s CPU-only wall** across 480 human source phrases, including model load and general spaCy parser; mean ~14.4 ms per phrase over that one batch, not production per-request latency. Post-frozen human label scoring and confidence analysis took 23.679 s including separate full CSV processing and 10,000 bootstrap resamples; this is research audit cost, **not runtime model inference**.

## Negative controls and uncertainty

Among the 480 original human utterances, **71 distinct cases** have a natural source phrase such as **“on the right/left/side/end”** or **“not on”** rather than clear vertical physical support. Under the source-frozen conservative dependency grammar, zero candidate ON proposals overlapped those exact original idioms. This is a pre-registered **0/71 narrow natural semantic-negative rate**, Wilson 95% interval **0–5.13%**; it does NOT prove below 3% true error with 95% confidence, and is not exhaustive independent human contact-negative gold. The parser proposed **15** nominal ON top relations total in the 480 source examples. No random parent reassignment control was used.

## NEW real authoritative GameCore/Rapier matched experiment on the external human source

Frozen original corpus source-only relationships, not its gold, determined an **independent 31-scene feasibility cohort**: all **15** candidate ON nominal phrases and **16** naturally nonvertical source-negative phrases with two older-lexicon named kinds. Neither class, parent identity nor physical target geometry was picked by independent gold. Only source-text anchored types entered the physical model.

Both arms per utterance use **EXACTLY two native bodies** with the same source ID, category, mass, generic 3D box collider shape and metric dimensions. Parent is a fixed wide provisional box; child is dynamic. **Control:** separated on the floor with no interobject contact. **Source arm:** child moved *only* onto the source-mentioned parent for explicit source ON; natural non-top negative phrases cause **zero** body moves. They use the SAME GameCore/Rapier solver, exactly **38 native steps** per arm, real collider manifolds, and native whole-world state snapshots/restores.

Measured **62 actual PRSELoop/GameCore/Rapier worlds**:
- **31/31 exact same-body category/dimension comparisons**, no execution failures;
- all **15 source-explicit candidate placements** produced real nonwall Rapier contact manifolds after 38 ticks; no unrelated parent was randomly tried;
- all **16 natural non-top negative-control** scenes retained EXACT identical native interobject contact sets (zero before and after), avoiding unsupported contacts;
- **62/62** true whole-world native GameCore/Rapier snapshots restored the same source text/body IDs and contact pairs;
- **6.584 s** CPU-only wall for all paired worlds, median ~137.6 ms per paired 38-tick scene and 95th ~616.7 ms. No GPU/model call or production service disturbance.

**Critical limitation:** the method places a **provisional square box onto another provisional box by design**. Thus 15/15 real contact success establishes only that the physical placement/snapshot mechanism can create and preserve these source-nominated contacts **given assumed geometry**, not that the speaker intended that exact object's 3D model and support. For example, source-accepted “window located on a staircase” does not validate a physically meaningful full-size window resting on a step. The original ScanNet meshes, true bounding boxes, collision surfaces and room topology are not present. This feasibility exercise **must not** be represented as source-to-ground-truth-3D support precision or general physical plausibility. It is not a random-feasible-parent placebo and does not remedy the earlier denied control.

### Postfrozen separate human 3D phrase-to-object IDs score for the 15 real contacts

Only after real native worlds and contacts were immutable did the source/gold auditor open Nr3D `instance_type`, `target_id` and ScanEnts3D annotated phrase-to-3D ID lists.

- **11/15** proposal **child kind** matches the independently annotated actual human target object class, Wilson 95% CI approximately 48.05–89.10%.
- **4/15** source-nominated **parent kind** appears as a separately annotated *other* original ScanNet object instance in that expression.
- Exactly **4/15** have *both* kinds independently grounded to annotated distinct 3D referents, Wilson 95% CI roughly 10.9–52.0%. None has a source-derived unique target instance ID prediction.
- The other eleven cannot be honestly called independent source-grounded support successes. Some anchors are omitted from entity annotations and some aliases differ; unknowns must not be converted automatically into negatives. No real ScanNet mesh/collider support labels were available. Actual physical support precision remains **UNKNOWN**, distinct from the nominal 15/15 fabricated generic geometry contact rate.

This separately demonstrates the principal failure: more detected nouns and engine-created contacts do not equal actual object references, correctly sized geometries and faithful literary semantics.

## Product acceptance / prior known limits

A prior real browser acceptance on Nitro's canonical viewer succeeded on the existing scripted forest game and a separate real candle-paper study worker. However, it could not import an original human-written conference room projector/table scene into the player's actual source-specific 3D world. In the full independent LEGO 130 scene + 1,250 constraint server test, neither source version created any intended external literary world; overlength requests were rejected and the rest returned generic help. That remains a separate product failure and is not fixed by Nr3D object-kind improvement.

Earlier SceneEval gains in source “ON” came from assisted descriptions, not original fully human ones. LEGO-Bench offered independent full-scene source and annotations, but no complete source-grounded metric mesh/collider with trustworthy room-specific stable instance IDs. The previous denied feasible-random-support placebo remains **denied and unattempted** here; the earlier denied broad observer-cycle experiment also remains unperformed. No player macro/habit work was conducted.

## Reproducible source, status and required next milestone

Owner's isolated Nitro worktree `research/game-skills-hidden-20261024`, round-seven owned research subfolder `browser_physics_prototype/research/2026-10-26-round7/`:

- Frozen Markdown preregistration preserved untouched both in Git and private evidence; explicit locked source split, accuracy threshold and uncertainty.
- `prse_round7_nr3d_source_only_480.py`: NO GOLD source-only selection and lexical / pretrained nominal proposals, frozen original input hashes and candidates.
- `prse_round7_nr3d_independent_postfreeze_audit.py`: independent annotations opened only AFTER source-only predictions were frozen; correct labels, paired confidence, coverage and acceptance adjudication.
- `prse_round7_nr3d_freeze_physical_probe_source.py`: frozen 31 physical source/negative-controls directly from already frozen text proposals, never from target-ID gold.
- `prse_round7_nr3d_real_rapier_goldblind_31.mjs`: exact same body/shape/mass native GameCore 3D comparison, actual Rapier collision manifolds, 38 steps, source/native whole-world save/restore.
- `prse_round7_native_role_postfrozen_human_gold.py`: independent annotated target/anchor 3D object IDs for 15 source-nominated real contacts, postfrozen.
- `prse_round7_nr3d_readonly_entire_evidence_verify.py`: securely rerunnable verification of full original SHA hashes, prereg, 480 independent gold-scored and 31 matched actual native physical sources and same-body controls.
- Safe aggregate JSON files for the main 480 independent source tests, 31 true native worlds and 15 human object-class/anchor audits; **original 12.6 MB CSV, descriptions, per-case gold reference IDs, native body states and all labels remain protected in private mode 0700/0600 under the isolated Nitro evidence root**. Do not commit that private data.

Acceptance is **FAILED** on the predeclared 75% target object-type criterion; no full-PRSE literary world acceptance is claimed. **Next decisive empirical work** must connect a source-only parser to *validated* room-qualified target instance IDs and measured ScanNet or owner-controlled approved 3D mesh/collider geometry, with independent 3D physical contact/pose and exhaustive negative labels and later human-evaluated observer-limited prose through actual native physics, offscreen evolution, save/reentry. The generic Rapier feasibility result does not close this.

No production GPU/model services restarted, no existing checkout modified, no denied effect retried, no new recurring task created.

Status: PARTIAL.
