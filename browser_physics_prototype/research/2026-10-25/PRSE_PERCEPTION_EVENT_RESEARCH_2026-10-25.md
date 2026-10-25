# PRSE physical perception, witnessed events, and truthful re-entry
Research continuation, 25 October 2026 — isolated Games research branch

## The original priority

The preserved owner recordings of August 13 and October 9, especially the October 9 18:04 recording, require a persistent literary and semantic world that materializes as **one authoritative three-dimensional physical world**, changes through genuine game events, and returns to faithful descriptions after interaction, absence, save and re-entry. A renderer is only an adapter; speculative model prose is never a substitute for verified physical truth.

This continuation rechecked current Infra AGENTS.md, the original owner passages, current games/semantic_physics_text_loop.md, the previous completed research, Git worktree and remote state, and Nitro production resource usage. The prior research commit 4035f67 was already pushed, so no old external effect was replayed. Canonical Games main was heavily dirty with concurrent changes, and live PRSE, commercial rendering, Nitro inference and other agents were untouched. New work used the existing isolated branch and low-priority CPU headless GameCore/Rapier.

The prior independently annotated source-scene test remains a **major negative result**: only 30/478 human-scene and 22/743 assisted-scene object relation claims were physically satisfied using an optimistic, direction-insensitive comparison. This continuation focuses on a separate open part: can the player's **perceived textual knowledge** reflect real three-dimensional occlusion and physical event timing without revealing hidden causes or losing rapid events?

## Independent scientific context

The published SceneEval benchmark (Tam et al., WACV 2026, https://openaccess.thecvf.com/content/WACV2026/html/Tam_SceneEval_Evaluating_Semantic_Coherence_in_Text-Conditioned_3D_Indoor_Scene_Synthesis_WACV_2026_paper.html) distinguishes explicit scene counts/relations from physically plausible output. We reused its original SceneEval-500 descriptions, not its annotations as simulated perception truth.

Holodeck (Yang et al., CVPR 2024, https://openaccess.thecvf.com/content/CVPR2024/html/Yang_Holodeck_Language_Guided_Generation_of_3D_Embodied_AI_Environments_CVPR_2024_paper.html) generates language-driven spatial proposals and optimizes object layout, but it is not a validation of our game. Descrip3D (Xue et al., WACV 2026, https://openaccess.thecvf.com/content/WACV2026/html/Xue_Descrip3D_Enhancing_Large_Language_Model-based_3D_Scene_Understanding_with_Object-Level_WACV_2026_paper.html) provides evidence that explicit object-relation descriptions matter for 3D scene-language understanding. Those are external studies, not model experiments performed in this task.

The new empirical tests below run actual GameCore/Rapier collider rays and use actual entity/event IDs. The provisional furniture layouts, five investigator-chosen camera positions and seven sample points per target are **not human vision measurements**, and they do not capture acoustic perception, lighting, glass transparency or actual graphical rendering.

## Physics-correct perception versus distance alone

The existing research PRSELoop.visibleIds used only distance. A stone partition in the *real Rapier world* demonstrably blocked the first-hit ray from an eye to a pot while that method still said the pot was visible. On the unobstructed side, the actual physics ray struck the pot.

We added a separate research-only PRSEPhysicalObserver adapter, using the same GameCore rigid bodies, ray casts and persistent IDs. It checks distance, optional facing direction, and seven sampled target points. A structural wall may block light but is not automatically described as a literary object. Destroyed semantic identities are never treated as existing physical colliders; physically visible ash may retain source lineage.

The frozen earlier text interpreter and geometry proposals were used unchanged on **200 external descriptions**: 100 human-authored and 100 systematically sampled partly machine-authored SceneEval rows. Of these, 196 produced acceptable physical scenes. Five fixed interior eye positions per scene were considered, and seven positions physically embedded inside objects were excluded. Of **2,917 distance-eligible object observations**, **142 were occluded according to authoritative collider first-hit checks**, about 4.87 percent. Seventy-five occurred in the human-authored sample and sixty-seven in the partly assisted sample. Furniture accounted for 139 blocked cases, wall geometry for three; approximately four thousand Rapier rays were cast. All of these are geometry-consistency observations, **not a human ground-truth optical visibility score**. An object behind translucent glass could be wrongly hidden, and the provisional layout itself may be semantically wrong.

## Event time must be the actual cause instant

A second original observer defect appeared when a fast object changed its line of sight between an event being emitted and the next GameCore physics step. A separate one-second UI polling test also showed that the old observer could lose an event it should have delivered.

In the fixed 200-scene source group, 64 contained dynamic entities. Sixty-three had at least one unobstructed candidate eye, and seventeen also had a contrasting eye occluded by physical geometry. A fixed physical GameCore impulse was applied to each eligible object. In the **original post-step event capture** batch, only 62/63 originally visible source impulses were delivered, and one of seventeen occluded observers wrongly received a hidden cause. No repeat after reloading was observed.

The original complete raw result, prse_observer_event_batch_200_raw_v1.json, was retained unchanged. Two particular external cases exposed the exact problem:

- Row 27: the cup was visible when the physical impulse was applied but moved behind a television one step later, so late capture missed the event.
- Row 29: the book was behind a bookshelf when the impulse was applied but moved into view one step later, so late capture retroactively revealed the cause.

These are not synthetic manually faked success claims: the observer status before and after that physics step was obtained using actual Rapier first-hit rays on physical bodies from the source-derived scenes.

## Synchronous event witness record, durable across save/re-entry

The isolated research PRSELoop now offers an optional, synchronous read-only event-emission subscription. The observer attaches to it so that perception is tested at the **moment the authoritative event is emitted**, rather than sampling later geometry. A failed observer callback is recorded instead of mutating game truth. The observer stores bounded queues of **authoritative event sequence IDs**, not invented natural-language causes, and each delivery journal survives serialization with independently validated entity/event references.

After correcting this one timing boundary, the **same 200 scene inputs and fixed impulses** were evaluated again. In the same 63 eligible moving-object cases, **63/63 visible impulses** were captured and delivered despite approximately one second of delayed text polling, while **0/17 contrasting occluded observers** received those hidden impulses. Already delivered events were not repeated after saving and reloading. There were no runtime failures. Rows 27 and 29 were retested directly and now have the correct observer permissions. This is a controlled research-sidecar mechanism, **not a production deployment or an independently sampled human playtest**.

Without a synchronous callback, the strict text-observer method deliberately does not infer event witnessing merely from a later viewpoint. A slow UI update can still describe the object's **current visible state**, but may not attribute to the player a cause the player never witnessed. Genuine rapid physical events are retained when witnessed at event time, then delivered later from the authoritative event history.

## Offscreen rematerialization and private knowledge

The original owner's offscreen candle/fire continuity question was exercised independently. A source-linked paper note was converted, by an explicitly authored semantic combustion rule, into scorched then ash state while unloaded. The historical note ID remained a tombstone; a **separate real fixed ash collider** with explicit source provenance rematerialized when the observer returned. That observer received the current physical fact that ash remained, but **zero retrospective narration of an ignition not observed**, and no duplicate after polling or save/reload. This is a coarse fixed physical ash patch, **not simulated chemistry**, and it has not been merged with the separate native shelter-fire implementation currently being developed on dirty main.

The observer state and world snapshots remain separate research artifacts; production must save them atomically and reattach actual live observer pose subscriptions after restore. The existing legacy PRSELoop.narrate remains distance-only; the new physical observer is the tested research alternative, not a replaced live renderer.

## Artifacts and precise evidence levels

The owning Games project research/2026-10-25 folder contains:
- prse_physical_observer.mjs: physical first-hit observer, event-emission capture, per-observer witness queue and persistent journal.
- prse_physical_occlusion_benchmark.mjs and prse_occlusion_200_aggregate_v1.json: source-proposal physical visibility comparison on 200 descriptions.
- prse_observer_event_corpus_study.mjs, and distinct versioned safe v1 and v2 aggregate JSON: post-step versus synchronous emission capture on the same selected physical object, impulse and viewpoints.
- prse_event_emission_timing_fix_study.mjs: explicit corrections of earlier failed external IDs 27 and 29.
- prse_observer_delayed_witness_study.mjs, prse_observer_causal_reentry_study.mjs and prse_observer_offscreen_remnant_study.mjs: controlled real physics, observer-specific event/fact delivery and save/reentry.
- prse_physical_perception_evidence_verify.py and a safe aggregate manifest: verifies source ZIP digest, private complete research output hashes, exact source IDs, previous versus updated counts, physical reentry and no invented human observations.

Full third-party source-derived JSON and previous failed test outputs are retained in owner-private Nitro research storage under /data/var/games/prse_semantic_research/runs/2026-10-25-physical-visibility. File permissions are restricted and SHA-256 values accompany the committed aggregate. The authored non-corpus research fixtures and their results are in the project; the complete SceneEval prompts are not republished. Earlier accepted original result files were never overwritten.

## What remains honestly unresolved

- **General language understanding is still inadequate.** Correct physical visibility cannot repair unknown nouns, misunderstood quantifiers, wrong support relations, implicit context or absent/counterfactual conditions. Earlier gold relation accuracy remains very low.
- The ray approximation does not model actual camera framing, translucent materials, lighting, field of view unless supplied, auditory/thermal clues, human perceptual thresholds or texture-level occlusion. An observer can be visually blocked and still hear an impact, which is not supported here.
- Event subscription is research-only and **not wired to the live PRSE service, client input/camera, terminal text reader, sprite UI or production GameCore**. The intended hook must be used reliably for every relevant physics/semantic event.
- Captured event sequences are saved with structural integrity validation, not cryptographic proof against intentionally forged save files. A full durable game should specify source trust boundaries.
- Capturing currently scans the event list; sustained high-volume simulation should use a monotonic event pointer or bounded event queue rather than quadratic growth. Large-scale performance and latencies remain unknown; the approximately 17-second 200-scene visibility run occurred under heavy shared Nitro CPU load and includes world construction.
- Full offscreen physics for moving actors and objects, source-grounded literary LLM rewriting, physically emergent fracture/combustion and shared multiple-actor/observer causal timelines remain incomplete. No matched small-LLM versus deterministic narration evaluation was possible without confirmed free inference capacity.

**Scientific conclusion:** For PRSE's bidirectional story↔physics design, authoritative world truth and observer-specific knowledge must be separate. Physically witnessed events are attributable to that observer only when tested **at event occurrence**; unseen history stays in the world ledger and becomes discoverable through physically present aftermath, not ungrounded retrospective narration. This distinction was implemented and tested in the **existing GameCore research sidecar** across varied source-derived scenes, while the complete general system remains PARTIAL.
