#if UNITY_EDITOR && ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using HPR.GameplaySuite;

public static class InputKeySafetyValidator
{
    [Serializable] private sealed class Observation
    {
        public string name;
        public int legacyCode;
        public bool expected;
        public bool nativeHeld;
        public bool nativeEdge;
        public bool pressed;
        public bool edge;
        public string error = "";
        public bool passed;
    }
    [Serializable] private sealed class Receipt
    {
        public string engineVersion;
        public string numericAliasKey;
        public bool aliasLegacyValueUndefined;
        public bool aliasNewValueDefined;
        public List<Observation> cases = new List<Observation>();
    }
    private static void Case(Receipt receipt, Keyboard keyboard, string name, KeyCode code, Key pressed, bool expected)
    {
        InputSystem.QueueStateEvent(keyboard, new KeyboardState()); InputSystem.Update();
        InputSystem.QueueStateEvent(keyboard, new KeyboardState(pressed)); InputSystem.Update();
        keyboard.MakeCurrent();
        var result = new Observation { name = name, legacyCode = (int)code, expected = expected,
            nativeHeld = keyboard[pressed].isPressed, nativeEdge = keyboard[pressed].wasPressedThisFrame };
        try
        {
            result.pressed = HprSuiteUnityInputSource.Instance.IsPressed(code);
            result.edge = HprSuiteUnityInputSource.Instance.WasPressed(code);
            result.passed = result.nativeHeld && result.nativeEdge && result.pressed == expected && result.edge == expected;
        }
        catch (Exception error) { result.error = error.GetType().Name; }
        receipt.cases.Add(result);
    }
    private static int phase;
    private static int frames;
    private static int exitCode;
    private static double startup;
    public static void Run()
    {
        if (EditorSettings.enterPlayModeOptionsEnabled != true ||
            (EditorSettings.enterPlayModeOptions & EnterPlayModeOptions.DisableDomainReload) == 0)
            throw new InvalidOperationException("Private probe requires explicit domain-reload-off configuration");
        startup = EditorApplication.timeSinceStartup;
        EditorApplication.update += Step;
    }
    private static void Step()
    {
        try
        {
            if (phase == 0)
            {
                if (EditorApplication.timeSinceStartup - startup < 20 || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                phase = 1; EditorApplication.isPlaying = true;
            }
            else if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 30) return;
                exitCode = ExecuteCases(); phase = 2; EditorApplication.isPlaying = false;
            }
            else if (phase == 2 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                EditorApplication.update -= Step; EditorApplication.Exit(exitCode);
            }
        }
        catch (Exception error)
        {
            string root = Environment.GetEnvironmentVariable("HPR_INPUT_KEY_OUTPUT");
            File.WriteAllText(Path.Combine(root, "probe-failure.txt"), error.ToString());
            EditorApplication.update -= Step; EditorApplication.Exit(4);
        }
    }
    private static int ExecuteCases()
    {
        string root = Environment.GetEnvironmentVariable("HPR_INPUT_KEY_OUTPUT");
        if (!Directory.Exists(root) || File.Exists(Path.Combine(root, "native-input-keys.json")))
            throw new InvalidOperationException("Fresh private output required");
        var receipt = new Receipt { engineVersion = Application.unityVersion, numericAliasKey = ((Key)18).ToString(),
            aliasLegacyValueUndefined = !Enum.IsDefined(typeof(KeyCode), 18), aliasNewValueDefined = Enum.IsDefined(typeof(Key), 18) };
        if (!receipt.aliasLegacyValueUndefined || !receipt.aliasNewValueDefined)
            throw new InvalidOperationException("Numeric-alias control is not valid on this installed version");
        var settings = InputSystem.settings;
        var background = settings.backgroundBehavior;
        var editorInput = settings.editorInputBehaviorInPlayMode;
        var updateMode = settings.updateMode;
        Keyboard keyboard = null;
        try
        {
            settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
            settings.updateMode = InputSettings.UpdateMode.ProcessEventsManually;
            keyboard = InputSystem.AddDevice<Keyboard>();
            Case(receipt, keyboard, "letter_a", KeyCode.A, Key.A, true);
            Case(receipt, keyboard, "alpha_1", KeyCode.Alpha1, Key.Digit1, true);
            Case(receipt, keyboard, "left_control", KeyCode.LeftControl, Key.LeftCtrl, true);
            Case(receipt, keyboard, "return", KeyCode.Return, Key.Enter, true);
            Case(receipt, keyboard, "keypad_enter", KeyCode.KeypadEnter, Key.NumpadEnter, true);
            Case(receipt, keyboard, "keypad_0", KeyCode.Keypad0, Key.Numpad0, true);
            Case(receipt, keyboard, "none", KeyCode.None, (Key)18, false);
            Case(receipt, keyboard, "mouse_not_keyboard", KeyCode.Mouse0, (Key)18, false);
            Case(receipt, keyboard, "joystick_not_keyboard", KeyCode.JoystickButton0, (Key)18, false);
            Case(receipt, keyboard, "undefined_numeric_alias", (KeyCode)18, (Key)18, false);
            Case(receipt, keyboard, "undefined_large_value", (KeyCode)50000, (Key)18, false);
            Case(receipt, keyboard, "undefined_negative_value", (KeyCode)(-1), (Key)18, false);
        }
        finally
        {
            if (keyboard != null) InputSystem.RemoveDevice(keyboard);
            settings.backgroundBehavior = background;
            settings.editorInputBehaviorInPlayMode = editorInput;
            settings.updateMode = updateMode;
        }
        File.WriteAllText(Path.Combine(root, "native-input-keys.json"), JsonUtility.ToJson(receipt, true));
        return receipt.cases.TrueForAll(row => row.passed) ? 0 : 3;
    }
}
#endif
