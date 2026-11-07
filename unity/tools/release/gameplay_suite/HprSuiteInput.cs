using System;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using System.Collections.Generic;
using UnityEngine.InputSystem;
#endif

namespace HPR.GameplaySuite
{
    // Runtime-only interface: existing games can supply their own input source.
    public interface IHprSuiteInputSource
    {
        bool IsPressed(KeyCode key);
        bool WasPressed(KeyCode key);
        bool TryGetPointer(out Vector2 screenPosition);
    }

    public sealed class HprSuiteUnityInputSource : IHprSuiteInputSource
    {
        public static readonly HprSuiteUnityInputSource Instance = new HprSuiteUnityInputSource();
#if ENABLE_INPUT_SYSTEM
        private static readonly Dictionary<KeyCode, Key> Cached = new();

        private static Key Map(KeyCode code)
        {
            if (Cached.TryGetValue(code, out Key key)) return key;
            // Undefined serialized KeyCodes stringify as integers; Enum.TryParse
            // would otherwise alias a different key or produce an invalid index.
            if (!Enum.IsDefined(typeof(KeyCode), code)) return Key.None;
            // Legacy KeyCode names do not map one-to-one onto the new
            // Input System enum. Handle its common mismatches explicitly.
            // Unsupported joystick/mouse-only KeyCodes remain Key.None
            // rather than accidentally activating another action.
            switch (code)
            {
                case KeyCode.LeftControl: key = Key.LeftCtrl; break;
                case KeyCode.RightControl: key = Key.RightCtrl; break;
                case KeyCode.Return: key = Key.Enter; break;
                case KeyCode.KeypadEnter: key = Key.NumpadEnter; break;
                case KeyCode.Keypad0: key = Key.Numpad0; break;
                case KeyCode.Keypad1: key = Key.Numpad1; break;
                case KeyCode.Keypad2: key = Key.Numpad2; break;
                case KeyCode.Keypad3: key = Key.Numpad3; break;
                case KeyCode.Keypad4: key = Key.Numpad4; break;
                case KeyCode.Keypad5: key = Key.Numpad5; break;
                case KeyCode.Keypad6: key = Key.Numpad6; break;
                case KeyCode.Keypad7: key = Key.Numpad7; break;
                case KeyCode.Keypad8: key = Key.Numpad8; break;
                case KeyCode.Keypad9: key = Key.Numpad9; break;
                default:
                    string name = code.ToString();
                    if (name.StartsWith("Alpha", StringComparison.Ordinal))
                        name = "Digit" + name.Substring(5);
                    else if (name.StartsWith("Keypad", StringComparison.Ordinal))
                        name = "Numpad" + name.Substring(6);
                    if (!Enum.TryParse(name, true, out key)) key = Key.None;
                    break;
            }
            Cached.Add(code, key);
            return key;
        }

        public bool IsPressed(KeyCode code)
        {
            var keyboard = Keyboard.current;
            Key key = Map(code);
            return keyboard != null && key != Key.None && keyboard[key] != null &&
                   keyboard[key].isPressed;
        }

        public bool WasPressed(KeyCode code)
        {
            var keyboard = Keyboard.current;
            Key key = Map(code);
            return keyboard != null && key != Key.None && keyboard[key] != null &&
                   keyboard[key].wasPressedThisFrame;
        }

        public bool TryGetPointer(out Vector2 position)
        {
            var mouse = Mouse.current;
            position = mouse != null ? mouse.position.ReadValue() : Vector2.zero;
            return mouse != null;
        }
#elif ENABLE_LEGACY_INPUT_MANAGER
        public bool IsPressed(KeyCode code) => Input.GetKey(code);
        public bool WasPressed(KeyCode code) => Input.GetKeyDown(code);
        public bool TryGetPointer(out Vector2 position)
        {
            position = Input.mousePosition;
            return true;
        }
#else
        public bool IsPressed(KeyCode code) => false;
        public bool WasPressed(KeyCode code) => false;
        public bool TryGetPointer(out Vector2 position)
        {
            position = Vector2.zero;
            return false;
        }
#endif
    }
}
