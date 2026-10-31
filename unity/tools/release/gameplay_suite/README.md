# HPR Gameplay Systems Suite — integrated training arena

Version 0.2.0 internal review candidate. This is original Unity C# source plus
one purpose-built training arena, not a complete FPS controller, character-art
pack, cloud service, networking solution, navigation AI, or finished game.
The ten original runtimes are delivered as one Unity Asset Store package with
the project root at `Assets/HPRGameplaySuite`. The nine former individual
submissions were declined; this is an independently developed integration
candidate, **not an approved or published listing**.

## What actually works

The Training Arena demonstrates cross-system features from all ten included
modules without additional Registry dependencies:

* **EventBus:** typed `DamageEvent` and ability/pickup events; player stats
  and enemy adapters subscribe independently.
* **Inventory:** pick up a medkit and a training key with `IInteractable`;
  consume a medkit for recovery and collect loot from an eliminated target.
* **Interaction:** approach two pickup stations, then approach the locked
  gate with the collected key to toggle its open state.
* **Stats:** health, stamina, healing and typed combat damage.
* **Weapons:** magazine, reserve ammunition, reloading, cooldowns and hits.
* **Enemy:** deterministic health, attacks and cooldowns. It does not
  independently pathfind, navigate or use generative AI.
* **Abilities:** unlockable heal and area-damage abilities, stamina cost,
  physics-overlap selection and cooldowns. Area damage reaches the enemy via
  the same typed damage event used by other systems.
* **Composition:** a real service registry resolves inventory, stats and
  abilities during actions.
* **World:** a ScriptableObject asset metadata registry resolves the included
  medkit definition by stable identifier.
* **Save:** schema-versioned encounter snapshots restore position, health,
  stamina, inventory, ammunition, weapon and enemy cooldown, enemy health,
  ability unlock/cooldown state, pickup availability and door state. Memory
  checkpoint and **opt-in local JSON save/load slot** are both demonstrated.

## Installation

Import the single `.unitypackage` into a Unity 6000.4 project. The content is
inside `Assets/HPRGameplaySuite`; do not additionally install any of the ten
individual `com.hpr.*` packages, because this duplicates assemblies.
Open `Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity` and press
Play. All scene dependencies and sample ScriptableObject assets are included.
See `QUICKSTART.md` for the complete player route and `ARCHITECTURE.md`
for C# integration examples and extension points.

The arena uses Unity built-in primitives and standard materials, simple
top-down WASD/arrow movement, and runtime IMGUI. It deliberately does not
provide physics collision-aware movement, full combat aiming, enemy navigation,
character animations, complex inventory grids or multiplayer synchronization.
The weapon button targets the training enemy directly, and the enemy-attack
button simulates a deterministic close-range encounter. The ability area hit
does use a Unity physics overlap and type-safe event delivery.

## Saving and portability

The example writes only if a user explicitly presses **Save disk slot**.
It stores JSON at
`Application.persistentDataPath/HPRGameplaySuite/demo-slot.json`.
Load requires an existing, compatible version-two JSON slot. It writes using
a temporary file and replacement on supported local filesystems; failure or
corruption is reported on-screen without overwriting the live encounter.
This is an illustrative local save slot; it is not encrypted, tamper-resistant,
autosaved, cloud-synced, or multiplayer-authoritative. Consumers should add
their own game-specific validation, migrations and integrity protection.
The modular HPR Save runtime remains a **data contract**, not an automatic
full-project persistence solution.

No external art, runtime model inference, user tracking, outbound requests,
online accounts, or API keys are included or required. The C# source is
provided under `LICENSE.md`, and `ThirdPartyNotices.md` inventories rights.

## Validation and AI disclosure

Source unit-test assemblies are retained in the development repository, not
installed in buyers' runtime assemblies. The development pipeline builds
in Unity 6000.4, exports a real .unitypackage, imports it into a completely
fresh Unity project, and executes independent runtime tests. Evidence and
logs stay outside Git and are not a claim of marketplace approval.

**AI-assisted coding tools** contributed to original HPR C# modules, the
integrated demonstration, engineering iterations, automated tests, and docs.
Developers reviewed the architecture, connected the components, built
deterministic tests, and verified the imported archives using Unity. The
publisher must also accurately identify the specific tools used in the
Asset Store's dedicated AI Description field, and disclose the scope and
manual corrections performed. AI-generated or AI-assisted code is not
represented as exclusively human-authored.

### Dependency-free cleanroom compilation

All ten included runtimes use Unity APIs with no external UI or art packages.
Legacy standalone module demos that require the UI package are excluded.
The shipped demo uses immediate-mode controls provided by the Editor/Unity.
The buyer archive is tested in a fresh Unity 6000.4 project without adding
`com.unity.ugui` or any unrelated Unity Registry package.

This package has **not** been resubmitted to Unity since the rejection of the
former standalone products. It is a technical and product-quality candidate.
