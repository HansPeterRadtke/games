// Private Linux Player regression for the showcase's injected input and normal Update loop.
#if UNITY_STANDALONE_LINUX && !UNITY_EDITOR
using System;
using System.Collections;
using HPR.GameplaySuite;
using UnityEngine;
using UnityEngine.Rendering;

public sealed class PointerAimPlayerProbe : MonoBehaviour, IHprSuiteInputSource
{
    private const string CameraDiagnostic = "Screen position out of view frustum";
    private HprGameplaySuitePlayground game;
    private string mode;
    private Vector2 supplied;
    private Vector2 lastPointer;
    private bool lastAvailable;
    private int reads;
    private int warnings;
    private int failures;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Install()
    {
        new GameObject(nameof(PointerAimPlayerProbe)).AddComponent<PointerAimPlayerProbe>();
    }

    private IEnumerator Start()
    {
        Application.runInBackground = true;
        game = UnityEngine.Object.FindAnyObjectByType<HprGameplaySuitePlayground>();
        if (!game || !game.enabled || !game.ServicesAvailable)
        {
            Debug.LogError("HPR_POINTER_TEST_INVALID: showcase did not initialize");
            Application.Quit(2);
            yield break;
        }

        game.SetAutomaticEnemy(false);
        game.BindInputSource(this);
        Application.logMessageReceived += CountCameraDiagnostic;
        bool graphics = SystemInfo.graphicsDeviceType != GraphicsDeviceType.Null;
        bool desktop = Environment.GetEnvironmentVariable("HPR_POINTER_DESKTOP") == "1";
        foreach (string stage in new[] { "native", "disabled", "absent", "nan-x", "infinite-y",
                     "finite", "left", "right", "mouse-left", "mouse-right" })
        {
            bool mouse = stage == "mouse-left" || stage == "mouse-right";
            bool target = mouse || stage == "left" || stage == "right";
            if ((target && !graphics) || (mouse && !desktop)) continue;
            mode = stage;
            reads = warnings = 0;
            lastAvailable = false;
            lastPointer = Vector2.zero;
            game.enabled = stage != "disabled";
            var player = game.CaptureSnapshot().Player;
            Quaternion before = player.rotation.ToQuaternion();
            Vector3 aimDirection = stage == "left" || stage == "mouse-left" ? Vector3.left : Vector3.right;
            if (target)
                supplied = Camera.main.WorldToScreenPoint(player.position.ToVector3() + aimDirection * 2);
            else if (stage == "nan-x") supplied = new Vector2(float.NaN, 100);
            else if (stage == "infinite-y") supplied = new Vector2(100, float.PositiveInfinity);
            else supplied = new Vector2(100, 100);

            if (mouse)
            {
                // X11 window coordinates start at the top left. Unity screen coordinates start at the bottom left.
                int x = Mathf.RoundToInt(supplied.x);
                int y = Screen.height - 1 - Mathf.RoundToInt(supplied.y);
                Debug.Log($"HPR_POINTER_MOVE {stage} {x} {y}");
                float deadline = Time.realtimeSinceStartup + 10f;
                while ((!lastAvailable || Vector2.Distance(lastPointer, supplied) > 3f) &&
                       Time.realtimeSinceStartup < deadline) yield return null;
            }
            for (int frame = 0; frame < 4; ++frame) yield return null;
            Quaternion after = game.CaptureSnapshot().Player.rotation.ToQuaternion();
            bool stayed = Quaternion.Angle(before, after) < 0.05f;
            bool aimed = Vector3.Dot(after * Vector3.forward, aimDirection) > .999f;
            bool ok = warnings == 0 && (stage == "disabled" ? reads == 0 : reads > 0);
            if (stage == "absent" || stage == "nan-x" || stage == "infinite-y") ok &= stayed;
            if (target) ok &= aimed;
            if (mouse) ok &= lastAvailable && Vector2.Distance(lastPointer, supplied) <= 3f;
            if (!ok) failures++;
            Debug.Log($"HPR_POINTER_CASE stage={stage} graphics={SystemInfo.graphicsDeviceType} " +
                $"reads={reads} available={lastAvailable} pointer=({lastPointer.x:R},{lastPointer.y:R}) " +
                $"warnings={warnings} stayed={stayed} aimed={aimed} pass={ok}");
        }

        if (graphics && desktop)
        {
            mode = "native";
            game.SetAutomaticEnemy(true);
            foreach (string action in new[] { "cancel", "pause", "resume" })
            {
                Debug.Log($"HPR_HUD_ACTION {action}");
                float deadline = Time.realtimeSinceStartup + 10f;
                while (!MouseReleased() && Time.realtimeSinceStartup < deadline) yield return null;
                bool released = MouseReleased();
                for (int frame = 0; frame < 4; ++frame) yield return null;
                bool ok = released && game.AutomaticEnemy == (action != "pause");
                if (!ok) failures++;
                Debug.Log($"HPR_HUD_CASE {action} released={released} live={game.AutomaticEnemy} pass={ok}");
            }
        }

        mode = "absent";
        Debug.Log($"HPR_POINTER_DONE failures={failures}");
        Application.Quit(failures == 0 ? 0 : 1);
    }

    private static bool MouseReleased()
    {
#if ENABLE_INPUT_SYSTEM
        var mouse = UnityEngine.InputSystem.Mouse.current;
        return mouse != null && mouse.leftButton.wasReleasedThisFrame;
#elif ENABLE_LEGACY_INPUT_MANAGER
        return Input.GetMouseButtonUp(0);
#else
        return false;
#endif
    }

    private void OnDestroy() { Application.logMessageReceived -= CountCameraDiagnostic; }

    private void CountCameraDiagnostic(string message, string stack, LogType type)
    {
        if (message.StartsWith(CameraDiagnostic, StringComparison.Ordinal)) warnings++;
    }

    public bool IsPressed(KeyCode key) => false;
    public bool WasPressed(KeyCode key) => false;

    public bool TryGetPointer(out Vector2 position)
    {
        ++reads;
        position = supplied;
        bool native = mode == "native" || mode == "mouse-left" || mode == "mouse-right";
        lastAvailable = native
            ? HprSuiteUnityInputSource.Instance.TryGetPointer(out position) : mode != "absent";
        lastPointer = position;
        return lastAvailable;
    }
}
#endif
