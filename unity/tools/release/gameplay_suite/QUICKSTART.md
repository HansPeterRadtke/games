# Five-minute buyer walkthrough

This is a **code toolkit**, not a premade game. Start Unity 6000.4 or later,
import the supplied `.unitypackage`, then open:
`Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity`.

Press Play. The blue capsule is the player and the orange capsule is the
training target. Move using W, A, S, D or arrow keys. The cyan cube dispenses
one medkit; the small amber cube dispenses a training key. Stand near a cube
and press E (or press **Interact**) to pick it up. Walk to the amber gate and
press E to open it. The gate demonstrates the real `KeyDoorInteractable`
and inventory key check.

Press F to fire the rifle and R to reload. Cooldowns and ammunition are real
`WeaponRuntimeState` values. Press **Enemy attacks** to simulate an adjacent
opponent's attack; health decreases via a typed `DamageEvent`. The enemy is a
deterministic state machine and does not follow the player.

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

The training arena does not claim to include navmesh pathfinding, aim/LOS
checks, full character physics, artist-created 3D models, robust save
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
