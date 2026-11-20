# HPR Animator Contract Audit

An Editor-only, read-only preflight for Unity Animator Controllers. The audit finds potential broken parameter *contracts* before you spend time debugging a transition, nested state machine, or Blend Tree. It never repairs or modifies project assets.

## Quick start

1. Import the HPR Animator Contract Audit `.unitypackage` into a Unity project. The tool adds only this `Assets/HPRAnimatorContract` folder.
2. Open **Tools > HPR > Animator Contract Audit**.
3. Choose **Scan Animator Controllers (read only)**. The tool inspects editable `.controller` assets inside `Assets/`; it does not change animations, scenes, parameters, or project settings.
4. For a finding, read the rule, parameter name, asset path and state or transition scope. Click **Select Controller** to select and highlight the affected Controller in the Project window. Inspect the named transition or state yourself before changing anything.
5. If you want a record, choose **Export JSON report (choose new file)**. Select a *new* external `.json` filename. The exporter refuses to overwrite an existing report; selecting Cancel writes nothing. The default scan writes no report to disk.
6. Make any intended changes manually in Unity, save your project normally, then run the scan again. Verify animation visually in Play Mode and in a built Player before release.

## Findings and how to interpret them

- **MISSING_PARAMETER / EMPTY_PARAMETER:** a transition, enabled state value, or Blend Tree refers to a parameter that is absent or unnamed. Inspect the referenced state, condition, and Controller's Parameters list. Recreating a name without checking the *type* may still be incorrect.
- **PARAMETER_TYPE_MISMATCH:** a transition condition uses a mode incompatible with the referenced Float, Int, Bool, or Trigger parameter. Review the transition condition and the declared parameter type.
- **STATE_PARAMETER_TYPE_MISMATCH:** an enabled state Speed, Time, Cycle Offset, or Mirror parameter has the wrong declared type. Speed, Time, and Cycle Offset require Float; Mirror requires Bool.
- **BLEND_PARAMETER_TYPE_MISMATCH:** a Blend Tree value or Direct child weight parameter does not use Float. Examine the blend mode and parameter names.
- **DUPLICATE_PARAMETER:** multiple parameter declarations have the same exact name, which makes bindings ambiguous. Resolve this deliberately in your original Controller rather than through automatic renaming.
- **UNREADABLE_CONTROLLER:** Unity could not load a controller identified during the project scan.

**ISSUES_FOUND** means the scanner found contracts to inspect. **NO_ISSUES_IN_CHECKED_CONTRACTS** means none of these specific rules matched; it does *not* guarantee your animations work. **INCOMPLETE** means the audit could not examine everything: for example an unreadable controller or a scan/finding cap.

## What is actually checked

The scanner visits each editable Animator Controller under the `Assets/` directory, including nested state machines, Any State, Entry and state-to-state transitions, active Speed/Time/Mirror/Cycle Offset state parameter bindings, and recursive Blend Trees (including Direct child weight parameters). It checks parameter existence and the types covered above. It limits controller count, state-machine traversal and collected findings; encountering a limit marks the result incomplete rather than returning a false success.

It does **not** check imported `.fbx` subasset Controllers, Animator Override Controller mappings, project code that calls `SetBool`, `SetTrigger` and related APIs, dynamic Controller creation, all custom layer semantics, avatar rigs, whether a motion is visually correct, whether an animation clip exists or blends properly, or every Unity Editor/runtime version. For diagnostic certainty, also inspect the real Animator window, input triggers and animation playback.

## Safety and support boundary

The audit does not create, rename, delete, repair or write Animator assets, change package dependencies, add runtime components, or upload data. The optional user-selected JSON export is the only intentional file write. There is no network service or external account dependency. The tool is compiled as an Editor script and should not be expected to run in a Player build.

Native engineering checks were performed with Unity **6000.6.8f1**, including import into a project using URP and the new Input System only. Additional Editor versions, manual graphical workflows, performance on large third-party projects, and independent buyer acceptance require separate verification. This is an **unpublished internal candidate**, not a commercially approved Asset Store release. License, pricing, marketing screenshots and seller authorization are not provided by this README.
