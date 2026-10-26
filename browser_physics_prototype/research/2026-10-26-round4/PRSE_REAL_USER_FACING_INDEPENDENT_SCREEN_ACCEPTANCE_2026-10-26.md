# PRSE — actual final user-facing outcome and canonical viewer acceptance
26 October 2026 — Round four, owner-directed independent research on Nitro

## Owner's actual question and decision

The original owner recordings of 13 August and 9 October describe an unusual game whose **persistent literary semantic world** can materialize into **one authoritative genuinely three-dimensional Rapier world** with source-correct object identities, categories, metric sizes, geometry, relative positions, physical supports and contact, forces and emergent effects. The physical state must then return to **truthful current, observer-limited prose**, preserve historical literary source, advance unseen offscreen processes coherently, and rematerialize with the same persistent object identities. Player macros and controller demos are secondary.

**Answer from this round: PARTIAL.** The real existing playable PRSE browser, Nitro-hosted GameCore/Rapier, user actions, ordinary text narration, native separate physical event demonstration, save/reload/reconnect, and desktop/mobile rendering function when tested end-to-end. But an actual independently human-written literary scene entered through the production-adjacent browser **does not generate that room or those objects**. It instead produces help text unrelated to the author's scene; the private saved authoritative scene remains the existing forest world. Therefore neither a graceful screenshot nor a correct rigid-body physics study is an answer to the owner's general text ↔ physical ↔ text vision.

## Scope, source versions, and isolation

The current Nitro infrastructure policy, recording-derived game semantic/physics and audio-style guidelines, original 13 August and 9 October source-recording identity hashes, prior same-body/human-authored SceneEval and LEGO-Bench studies and negative controls, the canonical PRSE HTTP/WS/DOM implementation, and the dedicated Games research branch were inspected before testing. The dedicated branch began at previously remote-verified round-three revision. Another worker's untracked round-two research files under `browser_physics_prototype/research/2026-10-26/` remain intact and are not part of this commit.

Two **distinct source versions** were tested independently, not conflated:

1. **Committed research branch:** current isolated Games worktree `research/game-skills-hidden-20261024`. The unchanged committed `browser_physics_prototype/viewer.html`, `viewer.js`, renderer and `prse_runtime/server.mjs` were served by an ephemeral private HTTP/WS forwarder to a new isolated real GameCore process.
2. **Current canonical working-tree snapshot:** `/data/src/github/games` has **other agents' uncommitted modifications** to `LLM_Game/web/index.html`, `browser_physics_prototype/viewer.js`, `physics-core.js`, `prse_runtime/server.mjs`, several supporting modules, etc. The current landing page, current viewer with new inspector/study controls and current server sources were executed **read-only** in a distinct private server/browser test, with exact SHA-256 hashes of eight relevant canonical source files recorded before and after. Those hashes remained unchanged. Their on-disk snapshot is **not asserted equal to binaries loaded by the pre-existing long-running production service**. No merge, restart, sync to production, or modification of the dirty canonical checkout occurred.

For both, a new private server used ephemeral loopback ports **not** 18764 and an owner-private data directory, and the test browser used Chromium remote-debugger disposable BrowserContext and new target, closed after the run. Existing browser tabs were untouched. All test subprocesses stopped. The production process and Apache mapping remained unchanged; no Jetson/LLM inference or GPU requests, no login, no calendar event or external publication. The canonical model endpoint was set to an intentionally unavailable localhost endpoint so no real Jetson call could occur. Screenshots and raw data remain owner-private, mode 0600 under a mode-0700 folder.

## First check: native headless production-facing WebSocket protocol

The existing real headless acceptance, run against its own private GameCore process, **passed** movement, `look`, explicit save, WebSocket reconnect with the same token and position, legacy save import, invalid snapshot rejection, real candle-lighting interaction/event, durable event log and 60 Hz configured physics. This is not a test of import from arbitrary prose.

## Real captured Chromium: committed research branch

The browser loaded the unchanged genuine `viewer.js`, not a research recreation. The local private WebSocket backend sent native GameCore state, and the UI rendered it through the existing `SideViewRenderer`. These observations came from real DOM pixels/text and private backend state, not merely intermediate JSON:

- UI connected and showed the real narrated forest path. One `look` result repeated the same plank descriptive sentence **four times** for four distinct physically present planks; a quality warning for narrative compression, not proof of a false entity.
- Keyboard movement displaced the player **2.855 m** in native state.
- Save acknowledged; reload and WebSocket interruption/reconnect retained the same capability token and restored position with **zero measured displacement**.
- Actual desktop screenshot: `private-real-game-desktop-v1.png`, 780×493, 198,649 bytes. Actual mobile screenshot: `private-real-game-mobile-v1.png`, 720×1480 (device scale two), 220,132 bytes. Both had substantial real pixel variance (contrast proxy ~70.57 and ~75.29), not blank synthetic images. Source and screenshot hashes saved with receipt.
- On mobile 360 CSS pixels: document width also 360, **zero horizontal overflow**, and **no buttons shorter than 44 CSS pixels**. The connected private backend health advertised physics 60 Hz and display 10 Hz; these are server configuration reports, **not** independent throughput/latency measurements.
- Private raw transcript, screenshots, backend logs and saved GameCore snapshot are protected under the Round Four owner-private evidence folder. Both backend and UI helper processes stopped.

## Original human literary source in the REAL browser — final user-facing failure

An independently human-written LEGO-Bench example asserts exactly: **“A projector in the conference room is on the table.”** It was submitted in the genuine browser form, below the existing 120-character command limit, to the private authoritative GameCore server. The **visible UI response** was:

> No supported action for bench. Try: look, read note, light candle, ignite note, pour water, wait 10, jump over fence.

This is both an explicit **functionality failure** (no author-specified conference room/projector/table instantiated) and a response-relevance error (invented reference to the existing forest game's **bench**, not the submitted scene). The private persisted authoritative GameCore snapshot kept exactly eleven preexisting semantic world objects; no `projector` or `table` appeared. The actual rendered failure screen `private-literary-entry-rejected-v3.png` is 780×493 and 94,069 bytes, captured from the browser. The first attempt used a wrong research-only startup path, failed before the private backend became available, and its logs were preserved. The corrected distinct v3 experiment passed its evidence and was not a retry of any denied external effect. No production-side import was attempted.

## Real Chromium against CURRENT canonical code, without changing that checkout

A *different*, newly created private GameCore instance read the current Nitro canonical server, landing-page HTML, browser viewer and supporting sources. The actual canonical landing page at `/llm_game/` loaded `viewer.js`; an isolated private test WebSocket supplied the real source-dependent server state.

Browser-side `prse-research` inspection correctly displayed that the **shelter was not yet generated** in the current player session. The user-facing **research study** button then sent `run_study`, which spawned the canonical `prse_runtime/studies/candle-causality.mjs` Worker in a **separate authoritative GameCore**. The real headless physics experiment verified a candle contacting paper after the candle was knocked, recording native positions (candle around x=36.7055, y=.4833; note around x=36.7000, y=.4510) and candle tilt **2.259 radians**. On leaving, the semantic consequences made the note ashes, bench scorched, shelter smoky; on returning, a physical note object was recreated. The study itself reported success, and the original actual browser display text included:

> PASS: An independent Nitro world was simulated for this experiment. No changes were made to your world.
>
> After lighting the candle: note intact, with 0 fire transitions.
>
> After knocking it: actual Rapier 3D candle-paper contact detected.
>
> After leaving: note ashes, bench scorched, shelter smoky.
>
> On return: physical note object recreated. Elapsed 6.11s.

This is a valid **user-click → WebSocket → server worker → real 3D physics/event/offscreen consequences → final rendered user-visible browser report** for the particular hardcoded candle test. **It is not an in-player-session arbitrary literary world.** The private player snapshot continued to contain its original eleven forest entities, with **no** shelter note/bench/candle generated in the player's real session. Its event log confirmed exactly one `study_started` and one successful `study_completed`, with **zero player `Interact` events, zero player-session note ignition and zero model requests**. Therefore this independent worker neither faked user world effects nor silently altered the live game.

A true player keypress moved the canonical browser's native player **1.485 m**. Its new durable-save acknowledgement, reload into same token with zero player-position deviation, and 360-CSS-pixel mobile screenshot all passed; mobile document width was exactly 360, touch heights ≥44 px, and no overflow. Captured from the actual current canonical UI:

- `private-canonical-study-desktop-v4.png`, 765×1965, 249,602 bytes: full-page actual rendered result.
- `private-canonical-literary-refusal-desktop-v4.png`, 780×493, 92,953 bytes.
- `private-canonical-mobile-study-panel-v4.png`, 720×1480, 170,484 bytes.

Crucially, **the same human projector-on-table literary request still returned the spurious "No supported action for bench" help text**, and no projector/table appeared in the private saved actual GameCore world. Current canonical dirty source hashes were unchanged before/after, and all six screenshots across both code versions were SHA-256 verified and visually nonblank.

## Reproducibility, costs and quality labels

Owned scripts under this round's isolated `browser_physics_prototype/research/2026-10-26-round4/`:

- `private_unmodified_viewer_proxy.mjs` and `private_real_viewer_acceptance.py` — private actual clean research viewer and backend browser.
- `literary_user_entry_rejection_browser_v3.py` — browser-originated authentic human source sentence against the actual GameCore protocol.
- `private_canonical_uncommitted_viewer_proxy.mjs` and `private_current_canonical_browser_acceptance_v4.py` — current dirty canonical source read-only + private backend + current on-screen study and literary failure.
- `prse_round4_readonly_final_acceptance_verify.py` and `prse_round4_readonly_final_acceptance_verify_v2.py` — rerunnable checks of SHA-256 source snapshots, all six exact original PNG files (dimensions, nonblank pixel statistics, size), private mode flags, actual original WebSocket session snapshots and event logs, real DOM report, physical study receipts and false scene creation.
- Three publicly safe aggregate JSON summaries for v1, v3 and v4. Complete HTML/LLM request-independent results and PNG files stay owner-private.

Round-four *new* physics-study user's browser-displayed duration was **6.11 seconds**, not language-model latency or whole-game frame time. Original isolated research UI's native headless acceptance was also run. No freshly generated literary paragraph underwent independent human quality evaluation, no true positive/negative source-to-instance/geometry score is claimed here, and no scale-calibrated physics asset was verified in the browser. The earlier SceneEval and LEGO same-body gold results and v1/v2/native negatives remain separate from this final-outcome study; no denied random feasible-parent placebo was rerun.

## Decision / most useful subsequent work

The engine-facing UI must gain a versioned, source-provenance-aware **author scene import** path into a multi-room instance-correct scene plan with metric approved 3D collider/mesh geometry and explicit uncertain referents, validated against real Rapier geometry before user activation. This must update the **player's actual authoritative world**, not only spawn a separate research worker; then independent human source facts, negative cases, physically caused events and observer-limited output need end-to-end evaluation in the real viewer and CLI with matched controls and recorded cost. An LLM's freeform phrase or a successful current demo study cannot constitute source meaning.

The bounded existing headless user game and independent physical study **work**, but unrestricted persistent literary text ↔ realistic 3D world ↔ independently truthful evolving literary narration remains **UNPROVEN**.

**Status: PARTIAL.**
