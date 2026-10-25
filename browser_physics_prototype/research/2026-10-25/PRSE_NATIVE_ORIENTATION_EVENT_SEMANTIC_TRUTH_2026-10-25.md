# PRSE — native 3D orientation, truthful physical events and current semantic state

> **Subsequent independently verified source/current story delivery:** [real source-event and current-fact channels on forty other scenes plus the eleven original false-tip cases](PRSE_DECISIVE_EVENT_CURRENT_SOURCE_EVIDENCE_2026-10-25.md). The first observer test falsely failed ten cases because it conflated truthful historic tip events with present object state. Both original invalid test evidence and corrected controls are preserved; typed historic and current factual narration reconstructs the old output losslessly while keeping the original negative source-meaning evidence.


25 October 2026. Isolated Games research, continuing the original PRSE literary ↔ physical ↔ literary world investigation.

## Owner's original priority and verified starting context

The August 13 original owner PRSE recordings, at 17:37 and 18:11, and October 9 recordings at 12:16 and 18:04 define a persistent world stored primarily as ordinary descriptive/literary text. Near the player, source-linked entities must become ONE real, authoritative three-dimensional physical GameCore world, with plausible scale, relationships, collisions and causal event histories. Physical changes and offscreen semantic processes must flow back into coherent current world descriptions, with stable source/physical identity on later reentry. Secondary player habit/macro learning and scripted fence demonstrations do NOT substitute for this central bidirectional problem.

This continuation read the full current Nitro Infra AGENTS.md first, mandatory doc/audio_style.md, games/world_and_generation.md, games/semantic_physics_text_loop.md and relevant original source excerpts. The isolated Games research branch was initially clean and the previous owner-only research commit was already present on its real remote. Canonical Games main had 83 unrelated other agents' dirty files. Trading, commercial 3D, browsers and Nitro shared inference/GPU remained busy, so all source-derived experiments used nice-19 CPU in the existing isolated worktree; no production GameCore, service, user Calendar event, original recording or other agent work was changed.

Prior independent external SceneEval and Rapier work already proved necessary bounded mechanics: native three-dimensional physics, coherent IDs, some real contacting objects, real impulse and typed event histories, native whole-world contact-preserving snapshot, observer-specific ray-tested fact delivery and author-inspired offscreen semantic destruction and rematerialization. The principal overall negative remains: the original scene compiler satisfies less than half of independent source count annotations, and generic boxes or destructive grammar pruning do not reliably preserve the original author's object relations. The new experiment does NOT change those earlier corpus conclusions.

## NEW correctness question: when is "tipped over" physically true?

An inspection of the research PRSELoop.capture() revealed the previous event classifier compared total quaternion rotation to a tipping threshold. Total rotation includes YAW about the gravity axis. A book, cup, lamp or vase can rotate in place, or tilt moderately while rotating around vertical, without exceeding the required physical up-axis tipping threshold. The old engine nevertheless emitted a TIPPED event and set a permanent current-state tipped flag once its total quaternion angle exceeded 0.7 radians. A subsequently upright rigid body could therefore remain described in present tense as tipped over. That is a concrete physical → semantic truth error, not a theoretical LLM concern.

The authoritative standard is the actual Rapier rigid body's world rotation, contact state and local up direction. For a unit quaternion q, up-axis dot world-up is 1 minus twice the sum of squared q.x and q.z. The physical tilt is the arccosine of the clamped value; YAW alone does not change this angle. The official Rapier advanced collision-detection guide, https://rapier.rs/docs/user_guides/javascript/advanced_collision_detection_js/, documents native collider contacts, manifold normals and solver contact evidence. This study uses existing real Rapier transforms for event verification. It does NOT claim calibrated physical tipping for arbitrary articulated meshes, multi-part furniture or deforming objects.

## Original unmodified support-relation physical audit

Before editing PRSELoop, executed an independent source-neutral support/contact audit on EXACTLY the same previously frozen first 100 human SceneEval descriptions plus systematic assisted 100 sample. There were 197 previously accepted source scenes, four fixed native impulse directions per scene, 788 source scene/action conditions, and 256 actual movable-body interventions across 64 separate source scenes. All source metadata, native transforms and contacts came from GameCore/Rapier, with no author gold annotations used to generate actions or adjust the world.

Among 196 old positive support claims measured under these repeated conditions, NONE was directly contradicted by the stricter native upright/contact check. After complete ticks, object metadata position matched native body position in the tested source relations. Twenty-seven possible relations involved physically tilted forms for which simplistic axis-aligned support geometry cannot prove physical truth. Those remain explicit UNKNOWN cases, not a spurious model-quality success. This independent negative matters: it prevents us from falsely blaming generic stale positions for every problem.

Original owner-private complete raw result and safe aggregate: prse_native_orientation_support_audit_197x4_raw_v1.json and corresponding public numerical summary.

## Actual source-derived event-time failure

The more targeted actual native orientation audit used ALL 64 previously source-derived scenes with moving physical bodies, under FOUR predeclared real GameCore impulses each, 256 native 3D action conditions. Actual Rapier physics ran 160 steps after each impulse. At the exact event time, the initial engine's newly emitted typed TIPPED events were compared with native body local-up tilt and total quaternion rotation. The end-of-scene persistent semantic tipped flag was checked against actual final native posture. No independent author gold label entered this experiment; the physical event itself is evaluated, not a narrative parser's source relationship.

The original frozen engine emitted 173 TIPPED events. EIGHTY-TWO of them failed the engine's original physical tipping threshold when assessed by the body up direction. Two were almost fully upright, with up tilt under 0.12 radians at event emission. The event-time mismatch affected multiple source-derived object categories and forty-one source descriptions. ELEVEN scenes contained a persistent present-tense TIPPED flag while the actual native rigid body was close to upright at the final physical frame. Those are independently measured false physical event/current-world interpretations.

All v1 per-source cases, actual native rotation measurements, original emitted events and failure metadata were saved owner-private BEFORE the code correction and remain immutable.

## Actual isolated research-core fix and source/observer contract

Only the owned isolated PRSE research code was changed. The native GameCore physics integrator, forces, contacts, spatial assets and source scene generator were NOT changed. PRSELoop.capture() now calculates actual up-axis tilt from the normalized Rapier quaternion and emits a TIPPED event for a non-spherical body ONLY after that measured physical tilt exceeds the existing 0.7-radian threshold. Its prior separate ROTATED event for physically rotating spheres stays separate.

When a previously tipped non-spherical body later returns below a 0.12-radian near-upright threshold, PRSELoop clears the CURRENT semantic tipped state but retains the historical TIPPED event and emits a distinct physically grounded RIGHTED event. The observer-specific event text can now say an object became upright again only when the event was genuinely captured by the existing ray-tested, event-time perception adapter. The old source literary text and original physical identity remain untouched; an absent observer cannot retrospectively acquire a hidden cause.

A real object may still be partially leaning between 0.12 and 0.7 radians after a previous tip. That is a conservative state/hysteresis limitation, not a guarantee of human-equivalent appearance labels.

## Exact physically matched correction and new empirical result

Reexecuted the SAME 256 source scene/impulse/160-step native physical conditions as an independent, exclusive v2 result. Every actual final Rapier up-axis orientation and total rotation measurement matched the original v1 run EXACTLY, because only semantic classification was modified.

The corrected engine emitted 178 true TIPPED events and ZERO events below the authoritative 0.7-radian up-axis threshold. It retained ZERO false present tipped states on near-upright native bodies, correcting all ELEVEN original persistent errors. The corrected event count is greater than the original because the engine can now tip, genuinely right itself and later tip again, whereas the old one-time sticky flag prevented repeated historic tipping reports.

An additional one-source outcome finished partially leaning at about 0.49 radians and remains conservatively represented as not fully righted, as specified by the reset threshold. The code does not invent a "fully upright" event for that body.

## Eleven previously failing source-derived observer/native-save regressions

Independently selected all ELEVEN prior false-current source scenarios from the original frozen evidence and replayed their original actual native GameCore impulses. This is a targeted regression against known failures, NOT eleven new blinded independent literary source worlds.

All eleven corrected native worlds reported physically near-upright bodies with current tipped false. The real event-time stream in those cases contained THIRTEEN physically verified TIPPED and THIRTEEN physically verified RIGHTED events, with ZERO physically misclassified event. The same eleven current semantic documents contained no false present-tense tipped statement for the target entity. For the five returning observer positions where the target was actually ray-visible, the existing observer-specific current text did not falsely call it tipped. Complete native Rapier world, historical source text, object IDs, observer state and current semantic document all saved/restored consistently in eleven of eleven cases.

No claim is made that a physically absent witness watched every actual event. The test checks real returned physical facts, not impossible omniscience or source author intent.

## Larger full scene/source regressions after the code change

Reran the existing broader source → actual three-dimensional GameCore → typed current world text → native source/observer save and next physics tick test on BOTH frozen source interpreters under new exclusive v3 evidence names.

Deterministic original source interpreter: 197 of 200 external source scenes accepted and saved without new runtime failure, new unsupported source prose, repeated unchanged text or source/physics divergence. Parsed relation truth totals remained 100 TRUE, 34 FALSE and 273 UNKNOWN. Fifty-seven source scenes produced meaningful semantic document changes under the fixed real impulse.

Pretrained grammar-union interpreter: 195 of 200 source scenes accepted, identical native whole-world/source/observer saving and later physical source truth, no new unsupported source narration or duplicate unchanged revision. Parsed relation totals remained 133 TRUE, 41 FALSE and 407 UNKNOWN. Fifty-seven meaningful changed-world scenarios again.

Both new summaries exactly match the relevant prior full-scene source/fact metrics. Thus fixing false tipping narration does not make the existing literary-source parser suddenly more capable or degrade the already verified native 3D materialization and original source factual continuity.

## Scientific limits, provenance and future architecture

This work is meaningful because it found and corrected a REAL independent native-to-semantic defect after apparently successful source/physics/save tests. It also reports the non-finding that old positive support statements did not contradict the stricter native upright/real-contact evidence within this particular externally sourced workload. This is not scientific evidence that all support and future events are correct: compound colliders, rotated surface normals, frictional tipping, physical damage and exact author identity remain incompletely modeled.

The primary owner objective still needs unrestricted original literary interpretation, correct persistent referents/quantifiers/negation, approved scale/shape/affordance-rich 3D assets, source-conditioned support/containment placement, unseen evolving NPC society and coherent independent author-quality literary rewriting. A verified native force/contact/world event may ground a factual change, but it does NOT independently prove that the initial source parser understood the original story. No generative LLM or human literary reader was tested in this continuation while production GPU/inference loads were active.

The complete original source-derived physical event traces, the first frozen false tipping results, correction v2 and observer current-world retests are stored in private Nitro research at /data/var/games/prse_semantic_research/runs/2026-10-25-native-orientation-audit. Owner-private directory mode 700 and raw JSON mode 600, exact raw bytes verified by source SHA-256; no full third-party source paragraphs or actual GameCore native world binary snapshots were committed.

Reproduction code and public-safe numerical results belong to the owned browser_physics_prototype/research/2026-10-25 folder: prse_native_orientation_support_audit.mjs; prse_native_tipped_event_audit.mjs; prse_native_tipped_current_observer_regression.mjs; prse_native_tipping_semantic_evidence_verify.py; source-safe orientation, tipped-event, native observer aggregates and current semantic document v3 benchmark aggregates; plus this dated report. The actual physics event correction is scoped to the existing owned research prse_semantic_roundtrip.mjs and the research physical observer adapter's RIGHTED event vocabulary; it does not change live PRSE.

**Bottom line:** real false physical tipping events and stale present-tense object orientation states are now corrected and independently matched against the original authoritative Rapier trajectories across hundreds of source-derived conditions. The full unrestricted persistent literary↔authoritative 3D↔coherent current literary-world objective remains PARTIAL.
