# HPR Gameplay Systems Suite — Unity Asset Store draft listing

**Status:** Private candidate only. Do not submit until verified buyer package,
screenshots, AI disclosure, verified publisher account, and curation eligibility.
Publisher: original Multiverse3d account; do not create a second account.
Category: Tools > Game Toolkits. Extension Asset. Proposed version 0.2.0.
The price is not fixed; initial lower-priced positioning needs buyer validation.

## Title

HPR Gameplay Systems Suite — Modular Combat, Inventory and Save Demo

## Short description

A source-level Unity gameplay toolkit connecting ten C# runtime modules in
one interactive training arena. Learn and adapt typed events, item pickups,
keyed doors, player stats, timed abilities, weapons, deterministic enemy
combat and save/restore in one dependency-free example.

## Full description

HPR Gameplay Systems Suite brings together ten focused C# runtime modules
under one package root, with a completely integrated demonstration scene.
It is designed for Unity programmers who want to inspect, extend and embed
modular gameplay code rather than commit to a large visual-scripting engine.

The included modules cover a type-safe event bus, composition/service
resolution, save-state contracts, health and stamina, item inventory, player
interaction, ability effects and cooldowns, magazine-based weapons, deterministic
enemy state/attacks and ScriptableObject world-asset metadata lookup.

The original training arena shows how those parts cooperate: collect a
medkit, retrieve a key, open a locked gate, fire and reload, take typed-event
damage, spend stamina for healing or an area pulse, collect enemy loot, save
a checkpoint and restore the full encounter. The example demonstrates both
in-memory checkpoints and an explicit local JSON save slot with schema
validation. The included source explains where to add your own game systems.

This package ships C# source, demo scene, sample data assets, a scene rebuild
menu, integrated examples, quickstart and API documentation. It does not require
third-party Asset Store packages, user accounts, runtime inference, telemetry
or online services. A complete Unity 6000.4 clean-project import is part of the
development acceptance process.

**Important scope limits:** The training scene uses original Unity primitives,
planar keyboard movement and a simple immediate-mode HUD. It is not a finished
FPS controller, advanced navigation AI, camera-aiming combat system, production
inventory UI, multiplayer SDK or complete cross-project save framework.
The enemy decision runtime is deterministic and contains no generative AI.
The optional JSON example is a local illustration, not secure or cloud
persistence. All gameplay rules are intended for customization.

**Compatibility:** Independently tested with Unity 6000.4.0f1 and Built-in
Render Pipeline. Additional Unity versions and URP/HDRP configurations are
not yet independently certified. Third-party required packages: none.

**Third-party notices:** No third-party art or runtime plugins are bundled.
A per-module license and consolidated notices are included. Unity itself is
an external dependency.

## Technical details

Ten original HPR runtime modules and one integrated playable primitive-based
scene. Original HPR module sources included. ScriptableObjects for inventory,
weapons, enemy configuration, abilities, effects and asset registry. Independent
module source tests remain in the development repository, while the buyer
archive excludes test runner assemblies and obsolete individual demos.
The sample uses a single `Assets/HPRGameplaySuite` folder.

**Controls:** WASD or arrows move, E interacts, F fires, R reloads,
H consumes a medkit, Q heals using stamina, Space uses an area damage
ability, K saves a memory checkpoint and L restores it. On-screen buttons
provide the same options plus opt-in local JSON save/load.

## AI description — mandatory publisher field, draft requires provenance sign-off

OpenAI ChatGPT assisted with authoring and revising part of the C# code
for the original HPR gameplay modules, additional integration adapters,
demo controller and Unity editor scene builder, packaging automation,
documentation and test code. The original module work had AI assistance;
the complete list of AI tools used for that earlier work must be confirmed
from original project records before any submission. The implementation
was substantially reorganized into one product, code was inspected and
bugs fixed, ten module functions were integrated through real services,
typed events, state snapshots and a playable scene, and independently
tested using real Unity package imports and runtime tests. No AI-generated
visual assets are included in the package. The product runs without AI
models or third-party API calls.

**Not ready to paste until tool provenance is verified.** Unity requires the
actual tools and generated content to be disclosed accurately, not simply
the general phrase “AI assisted”.

## Marketing image requirements

Use real Unity-captured screenshots from the imported package; label them
faithfully (“Training arena”, “Weapon, inventory & abilities”, “Full encounter
snapshot”, “Code/API structure”). Prepare a clean cover and card using the
actual scene or a minimal original graphic, title and publisher identity
only. Do not imply sophisticated characters, realistic art, autonomous
enemy navigation, chatbots or visual scripting beyond what is delivered.
Reviewers require truthful actual functionality and a working demo.
