using UnityEngine;

namespace HPR
{
    public interface IInputSource
    {
        bool GetKey(KeyCode key);
        bool GetKeyDown(KeyCode key);
        bool GetMouseButton(int button);
        bool GetMouseButtonDown(int button);
        float GetAxisRaw(string axisName);
        Vector2 MouseScrollDelta { get; }
        Vector3 MousePosition { get; }
    }

    public interface IInputBindingsSource
    {
        GameOptionsData CurrentOptions { get; }
    }

    public interface IOptionsController
    {
        void ApplyOptions(GameOptionsData updatedOptions);
        void RebindAction(GameAction action, KeyCode key);
    }
}
