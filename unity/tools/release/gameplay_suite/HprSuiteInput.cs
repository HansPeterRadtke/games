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
            string name = code.ToString();
            if (name.StartsWith("Alpha", StringComparison.Ordinal))
                name = "Digit" + name.Substring(5);
            else if (code == KeyCode.Return) name = "Enter";
            if (!Enum.TryParse(name, true, out key)) key = Key.None;
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
