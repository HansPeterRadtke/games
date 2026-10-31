# HPR Gameplay Systems Suite — integrated release candidate

This single original Unity product *replaces the nine separately proposed HPR
storefront submissions* declined by Unity in October 2026. The former modules
are collected under one `Assets/HPRGameplaySuite/` root. This is NOT a claim
of Unity reviewer approval, publisher-account access or public availability.

## Verified functional intent

One playable, newly authored scene combines actual code across modules:

- HPR Weapon Runtime fires with magazine/cooldown/reload state.
- HPR Enemy Runtime takes damage, transitions to death and implements a timed attack.
- HPR Event Bus publishes the attack as a typed damage event.
- HPR Stats subscribes and applies that damage to the player's health.
- HPR Inventory receives a medkit when the enemy is defeated and consumes it to heal.
- HPR Save stores and restores a memory-only checkpoint using its save payloads.
- HPR Composition, Abilities, Interaction and World remain included as original
  independent modules and can be integrated into the host game. The new scene
  does **not** claim to demonstrate or implement their full features.

The scene is `Demo/GameplaySuiteShowcase.unity` and provides Play-mode
buttons for firing, reloading, enemy attack, healing, saving, restoring and reset.
The geometry is original Unity primitives with simple standard materials. The
scene intentionally does not claim full NavMesh movement, mature FPS controls,
realistic animation, advanced AI, disk-save slots or commercial art quality.
Inventory and enemy health are restored from a memory-only checkpoint; weapon
ammunition/cooldown are not checkpointed. Data remains local to the Unity process.

Each original module retains its unmodified runtime sources and license.
The rejected standalone modules' redundant Editor/Demo scenes and their NUnit
`Tests` assemblies are deliberately **not** included in the buyer archive.
The single new integrated showcase supersedes those separate demos. All
original source tests remain in the repository and pass independently. The single-root export
contains no externally purchased art, audio or generated marketplace media.

## Usage and validation

The source-of-truth build helper is
`unity/tools/release/gameplay_suite/build_gameplay_suite.py` in the Games
repository. It runs an isolated Unity 6000.4 Editor to create the original
scene and export a real `.unitypackage` outside Git. The export only succeeds
if Unity creates the scene and file; a distinct multi-module compilation and
EditMode suite runs in an isolated project. Save output manifests and test
reports with the private candidate, not in public Git.

The exporter does **not** sign into the vendor portal, submit/review old
products, rename an account, create a marketplace draft, accept agreements,
or contact customers. Publishing requires an independent cleanroom import,
a full buyer-facing QA pass, verified content/AI-use marketing disclosures,
current account access and reviewer acceptance. Unity's October 2026 policy
forbids evading rejection by submitting identical old content in a new draft.
This suite must pass differentiation review based on the genuinely new integration
and end-user value before a *single* revised submission is contemplated.

## AI use and customer-facing disclosures

AI-assisted coding tools contributed to some original HPR module implementation,
this integration scene, tests and documentation. This must be stated plainly in
the Unity Publisher Portal's dedicated AI Description field, including what
was improved and verified after AI assistance. No model or external AI service
is required to use the published runtime. The buyer-facing title should
accurately advertise *modular components plus one integrated demonstration*;
it must not advertise autonomous generative enemy AI or a complete playable FPS.

Suggested accurate product title: **HPR Gameplay Systems Suite — Combat,
Inventory, Events, Enemy State and Saves**. Include requirements for Unity
6000.4 or newer, covered modules, truthful technical limitations, and a
single-root installation procedure. Prepare genuine Unity Editor screenshots
from the verified imported demo, not synthetic promotional screenshots.

**Dependency-free cleanroom compilation:** No external Unity Registry GUI
package is required by the buyer archive. The former Abilities demo scripts
that referenced `UnityEngine.UI.Text` are excluded, and the new integrated
showcase uses the Unity Editor's built-in IMGUI. Customers can import into a
new Unity 6000.4 project without manually installing a package first. The
source-of-truth cleanroom test intentionally imports into a fresh project
without adding a UI dependency.
