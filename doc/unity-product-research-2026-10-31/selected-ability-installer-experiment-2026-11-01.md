# Selected-object HPR ability integration — reversible Editor prototype

Date: November 1, 2026, Nitro. **Experimental private QA branch only.**
This is not included in any approved or published asset, nor in the
new frozen internal release archive. It was developed because the original
HPR guide could copy ScriptableObject sample assets but did not offer a
working, validated path to attach one chosen ability to an existing game.

## Customer problem and scope

A Unity developer already has their own controller, a scene, prefabs and
project settings. They want to add one healing ability, using an already
customer-owned ability and resource provider, without replacing the
controller, changing input handling or silently overwriting project files.

The prototype lives in
`unity/tools/release/gameplay_suite/qa/HprSelectedAbilityInstaller.cs`.
It provides a deliberate Editor menu action under
`Tools > HPR > Gameplay Suite` and a UI Toolkit window with a selected
GameObject field, customer ability ObjectField, resource provider field,
a read-only status/compatibility preview and one explicit attach button.
It uses public APIs only and does not run automatically on import, save a
scene, change project input or graphics settings, copy assets or call a
provider API.

The `ValidateSelection` method rejects Play mode, prefab assets,
non-active-scene objects, a pre-existing HPR AbilityRunner, missing or
foreign resource provider, vendor-owned AbilityData, invalid ability
identifiers/costs/cooldowns and vendor-owned effect dependencies. Only
`AttachExplicitly` has a mutation path, invoked by a user action.
It uses Unity Undo.AddComponent, SerializedObject/SerializedProperty,
Undo.RecordObject, and scene dirty marking, preserving the customer's
source and prefabs. It adds **one optional HPR component**, not a
new controller. The user must manually save the scene to persist it.

## Real Unity acceptance

Test-first Python contract checks failed before the new feature and
validator existed and passed after they were implemented. The real
Unity test file is
`unity/tools/release/gameplay_suite/qa/HprSelectedAbilityInstallerValidator.cs`.

The private test cloned a real Unity six point six customer project with
a separate custom player, prefab, original scene, custom serialization
settings and an independently copied healing AbilityData/effect. A new
disposable **scene copy** was created; the original scene stayed untouched.
The test first called read-only validation with missing resource provider
and with a vendor-owned ability: both were rejected without adding
components. It then added a **private QA-only adapter** implementing
`IAbilityResourcePool` to the new scene, and explicitly invoked the
install method.

The actual Unity 6000.6.7f1 Editor process reported **exit zero** and
wrote `installer-customer-editor-receipt.txt` with all eight checks
passing:

- Preflight rejected unsafe / missing dependencies without writes.
- A single optional HPR AbilityRunner was attached to the selected object.
- Unity Undo removed only the new runner, preserving customer controller
  and independent adapter.
- Unity Redo restored the runner and configured ability.
- The chosen customer-owned ability, inspector unlock state and resource
  reference survived saving/reopening the **new scene**.
- The original controller, prefab, original scene, serialized settings
  and customer-owned ability assets retained exact bytes and Unity GUIDs.
- A real UI Toolkit EditorWindow exposed three fields, two buttons and
  an actionable validation/status control.
- Installer itself never auto-saved the scene or wrote project settings.

Independent post-run SHA-256 verification measured **sixty-one** existing
protected customer Assets/ProjectSettings/Packages files and found **no
modified or removed original**. The only four new files were the explicit
new demonstration scene + metadata and the two Unity-generated metadata
files belonging to the newly introduced private Editor QA scripts. An
initial too-narrow allowlist incorrectly flagged those two expected QA
metadata files; the original result was retained, and a second read-only
audit with the complete expected additions passed. See
`installer-buyer-baseline.json`, `installer-buyer-after.json` and
`installer-buyer-after-accepted.json` in the private scratch root.

The UI structure and functionality have been compiled/tested in the actual
Unity Editor, **but a visual screenshot, desktop keyboard navigation,
high-DPI/dark theme layout and independent external-developer task
completion have not been verified**. No paid market demand is implied.

## Commercial and implementation blockers

This implementation still requires the customer to have an
`IAbilityResourcePool` adapter and their own valid independent ability
definitions. It therefore reduces insertion friction for a technically
skilled buyer but is not a zero-code feature. It has not been benchmarked
against Ability System Kit or Game Creator 2, nor tested across varied
customer prefabs, nested scenes, multiple HPR modules, Unity 6.4 and
physical input devices. It is separate from the currently built buyer
archive and has no actual package-versioned migration contract.

The current ten-module suite remains **commercial NO-GO** pending genuine
buyer differentiation and a new reviewed release that includes any
approved changes. Keep this prototype in the independent QA branch until
a real product owner explicitly reconciles it with the other agent's
working code. Preserve the original customer's source, scene and GUIDs.
