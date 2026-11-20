// Disposable QA only. A real MonoBehaviour.Update reads Unity Input System
// key transitions on the game update tick, unlike EditorApplication.update.
#if ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using HPR.GameplaySuite;

public sealed class HprSuiteInputGameplayProbe : MonoBehaviour
{
    private Keyboard keyboard;
    private InputSettings.BackgroundBehavior previousBackgroundBehavior;
    private InputSettings.EditorInputBehaviorInPlayMode previousEditorInputBehavior;
    private InputSettings.UpdateMode previousUpdateMode;
    private int stage;
    private int ticks;

    private void Awake()
    {
        // Only the disposable QA project ignores the unfocused batch Editor.
        previousBackgroundBehavior = InputSystem.settings.backgroundBehavior;
        previousEditorInputBehavior = InputSystem.settings.editorInputBehaviorInPlayMode;
        previousUpdateMode = InputSystem.settings.updateMode;
        Debug.Log("HPR_PRIVATE_NEW_INPUT_PREVIOUS update=" + previousUpdateMode +
                  " editor=" + previousEditorInputBehavior + " focus=" + Application.isFocused);
        // Headless Editor lacks a focused Game View. Route the disposable
        // virtual keyboard to the game rather than to the Editor UI.
        InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
        InputSystem.settings.editorInputBehaviorInPlayMode =
            InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
        InputSystem.settings.updateMode = InputSettings.UpdateMode.ProcessEventsInDynamicUpdate;
        keyboard = InputSystem.AddDevice<Keyboard>();
        if (keyboard == null)
            ReportFailure("Cannot create a virtual test keyboard");
    }

    private void Update()
    {
        if (stage == 99 || keyboard == null) return;
        if (++ticks > 300)
        {
            ReportFailure("Input test did not complete within 300 game frames");
            return;
        }
        try
        {
            HprSuiteUnityInputSource source = HprSuiteUnityInputSource.Instance;
            if (stage == 0)
            {
                // Events queued from game Update are processed at the
                // beginning of the following input/game update tick.
                InputSystem.QueueStateEvent(keyboard,
                    new KeyboardState(Key.W, Key.LeftArrow, Key.Digit1, Key.LeftCtrl, Key.Numpad1));
                stage = 1;
                return;
            }
            if (stage == 1)
            {
                bool pressed = source.IsPressed(KeyCode.W) &&
                    source.IsPressed(KeyCode.LeftArrow) &&
                    source.IsPressed(KeyCode.Alpha1) &&
                    source.IsPressed(KeyCode.LeftControl) &&
                    source.IsPressed(KeyCode.Keypad1);
                bool justPressed = source.WasPressed(KeyCode.W);
                bool engineJustPressed = keyboard.wKey.wasPressedThisFrame;
                Debug.Log("HPR_GAME_INPUT_FRAME press=" + pressed +
                    " justPressed=" + justPressed + " native=" + engineJustPressed +
                    " deviceUpdated=" + keyboard.wasUpdatedThisFrame);
                if (!pressed || !justPressed || !engineJustPressed)
                    throw new InvalidOperationException(
                        "Input System key press was not visible during a real game Update.");
                InputSystem.QueueStateEvent(keyboard, new KeyboardState());
                stage = 2;
                return;
            }
            if (stage == 2)
            {
                if (source.IsPressed(KeyCode.W))
                    throw new InvalidOperationException("Released key remains pressed in game Update.");
                if (source.WasPressed(KeyCode.W))
                    throw new InvalidOperationException("Released key incorrectly reports a new press.");
                stage = 99;
                File.WriteAllText(Receipt(),
                    "unity=" + Application.unityVersion + "\n" +
                    "new_input_adapter_real_game_update=PASS\n" +
                    "key_press_and_frame_transition=PASS\n" +
                    "keyboard_modifiers_and_numpad=PASS\n" +
                    "key_release=PASS\n");
                Debug.Log("HPR_NEW_INPUT_GAME_UPDATE_PASS");
                if (!Application.isEditor) Application.Quit(0);
            }
        }
        catch (Exception failure)
        {
            ReportFailure(failure.ToString());
        }
    }

    private void ReportFailure(string reason)
    {
        stage = 99;
        File.WriteAllText(Receipt() + ".FAILED", reason);
        Debug.LogError("HPR_NEW_INPUT_GAME_UPDATE_FAILED: " + reason);
        if (!Application.isEditor) Application.Quit(1);
    }

    private static string Receipt()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_NEW_INPUT_GAME_UPDATE_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt))
            throw new InvalidOperationException("New Input System test has no receipt path.");
        return receipt;
    }

    private void OnDestroy()
    {
        InputSystem.settings.backgroundBehavior = previousBackgroundBehavior;
        InputSystem.settings.editorInputBehaviorInPlayMode = previousEditorInputBehavior;
        InputSystem.settings.updateMode = previousUpdateMode;
        if (keyboard != null)
        {
            InputSystem.RemoveDevice(keyboard);
            keyboard = null;
        }
    }
}
#endif
