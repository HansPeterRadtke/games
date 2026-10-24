# Game Skill Learning and Hidden-Mechanic Research — second continuation, 2026-10-24

This is the second scheduled continuation of the **same task**, not a new holdout. It adds independent constrained headless fence studies, input-latency and cancellation diagnostics, and a save/resume defect investigation to [REPORT.md](REPORT.md) and [CONTINUATION_2026-10-24.md](CONTINUATION_2026-10-24.md). The formerly consumed 7/8 kNN versus 0/8 macro fixture and prior 56/56 movement scenarios remain unchanged, with the same negative evidence intact.

## Ownership, resources, primary sources

Read Nitro `/data/infra/AGENTS.md` before tool effects. All work was in the existing Games isolated branch and worktree under `browser_physics_prototype/research/2026-10-24` or one owned physics-core fix and test. Read the current source for `GameCore` commands/physics/saving, existing core headless suite, PRSE host and browser command adapters, the prior owner reports, semantic-coverage ledger, and preserved original recordings. The complete relevant Games original set — **23 of 23 recordings** — was semantically read in the prior continuation. Readable Infra beyond the 17 source-listed relevant guideline files still is **not semantically complete**: the larger tracked-file inventory is just a byte inventory; do not call it a completed reading.

Inspected the live Games main, which remained heavily dirty; never reset, merged, edited or force-pushed that checkout. The live authoritative PRSE game service and Nitro Blender commercial renderer remained active. Work was low-priority headless CPU; no production GPU allocations or live-session control were requested. The isolated research code is based on the previously committed source snapshot, so the main checkout's uncommitted changes are not represented.

The authentic PRSE name expansion is **UNKNOWN**. A case-insensitive exact search of *all preserved original-recordings* returned just four Games transcripts, of which the August thirteenth seventeenth-hour original explicitly says the speaker had forgotten the expansion. Do not invent one.

## New physical task: actual jump over the existing fence

Run `node browser_physics_prototype/research/2026-10-24/fence_skill_second_pass.mjs`. Evidence: `fence_skill_results.json`. The authoritative headless `GameCore` Rapier simulation runs gravity, impulses, the real fence collider and character landing. The existing world locks lateral z movement: despite 3D collider space, this is an **x/y movement** skill, not full three-axis motion or learned articulated gait.

Four **scripted keyboard-command demonstrations**, not humans, all crossed the physical fence. They supplied eight grounded jump-positive frames for learning. On eight distinct starts crossed with four scenarios (normal, two carried planks, a knee sprain, an imposed backward impulse), thirty-two complete heldout-ish rollouts per controller produced:

| Controller | Completed episodes | Interpretation |
| --- | ---: | --- |
| Engineering feedback demonstrator | **32/32** | Scripted reference only |
| Time-indexed open-loop jump macro | **4/32** | Negative evidence: position/load/timing changes cause missed jumps |
| Tiny instantaneous two-output seven-neighbor controller | **32/32** | Learns both low-level Move and Jump from the scripted demonstrations |
| Learned positive-jump-region state guard | **32/32** | Smaller non-neural alternative |

An apparently perfect small fixed set is **not** evidence of unrestricted/general or truly human-taught motor competence; scenario and policy construction are exploratory and use the same authored obstacle. Training and testing use distinct episodes but do not constitute a preregistered novel final holdout after previous experiment selection. Do not compare these pass fractions as statistical population estimates. No real human has played or taught this skill.

## Transport latency and stale-command interruption

Run `node browser_physics_prototype/research/2026-10-24/fence_latency_study.mjs` **only when intentionally updating its results**; the existing file `fence_latency_results.json` preserves the original pre-fix outcomes. The controller uses only a positive-jump-region learned from the previous saved fence experiment. All five additional start states completed under six observation/delivery configurations: instantaneous, six-frame or twelve-frame observation delay, six-frame command delivery delay, and combined six-frame or twelve-frame delay. These are small, deterministic **engine-level delays**, not measured actual Android/browser network latency.

The interruption arbiter was separately exercised at ticks thirty, forty-eight and fifty-eight with zero, six or twelve queued frames. With an epoch/generation guard, **nine of nine** situations maintained player-only control. Without the guard, **six of nine** allowed buffered *old automated Move commands* to override later player input. This reproduces a concrete dangerous stale-action replay mechanism and shows why merely issuing `TakeManualControl` is not sufficient if a surrounding dispatcher can deliver old commands later. The arbiter exists **only in the research script**, not live PRSE. No human or live browser end-to-end manual override was observed.

## New verified defect: saving between a learned action and a physical jump

The original source `GameCore.snapshot()` omitted the next allowed jump time (`nextJumpAt`) and pending jump input. `GameCore.restore()` silently set a new 150 ms cooldown. A separate problem: restored body transforms were not followed by a Rapier collision-query refresh, so the first `grounded()` query could report false. This consumed a queued Jump without applying an upward impulse.

Evidence was preserved **before patching** in `save_resume_jump_diagnostic_results.json`: identical queued commands from a saved world succeeded uninterrupted at tick 111 but failed after ordinary restore, remaining physically blocked at the fence. A controlled one-field experimental override of `nextJumpAt` restored success even before the second root cause was repaired, but it still left a one-frame difference. A new exact pending-Jump regression initially failed after the cooldown serialization fix alone; a direct query-pipeline diagnostic showed `grounded(): false` immediately after load becoming true after `world.updateSceneQueries()`.

The isolated research branch now contains a minimal **not deployed** GameCore correction: persist and validate optional `nextJumpAt`, `jumpRequested`, and the impact-contact event flag; restore the original cooldown/pending input; refresh world scene queries after setting all restored transforms. Existing older version-five saves without the new fields remain accepted. Manual button-held movement intentionally remains nonpersistent and requires a fresh input adapter command.

`browser_physics_prototype/tests/save-resume-jump-timing.mjs` now passes: the pending jump survives save/load, world velocity agrees on the immediate next step, cooldown stays the same, older saves load, and invalid timing/boolean state fails validation. `save_resume_jump_patched_results.json` demonstrates the formerly failing fence-reload scenario now completes, with the same final frame and **no position divergence** from the uninterrupted reference. The old negative result file has not been overwritten. Fix and tests are isolated from the dirty production main; deploying or merging the patch remains a separately controlled step.

## Human discovery and hidden mechanics: actual progress versus limitations

Do not replay or relabel the earlier model-based inference trial or the synthetic causality/fast-slow window comparison as new human evidence. A targeted read-only aggregate of existing live PRSE event logs showed **38 log files**, with **54 accepted Move direction-change records** across a subset of sessions; many may come from automated testing, and their logs contain neither a reliable human/automated provenance flag nor enough full, synchronized state/action/outcome trajectories for demonstrated skill-quality assessment. No identifiers, raw play logs, chat text or personal session data were exported or committed.

All **23 original game recordings** have verified semantic coverage in `semantic_coverage.json`, including the forgotten PRSE acronym. Direct original evidence distinguishes the recorded requirements (observable persistent causal hidden laws, experiments, manual mastery, optional automation, save anytime) from examples (sine, magic, a hypothetical switch, ritual, invisible energy) and unanswered scientific questions (exact disclosure, fair fast/slow timing, actual player enjoyment).

A participant-facing terminal discovery protocol and automated fixture already exist, but **no participant was enrolled**. Published human research motivates the missing evaluation, not a local result. Lynch, Jefferson and Hinrichs (DiGRA 2022), https://doi.org/10.26503/dl.v2022i1.1376, observed thirty-one Sudoku players whose actual strategies differed from typical AI-player assumptions. Cloude and colleagues (Frontiers in Education 2020), https://doi.org/10.3389/feduc.2020.572546, investigated sixty-eight undergraduates and emphasized that task actions alone cannot establish whether someone is engaging in scientific reasoning. These are methodological analogies only, **not tests of the PRSE hidden rules**. Actual PRSE human success, puzzle fairness, player enjoyment, real fast-reaction latency and long-period accessibility remain **unknown**.

## Reproduction and verification

New scripts and their immutable first results are: `fence_skill_second_pass.mjs` / `fence_skill_results.json`; `fence_latency_study.mjs` / `fence_latency_results.json`; `save_resume_jump_diagnostic.mjs` / both negative and patched JSON files. The new positive behavior test is `browser_physics_prototype/tests/save-resume-jump-timing.mjs`. All tests use the *existing*, authoritative Rapier 3D physics engine and no GPU. Five targeted earlier game headless regression results were already retained in `regression_log.txt`; the additional full suite result is reported by the separate full-suite log when verified.

The remaining objective is genuine user or recruited-human demonstration/diagnostic data with consent and recorded source labels, independent human hidden-rule learning studies, production controller handoff integration, contact-rich multidimensional skill transfer, and exhaustive semantic reading of all tracked Infra guidance. Neither a synthetic player, a rule-fitting model, a terminal-protocol fixture nor source-scanning can satisfy the human observations. **Research status is partial**, not complete.


### Final verification status for this second pass

The bounded **full** `run-game-tests.sh` attempt exceeded its 150-second wall limit while running `tests/narrative-roundtrip.mjs`, after ten earlier tests completed successfully. Retain `full_headless_regression_second_pass.log` verbatim; do not claim all twenty-three headless tests passed and do not automatically replay the uncertain timed-out narrative test. Exit status was **124**, an ordinary incomplete execution, not a known failing assertion in the edited save code.

Separately completed low-priority regressions **all passed**: `tests/save-migration.mjs`, `tests/modality-contract.mjs`, `tests/event-journal.mjs`, `tests/gameplay-journey.mjs`, and the new `tests/save-resume-jump-timing.mjs`; exact retained output is `save_related_regressions_second_pass.log`. A private temporary Nitro PRSE headless WebSocket server smoke also **passed**, including server physics, command acknowledgement, reconnect, save/import and event logging; its output is `headless_server_smoke_second_pass.log`. This temporary server was not the live service. The original first attempt at the new exact jump regression failed after only the cooldown fix; adding the Rapier query-pipeline refresh made that regression pass, and the failing pre-patch reproduction remains retained.

When taking this patch into the canonical Games main later, reconcile the concurrent, currently dirty main physics file rather than overwriting it. This research branch's correction has been proved only on its own pinned source revision and has **not** been installed in the running PRSE service. Testing the current live code and a real user-initiated save in the browser is still outstanding.

### Preservation and safe replay of experiments

The three original bounded study scripts now refuse to overwrite any existing JSON output. Their first results, including the negative save and unsafe-interruption observations, are frozen in this commit. To rerun intentionally, supply an unused basename through `--output=fresh_replay_name.json`; the scripts constrain it to a filename inside the same research directory and create it exclusively. Do not confuse fresh exploratory replays with new preregistered holdouts. The separate published human-protocol fixture is also synthetic; no invented participant data was added.
