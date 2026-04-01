using UnityEngine;

namespace HPR
{
    public class UnityInputSource : MonoBehaviour, IInputSource
    {
        public bool GetKey(KeyCode key) => Input.GetKey(key);
        public bool GetKeyDown(KeyCode key) => Input.GetKeyDown(key);
        public bool GetMouseButton(int button) => Input.GetMouseButton(button);
        public bool GetMouseButtonDown(int button) => Input.GetMouseButtonDown(button);
        public float GetAxisRaw(string axisName) => Input.GetAxisRaw(axisName);
        public Vector2 MouseScrollDelta => Input.mouseScrollDelta;
        public Vector3 MousePosition => Input.mousePosition;
    }
}
