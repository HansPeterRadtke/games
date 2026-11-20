# Unity 6.6 URP 17.6 + Input System 1.20.1 — real combined Play Mode QA

November 1, 2026, Nitro. This record concerns the frozen HPR v14 imported
buyer archive in a **private cloned Unity 6000.6.7f1** project with actual
Universal Render Pipeline 17.6.0 and `com.unity.inputsystem` 1.20.1.
`ProjectSettings/ProjectSettings.asset` reported `activeInputHandler: 1`,
meaning **new Input System only**. These are actual local Unity process
observations, not package metadata guesses.

Do **not** call this a clean full release-matrix pass. The independent
negative tests and the Editor search index exception remain part of the
evidence. No customer projects, Asset Store listings, actual buyer scenes,
or other agent's dirty Unity source were modified.

## Frozen independent assets and acceptance scope

Original project: private existing URP/new-input v14 imported game, copied into
`/data/tmp/hpr-caltask33-20261101-0903/combined-urp-new-input-v14`.
A SHA-256 baseline captured the original imported demo scene plus
GraphicsSettings, ProjectSettings, EditorSettings and Packages/manifest.
The candidate invokes a **real Unity Editor Play Mode** scene containing
the actual imported arena and a disposable virtual keyboard probe in
`MonoBehaviour.Update`. The probe checks W, left-arrow, left-control,
top-row one, keypad one; pressed/just-pressed transitions and key release.
The orchestrating Editor test additionally requires an active
`UniversalRenderPipelineAsset` and original scene camera.

Private QA source:
`unity/tools/release/gameplay_suite/qa/HprCombinedUrpInputPlaymodeValidator.cs`
and `HprSuiteInputGameplayProbe.cs`. The latter already existed in the
project's historical QA. This test must install **one and only one** copy
of the probe or Unity rejects the duplicated class.

## Actual failures

First real Unity compile: the copied URP project already had one
`HprSuiteInputGameplayProbe`; we mistakenly added a second in a new folder.
Unity compilation failed with `CS0101` and `CS0111`. This was a **QA
setup defect**, not an imported HPR source error. The failed Unity log is
`combined-urp-new-input-editor-20261101.unity.log`, preserved. Only the
redundant private QA script was removed; the original was left unchanged.

Second real Unity Play mode: with exactly one probe Unity compiled and entered
Play mode, but the synthetic keyboard frame showed all states FALSE:
`pressed=False, justPressed=False, native=False, deviceUpdated=False`.
Actual Editor process failed with status three and preserved the
`.FAILED` input receipt and a separate
`combined-urp-new-input-fixed-20261101.unity.log`.

This was **not** sufficient to conclude the HPR new-input adapter is broken
in a focused player. The Unity Editor was running headlessly with no
focused Game View. Unity's official Input System documentation explains
that by default Editor Play mode routes keyboard/pointer devices to the
Editor rather than the game when Game View lacks focus.

Unity official primary references:
- https://github.com/Unity-Technologies/InputSystem/blob/develop/Packages/com.unity.inputsystem/Documentation~/platform-specific-settings.md
- https://github.com/Unity-Technologies/InputSystem/blob/develop/Packages/com.unity.inputsystem/Documentation~/timing-select-mode.md

## Actual positive result — PASS with explicit private test focus control

A **third independent disposable project copy** retained the single probe
and temporarily configured the private test's
`InputSystem.settings.editorInputBehaviorInPlayMode` to
`AllDeviceInputAlwaysGoesToGameView`, with
`ProcessEventsInDynamicUpdate` as its update mode and
`IgnoreFocus` background behavior. The private MonoBehaviour restores
its previously observed settings during `OnDestroy`; it does not write
the customer's ProjectSettings.

Its actual diagnostic revealed the original dynamic update mode was
**already** `ProcessEventsInDynamicUpdate`, while Play Mode behavior had
been `PointersAndKeyboardsRespectGameViewFocus` and
`Application.isFocused` was FALSE. This supports focus routing as the
change responsible for the second failure, though only the combined
private configuration was experimentally changed.

The actual Unity 6.6 Editor process exited with status zero, with the
following native log observations:

- `HPR_GAME_INPUT_FRAME press=True justPressed=True native=True deviceUpdated=True`
- `HPR_NEW_INPUT_GAME_UPDATE_PASS`
- `HPR_COMBINED_URP_NEW_INPUT_ACCEPTANCE_PASS`

Actual receipt files:
`combined-urp-focused-editor-20261101.txt` and
`combined-urp-focused-game-frame-20261101.txt`. Checks include genuine
URP active, original imported arena camera, actual new-input-only
keyboard down/up/modifiers, and an Editor Play Mode run.

Independent post-test SHA-256 comparison found **zero changes across five
protected original buyer scene/project files**:
`combined-urp-focused-asset-integrity-20261101.json`. The real Editor
did emit the known `UnityEditor.Search.SearchDatabase`
`ArgumentOutOfRangeException` during startup indexing. Treat it as an
unresolved, independently unisolated Editor diagnostic, not a HPR runtime
test failure.

## Commercial limitations

Only one Unity Editor six point six build and one combined URP/new-input
configuration were exercised. This is **not** automated screenshot/UI
legibility acceptance, not full new/old Input System across all pipelines,
not HDRP or Unity six point four combined acceptance, not arbitrary
real-customer keyboard hardware, and not measured buyer task time. HPR has
not been submitted or approved. Retain commercial **NO-GO** pending direct
buyer-use differentiation, complete isolated release QA, and signoff.
