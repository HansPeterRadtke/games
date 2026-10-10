# Browser game — shared 3D simulation with a 2D viewport

Live game: `https://nitro.jonnyontherun.org/llm_game/` (original route). Static app source at `browser_physics_prototype/`; the original Nitro Apache `/llm_game/` alias remains on `LLM_Game/web/`. The root HTML loads the prototype modules through an explicit `base` path.

- `physics-core.js`: authoritative game state, commands, fixed stepping, impacts, canonical game events and snapshots. Rapier 3D is the physical backend; the renderer does not own physics.
- `active-ragdoll.js`: ten independent three-dimensional bodies with nine articulated hinge motors, force-based animation/root-follow controller, switchable passive fall, knockback, asymmetric knee impairment, physical limb collision and state restore.
- `semantic-world.js`: PRSE-style off-screen semantic state and durable entity identity, descriptions, movement and lineages.
- `world-bridge.js`: materialization of nearby semantic entities into actual dynamic rigid bodies, physical-to-semantic capture when they leave perception, reconstruction after return/save. Only an initial deterministic seed actor exists; procedural LLM synthesis is not implemented.
- `game.js`: side-view Canvas adapter; currently uses 2D Kenney character sprites (CC0) and stylized renderings of actual articulated body poses. Switching renderers should not change outcomes.

Controls: A/D or arrows to move, Space to jump, Enter to focus command field, G/"Cross fence" for semantic goal, Escape to interrupt; the mannequin can stand under powered pose assistance, attempt stepping, relax completely, be pushed, have its left knee motor impaired and be restored.

**Doability boundary:** The mannequin's hip/root is animated via applied forces, not a physiologically valid self-balanced active-ragdoll. Rapier still authoritatively solves gravity, joints, limb contacts and collisions; pose assistance can be turned off to observe the passive fall. Knee impairment currently affects torque strength only, not anatomy/bleeding/injury diagnosis. See `PHYSICS_DOABILITY_2026-10-10.md` for measured feasibility findings and open research.

Run all deterministic tests with `node test-physics.mjs && node tests/active-regression.mjs && node tests/local-obstacle-regression.mjs && node tests/prse-transition.mjs && node tests/semantic-input-regression.mjs && node tests/injury-response-study.mjs && node tests/performance.mjs`. Browser validation uses `tests/browser-smoke.py` against a pre-existing test CDP host and creates/disposes an isolated context without altering other tabs. Mobile test: `MOBILE=1 python3 tests/browser-smoke.py`.
