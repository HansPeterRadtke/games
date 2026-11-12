# HPR Gameplay Systems Suite — integrated training arena

Version 0.3.0 internal review candidate. This is original Unity C# source plus
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
* **Weapons:** magazine, reserve ammunition, reloading and cooldowns.
  Cursor-directed raycasting checks collision geometry and line of sight;
  missed shots still consume ammunition. A scripted button exercises the
  target firing path in the code walkthrough.
* **Enemy:** deterministic health, cooldowns and proximity-based automatic chase/attack
  within the sample arena; the included finite-state decision module is not
  NavMesh pathfinding, obstacle routing or generative AI.
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

**Security baseline (November 2026):** For new release builds and active
development, use the Unity 6000.6.8f1 editor (or a separately verified patched
Unity LTS stream). Older Unity 6000.4 and 6000.6.7 projects were used for
compatibility testing before the October 2026 eMudhra/Brotli security
updates; do not use them as a security-patched buyer-release baseline.
The builder verifies the editor version before creating output. See the
security patch audit in the repository research documents.

Import the single `.unitypackage` into a security-patched Unity 6000.6.8f1 project. The content is
inside `Assets/HPRGameplaySuite`; do not additionally install any of the ten
individual `com.hpr.*` packages, because this duplicates assemblies.
Open `Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity` and press
Play. All scene dependencies and sample ScriptableObject assets are included.
See `QUICKSTART.md` for the complete player route and `ARCHITECTURE.md`
for C# integration examples and extension points.

### Add an ability to an existing player

Open **Tools > HPR > Gameplay Suite > Integration Guide** and choose **Create my
own editable healing ability**. The guide copies the ability and its linked
effect into your project folder. It gives each copy an independent identifier.

Select your player in the scene, then use **Tools > HPR > Gameplay Suite >
Attach Ability to Selected Object**. The installer previews the configuration
and lets you attach or remove the runner with Undo. See `QUICKSTART.md` for
the resource component and scene-saving steps. The guide also reports missing
package files and opens the showcase.

### Render pipeline and tool compatibility

The scene's material examples use Unity Standard/Lit-style metallic and
smoothness channels. In a Built-in Render Pipeline project they are ready as
imported. In an existing **URP** or **HDRP** project, first ensure that the
chosen Render Pipeline package and project asset are set up, then deliberately
select **Tools > HPR > Gameplay Suite > Adapt Demo Materials to Current Render
Pipeline**. This explicit action retargets only the suite's included sample
materials; it does not install packages, change project Graphics Settings, or
silently alter unrelated assets. Do not run it on an unknown/custom pipeline.
URP/HDRP are optional host-project renderers, not required runtime dependencies.

Unity 6.6 introduces an official Asset Store compatibility requirement for
entering Play mode with domain reload disabled. This newer compatibility mode
and URP/HDRP import must be tested independently before claiming those features
as accepted; prior validation used Unity 6000.4 Built-in.


The arena uses Unity built-in primitives and standard materials, collision-aware
top-down WASD/arrow movement with a Unity CharacterController, cursor-aimed
hitscan weapons, a deterministic chase/attack encounter, and runtime IMGUI. It deliberately does not
provide a full third-person character controller, authored animation, NavMesh routing,
character animations, complex inventory grids or multiplayer synchronization.
The training target fire button aims at the actual target collider,
while the F keyboard action aims at the mouse cursor; both respect collision.
The enemy-attack button intentionally forces a close-range test scenario;
automatic chase and attack use actual separation and runtime cooldowns. The ability area hit
does use a Unity physics overlap and type-safe event delivery.

## Saving and portability

The example writes only if a user explicitly presses **Save disk slot**.
It stores JSON at
`Application.persistentDataPath/HPRGameplaySuite/demo-slot.json`.
Load requires an existing, compatible version-three JSON slot. It writes using
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


### Input without forcing another package

The demonstration exposes its keyboard bindings and interaction reach in the
controller Inspector. `HprSuiteInput` uses the legacy Input Manager only when that
backend is active, or Unity's optional Input System API when the corresponding
compile-time symbol is active. The shared gameplay runtime modules do not
require the Input System package. Professional games can inject their own
`IHprSuiteInputSource` for existing input actions, gamepads or test
fakes, instead of changing the project's Active Input Handling setting.
Not every historical KeyCode name maps to the Input System key enumeration;
use standard letter, arrow and action keys or a custom adapter when needed.


### Stable assets and upgrading an existing installation

The included scene and sample data are original Unity YAML source assets with
source-controlled `.meta` files. The runtime scripts, editor tools, demo scene
and sample ScriptableObjects retain stable Unity GUID identities across release
builds. We do not generate new GUIDs every time the buyer archive is created.

The repository's private release builder reads a checked-in authoring baseline
and exports it without opening or rewriting the demo. An internal scene builder
is only for a brand-new disposable authoring project; it refuses to overwrite
existing scene or sample files. The cleanroom archive validator checks asset
GUIDs against the version-controlled baseline.

**Upgrade policy:** Back up or version-control your own project before
importing any Asset Store update. Never modify `Assets/HPRGameplaySuite`
shipped source/assets directly if you want straightforward upgrades; derive or
copy samples into your own game namespace and change the copies. Unity GUID
stability preserves object identity, but it does not migrate every custom
serialized property or guarantee all future API compatibility.
