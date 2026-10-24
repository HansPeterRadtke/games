# Game skill and hidden-mechanic research: continuation, 2026-10-24

> **Owner correction, 2026-10-24:** Prior results using scripted teachers and fixed x-coordinate or fence objectives are **engineering tests, not evidence that a real human-taught physical skill was learned**. See [corrected source- and human-data-based research](CORRECTED_HUMAN_SKILL_RESEARCH_2026-10-24.md). The original results and failures remain preserved unchanged.

This is an independent continuation of [the initial bounded report](REPORT.md). All experiments live in the existing Games repo, on the owned isolated research worktree. The dirty canonical main tree, live PRSE service, GPU rendering and production workloads were untouched. Do not re-label or retune the previous **7/8** original kNN versus **0/8** fixed macro study: it was already used and remains preserved in [results.json](results.json).

## Primary sources and evidence levels

- Live original file: `/data/infra/AGENTS.md`, read at the start of this continuation.
- Requirements: `/data/infra/docs/guidlines/games/learned_habits_and_automation.md`, `hidden_systems_and_player_research.md`, `core_and_modalities.md`, `semantic_physics_text_loop.md`, `playability_realism_and_saving.md`, `world_and_generation.md`, `physical_character_model.md`, `early_game_engagement_and_onboarding.md`, `standard_game_foundation.md`; the general `testing.md`, `programming/README.md`, `source_traceability.md`, `security_privacy.md`, `agents/research_and_evidence.md` and audio-style instructions. See `semantic_coverage.json` for **actual semantic reading** plus per-file headings and the still-unread parts, not just hashes.
- Originals fully read in this continuation: August 13 17:37 and 18:11 PRSE, September 22 16:21 and 19:29 hidden systems, and October 9 12:16 and 18:04 authoritative PRSE physics core, and October 14 18:33 learned skills. Other sixteen original Games transcripts were **term scanned, not semantically read**, and Infra as a whole was not fully semantically read. Preserve this limitation. The August 13 17:37 original includes a very long repeated candle transcript loop; its repetition is not independent testimony.
- Implementation: `browser_physics_prototype/physics-core.js`, `character-model.js`, `hidden-mechanism.js`, authoritative `prse_runtime/README.md`; real Rapier GameCore headless steps, not a substituted toy physics system. Study scripts are standalone research harnesses rather than production game extensions.

## Physical skill controller: expanded measurement

Reproduction: `node browser_physics_prototype/research/2026-10-24/extended_skill_study.mjs` (low-priority CPU preferred). Evidence: `extended_results.json`. Four deterministic clean teacher demonstrations produced 255 state/action frames; four **synthetically button-held and mistake-injected** demonstrations produced 387 frames, and every noisy teacher episode completed. Those recordings are not human input. Controls affect real GameCore movement/inertia in the authoritative 3D Rapier world, although this selected movement skill is only along the constrained x axis and not unrestricted 3D locomotion.

The additional eight starts, crossed with seven conditions (normal; carrying one or two planks; knee sprain; fatigue; and forward/backward external velocity perturbations) comprise 56 episodes per controller. Results:

| Controller | Rollout success | Notes |
|---|---:|---|
| Fixed 80-step macro | **4/56** | Cannot respond appropriately to changing movement speed or external impulse |
| Instant-state seven-neighbor non-neural clone, clean teacher | **56/56** | x and velocity feedback, same training condition, but altered environments |
| Six-step-history temporal seven-neighbor clone, clean teacher | **56/56** | No measured improvement over instant-state clone in these scenarios |
| Temporal clone from noisy, delayed synthetic teaching | **12/56** | Poor generalization despite all four teacher episodes finishing |
| Temporal clone from success-filtered noisy teaching | **12/56** | Filtering failed to help because all teaching episodes succeeded |
| Hand-coded state-feedback teacher | **56/56** | Engineering reference, not an unseen human teacher |

The entire set is deterministic. There is **no statistical estimate of probability across random player strategies**, no high-dimensional arm/joint/contact skill and no evidence of true playability. The additional starting positions and conditions were defined after inspecting the earlier original study; they are separated by episodes but not a fully untouched outer scientific holdout. Different early termination and teacher dataset size (255 versus 259) also prevent silently treating this as a direct replay or improvement of the consumed 7/8 result. Keep failed evidence.

### Long interruption and saved controller persistence

An explicit *research-side* opt-in/manual-preemption arbiter was tested at ticks 1, 20, 45 and 70. In all four cases it stopped issuing autonomous actions for another 120 ticks, and continued to issue no autonomous actions after restoring the paused state and testing another 90 ticks; it also refused an incompatible severe injury/fatigue precondition. Invalid model output transferred control to manual. **This arbiter is not integrated into the production PRSE command dispatcher or browser**, so the live player-controlled interruption lifecycle is not verified.

`persisted_controller_study.mjs` with separate `prepare` and `resume` process runs wrote `checkpoint_active.json` and `checkpoint_manual.json` with the cloned skill's 255 training frames, valid serialized GameCore snapshot and controller state, and a dataset SHA-256 integrity guard. A fresh Node process restored the active case and completed the task after 48 policy commands. A fresh Node process restored the manual case, applied 160 explicit manual movement frames, and issued **zero** policy commands. Repeating each loaded checkpoint twice was deterministic; a corrupted checkpoint was rejected. Evidence: `persistence_results.json`. This is proof of research-side controller serialization and the core's world restore, **not** deployed player saves, crash recovery in the production engine, or unchanged command priority across render/voice interfaces. GameCore restores manual direction to neutral, requiring a new actual manual input after reload.

### Implications for controller choice

A simple learned non-neural feedback controller is feasible for this narrow task and significantly more robust than a blind fixed-duration macro. Temporal features did not outperform an adequate instantaneous state representation here. More realistic button-held, delayed and imperfect training caused severe imitation failure despite teacher success: task-level success labels alone cannot identify low-quality actions; train only after task segmentation and context/quality checks, and retain validation in autonomous rollouts. Future controllers should be independently measured on actual human input, contact-rich multidimensional skills, injected sensor noise, simulated missed inputs, mixed injury states and unanticipated obstacle regimes. Avoid claiming universal reliability or fun.

## Hidden mechanisms: inferability is a separate question from opportunities

Reproduction: `node browser_physics_prototype/research/2026-10-24/hidden_inference_study.mjs`. Evidence: `hidden_inference_results.json`. The existing GameCore's actual resonance function remains the source of the real case. The additional single-frequency, double-frequency, constant, slow and causal mechanisms are **synthetic research comparisons**, not installed game content.

A formula-blind deterministic fitting observer received sixteen noisy, rounded intensity readings spaced 1.5 seconds apart. It selected a constant, one-oscillator or two-oscillator Fourier model over a prespecified period grid with a complexity penalty, and forecast a different later time interval. This observer selected the two-frequency family for the actual PRSE resonance but had a later-value root-mean-square error of about **0.37**, despite gate-window classification on about **83%** of twenty-four later samples. More importantly, it **incorrectly selected two-frequency models** for the genuinely single-periodic and constant examples. A deliberately out-of-grid long cycle was mistaken for a constant and gate-window accuracy was about **58%**. These failures expose overfitting, phase aliasing, insufficient horizon and inadequate hypothesis family coverage. The good gate-window classification number is not proof that a person could learn the hidden law.

Causal observational equivalence counterexample: a time-triggered step and an actually controllable switch create **identical passive observations** if the switch naturally turns on at the trigger time. Holding the same world time and experimentally toggling the switch produces the expected different outcomes, distinguishing the mechanisms. A player needs meaningful interventions or controlled trials, not just a fluctuating meter; this example is a pure synthetic causal demonstration, not a new PRSE gameplay mechanic.

With the existing PRSE activation threshold, a sampled 120-second observation contains fifteen qualifying activation windows; the shortest lasts about **0.35 seconds**. If an input is issued exactly after a window starts but delayed by 0.6 seconds, thirteen of fifteen observed windows remain viable, while 1.0 second fits nine of fifteen. These are mathematical best-case reaction-delay comparisons, not real user latency measurements. A synthetic once-per-day oscillator has an opportunity spanning many hours yet may force a long calendar wait without game-time scheduling; a long window is not automatically fair.

### Current research conclusion on learnability and disclosure

A stable single oscillator with a readable time reference, repeatable measurements and partial clues is a plausible first player-research mechanic. Multiple frequencies require enough history and observability to distinguish candidate models; sparse noisy readings can mislead even an idealized fitting observer. Causal rules require repeatable controlled interventions at matched game time or otherwise separable explanatory evidence; uncontrolled passive correlation alone may be fundamentally non-identifying. For fast timing, show an anticipation cue and measure real input-latency tolerance; for slow time, allow journals, in-game planning and player-authorized automatic scheduling without excluding players who cannot play at particular real-world hours. Hidden parameters must not be randomized away every new character unless explicitly chosen.

**No people were recruited and no human observer inferred a rule in this study.** The model-fitting observer, counterfactual causal example and opportunity measurements are not substitutes for a representative blinded human study of comprehension, failure costs, false hypotheses, knowledge retention, and actual enjoyment. This original question remains unanswered empirically.

## PRSE working title

Authentic original recording `Recording 2026-08-13 17-37-45-601.txt` explicitly says the speaker forgot the expansion, offering only an uncertain sequence resembling 'Perception-based, reality, sensor, whatever, emergent'. Another original August 13 recording uses PRSE without expanding it. The exact authentic acronym remains **UNKNOWN**. No guessed expansion was adopted.

## Preservation, reproducibility and outstanding work

Study execution was low-priority CPU-only on busy Nitro. No commands changed the live game server, GPU models, browser, rendering jobs or the dirty main checkout. Primary sources and earlier consumed results remain unchanged. `checkpoint_*.json` are generated fixtures for replay; their exact bytes are preserved. Five existing targeted headless regressions passed without modifying the live engine: hidden-and-character, save-migration, modality-contract, causal-world, and gameplay-journey. Exact command outputs are preserved in `regression_log.txt`. New selected hypotheses and disclosure comparisons are exploratory, **not** a fresh blinded human holdout.

Remaining: full semantic Infra and sixteen Games original transcripts reading, actual captured player demonstrations and user-tested interruptions, production-integrated opt-in habit controller, full 3D body/contact actions, holdout evaluation across independent environments and users, and true human inferability/fast-slow timing tests. No claim of final objective completion is justified.

### Post-study source-coverage follow-through

The remaining sixteen Games recordings were subsequently read in full, and `semantic_coverage.json` was updated to mark **all 23 Games original recordings semantically read**. Relevant newly recovered source detail includes explicit **save at any time without forced save-point constraints** from September 25 18:40, player-controlled optional ability simplification and humorous initial walking from September 24 14:06, and player/agent blinded discovery of randomized influence graphs from September 24 20:20. These support the proposed study design and the user-controlled persistence emphasis, but none is proof of experimental human success. Whole Infra semantic coverage remains incomplete.

### Human investigation apparatus, not human outcomes

The new `human_rule_study_protocol.mjs` presents three anonymous undisclosed generator labels with a limit of twelve freely selected measurement times each, lets the participant choose constant/single/multi-oscillator families and forecast four heldout future threshold activations, then presents two timestamp/switch confounder observations and optional causal interventions before asking for a cause. The program can emit a participant's raw measurement choices, predictions and correctness to an explicit `--output` destination; without it, no participant answers are saved. Do not claim blindness if a participant has code access, and do not claim human testing from the existence of this apparatus.

A non-human scripted terminal exercise completed all prompts and generated `protocol_automated_fixture.json`, which passed a separate JSON shape/result integrity check. The first pexpect wrapper returned an **exit-status bookkeeping assertion failure** because the process status had not yet been collected after EOF; preserve the negative harness failure rather than count that wrapper as a passing full end-to-end subprocess-exit acceptance. The study script itself passed `node --check`. **No human participant interacted with the apparatus.** For a valid human evaluation, isolate source code, preregister participant selection and hypotheses, record response times and false models, compare alternative clue disclosure and timing latencies, and evaluate delayed repeat tests. The stored scripted smoke is explicitly not a real participant.
