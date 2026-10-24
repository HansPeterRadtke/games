# Coverage/evidence ledger (2026-10-24)

- Read `AGENTS.md` first on Nitro; inspected Infra working tree (817 tracked files; unrelated dirty files), canonical Games Git status, active processes, project README, authoritative host README, physics core commands and stepping, hidden-mechanism implementation, and a relevant existing test.
- Read complete `games/learned_habits_and_automation.md` and `games/hidden_systems_and_player_research.md`, and exact PRSE-containing snippets from four original game recordings including August 13, 17:37 and 18:11. Original recordings have **not** all been read in full.
- Required other game and general guideline text is **not yet verified as fully read**; do not infer compliance from inventory scanning. `infra_inventory.json` enumerates tracked bytes/hash with explicit `byte-inventoried-not-semantically-read` status for every entry. Deep reading and section coverage must be performed later.
- Headless reproducible script executed, `results.json` written; existing physics hidden/character test passed. No human playtest, neural controller, full interruption lifecycle or external deployment.
- Primary evidence: script + JSON, existing authoritative source and exact original recording paths; no claim of production game success.

## Same-day continuation, additional verified coverage

Read the updated Nitro Infra AGENTS.md **first** in this continuation, including its explicit commit/push-on-verified-work rule. Read all seventeen applicable general or game guideline files listed with per-file section headings and manually assessed semantic notes in `semantic_coverage.json`. Also read the **full text** of seven original Games recordings: August 13 (17:37 and 18:11), September 22 (16:21 and 19:29), October 9 (12:16 and 18:04), October 14 (18:33). Scanned all twenty-three original Games recordings for PRSE/learning/frequency terms, but sixteen were **not read in full**; do not report comprehensive semantic coverage. The much larger remaining Infra tracked human-readable tree remains hash-inventoried only, not deeply read.

New tests and independent measured outputs: `extended_skill_study.mjs` -> `extended_results.json`, `persisted_controller_study.mjs prepare` and `resume` in separate processes -> preserved checkpoints and `persistence_results.json`, `hidden_inference_study.mjs` -> `hidden_inference_results.json`. All comparisons, negative results, non-human limitations and corpus scope are described in `CONTINUATION_2026-10-24.md`. Existing original first-run `results.json` was not rewritten. No user human playtest has taken place.

### Completion of game-original semantic reading

Read all sixteen formerly only-term-scanned Games originals in full in bounded tool outputs; their individual semantic topics are now in `semantic_coverage.json`. **Twenty-three of twenty-three Games original transcripts have full semantic text coverage**, including very brief or repeated recordings. This does not establish that all tracked Infra non-game documents have been semantically read. No game-play participant or real human demonstration has been enrolled or observed.

The user-observation trial interface (`human_rule_study_protocol.mjs`) was built but no human was enrolled. The first automated pexpect wrapper produced the correct output fixture yet failed an exit-code assertion because its child exit status was not collected; the recorded fixture independently passed JSON checks. This is **not** a completed interactive human test. The existing game's full five-test regression stdout/stderr is retained in `regression_log.txt` and intentionally force-added to the owned research commit despite the repository's broad `*log.txt` ignore rule; no secrets or user data are present in these test logs.
