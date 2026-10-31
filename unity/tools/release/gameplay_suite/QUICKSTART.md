# Five-minute buyer walkthrough

This is a **code toolkit**, not a premade game. Start Unity 6000.4 or later,
import the supplied `.unitypackage`, then open:
`Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity`.

Press Play. The blue-armored capsule is the player and the orange target is the
training target. Move using W, A, S, D or arrow keys. The cyan cube dispenses
one medkit; the small amber cube dispenses a training key. Stand near a cube
and press E (or press **Interact**) to pick it up. Walk to the amber gate and
press E to open it. The gate demonstrates the real `KeyDoorInteractable`
and inventory key check.

Point your mouse over the target and press F to fire the rifle along a real
physics ray, or use the scripted training-fire button to aim at the target.
A crate or another solid obstacle can block shots; ammunition is still spent
on a miss. Press R to reload. Cooldowns and ammunition are real
`WeaponRuntimeState` values. Press **Enemy attacks** to simulate an adjacent
opponent's attack; health decreases via a typed `DamageEvent`. In the demo,
the enemy follows the player while within chase range and automatically
attacks when close enough. Its movement uses collision-aware Unity primitives,
not a NavMesh route planner or generative decision system. The **Enemy attacks**
button independently demonstrates the close-range event path without waiting.

Press Q for the recovery ability; it consumes stamina, restores health and
enters a cooldown. Press Space to activate the pulse ability; a Unity physics
overlap finds the target collider and publishes a typed `DamageEvent` which
the training arena routes to `EnemyRuntimeState`. An enemy killed with either
weapon or ability awards exactly one medkit. Press H to consume a medkit.

Press K to store a memory checkpoint and L to restore it. You can verify that
magazine ammunition, both ability cooldowns, player stamina, enemy health,
door state, and collected pickups return to their saved values. The buttons
**Save disk slot** and **Load disk slot** explicitly serialize that same
state to JSON and restore it, including after stopping and restarting Play.

The on-screen HUD shows the composed services and the world registry lookup.
Explore `Integration/HprGameplaySuitePlayground.cs` to see one complete
integration across the ten runtime modules.

The training arena does not claim to include navmesh pathfinding, full
third-person locomotion and animation, artist-created 3D models, robust save
migration, or production-ready UI. Those are integration points for buyers.

## Troubleshooting

* Scripts or classes duplicate: remove older standalone `com.hpr.*` UPM
  installations before importing the Suite.
* Demo scene does not compile: ensure the complete archive was imported
  under the single `Assets/HPRGameplaySuite` root, not individual files.
* Disk slot cannot be loaded: press **Save disk slot** once first, and inspect
  the status text. JSON written by other applications or older schemas is
  intentionally rejected.
* An ability is on cooldown: wait for the remaining seconds displayed on
  the ability HUD, then retry.
* A gate is locked: collect the amber Training Key first. E uses proximity,
  not a camera raycast; nearest active interactable within range is selected.


## URP/HDRP material setup

If the imported training arena is magenta in an existing URP/HDRP project,
use **Tools > HPR > Gameplay Suite > Adapt Demo Materials to Current Render
Pipeline**. The tool requires your render pipeline shader to be installed
and active; it converts only included demo materials. It does not switch
your project renderer, install registry packages or change other scene
assets. Built-in works without running this tool.


## Experienced-developer integration entry

Open **Tools > HPR > Gameplay Suite > Integration Guide** for an optional
read-only package check, current editor and render pipeline details, direct
links to actual sample data and documentation, and safe scene navigation.
The window never changes project-wide input, render or package settings.
Missing files are reported without auto-installing anything. The panel is
not a full test of your existing game; check its Console and PlayMode yourself.


## Remap demo controls

Select the HPR Playground controller in the Hierarchy. The demo key fields
and interaction radius are editable in the Inspector. The library itself
does not depend on a specific player controller; for an existing game's
input actions implement `IHprSuiteInputSource` and inject it through
`BindInputSource`. No global input settings are changed on import.


## Safe upgrades

The sample scene, scripts and data assets have stable Unity IDs between
package builds. Importing an update still replaces the vendor-owned sample
path, so keep customized game content in your own project folders and make
your own ScriptableObject copies or derived prefabs. Keep normal project
version-control history before upgrading; no automatic user-data migration
or destructive scene rebuild runs on import.
