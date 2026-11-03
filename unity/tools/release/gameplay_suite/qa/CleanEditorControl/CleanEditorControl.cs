// Private no-product control. Never included in the buyer archive.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace PrivateEditorControl
{
    [InitializeOnLoad]
    public static class CleanEditorControl
    {
        [Serializable] private sealed class Observation
        {
            public string editorVersion;
            public int observedEditorUpdates;
            public double observedSeconds;
            public int productAssemblyCount;
            public int assetScriptCount;
            public string graphicsDevice;
            public string graphicsDeviceName;
            public bool nativeUpdateProbeCompleted;
            public int completedPlayCycles;
            public bool domainReloadDisabled;
            public float editSecondsBeforePlay;
        }
        private const string PlayState = "PrivateEditorControl.PlayCycles";
        private static bool playSubscribed;
        static CleanEditorControl()
        {
            if (SessionState.GetInt(PlayState, 0) != 0) SubscribePlay();
        }
        private static void SubscribePlay()
        {
            if (playSubscribed) return;
            playSubscribed = true;
            EditorApplication.update += ObservePlay;
        }
        public static void RunPlayCycles()
        {
            output = Environment.GetEnvironmentVariable("UNITY_CLEAN_CONTROL_OUTPUT");
            if (!Directory.Exists(output) || File.Exists(Path.Combine(output, "native-observation.json")) ||
                EditorApplication.isPlayingOrWillChangePlaymode || SessionState.GetInt(PlayState, 0) != 0)
                throw new InvalidOperationException("Expected unused, idle private Play control");
            SessionState.SetString(PlayState + "output", output);
            SessionState.SetFloat(PlayState + "started", (float)EditorApplication.timeSinceStartup);
            SessionState.SetInt(PlayState + "cycles", 0);
            SessionState.SetInt(PlayState + "updates", 0);
            SessionState.SetBool(PlayState + "entered", false);
            bool settle = Environment.GetEnvironmentVariable("UNITY_CLEAN_CONTROL_SETTLE") == "1";
            SessionState.SetFloat(PlayState + "editSeconds", 0);
            SessionState.SetInt(PlayState, settle ? 3 : 1);
            SubscribePlay();
            if (!settle) EditorApplication.isPlaying = true;
        }
        private static void ObservePlay()
        {
            int phase = SessionState.GetInt(PlayState, 0);
            int count = SessionState.GetInt(PlayState + "updates", 0) + 1;
            SessionState.SetInt(PlayState + "updates", count);
            if (phase == 3)
            {
                double elapsed = EditorApplication.timeSinceStartup - SessionState.GetFloat(PlayState + "started", 0);
                if (elapsed < 20 || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
                SessionState.SetFloat(PlayState + "editSeconds", (float)elapsed);
                SessionState.SetInt(PlayState, 1);
                EditorApplication.isPlaying = true;
                return;
            }
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying) return;
                if (!SessionState.GetBool(PlayState + "entered", false))
                {
                    SessionState.SetBool(PlayState + "entered", true);
                    SessionState.SetFloat(PlayState + "playStarted", (float)EditorApplication.timeSinceStartup);
                }
                if (EditorApplication.timeSinceStartup - SessionState.GetFloat(PlayState + "playStarted", 0) < 10) return;
                SessionState.SetInt(PlayState + "cycles", SessionState.GetInt(PlayState + "cycles", 0) + 1);
                SessionState.SetInt(PlayState, 2);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 2 && !EditorApplication.isPlayingOrWillChangePlaymode &&
                !EditorApplication.isCompiling && !EditorApplication.isUpdating)
            {
                if (SessionState.GetInt(PlayState + "cycles", 0) < 2)
                {
                    SessionState.SetBool(PlayState + "entered", false);
                    SessionState.SetInt(PlayState, 1);
                    EditorApplication.isPlaying = true;
                    return;
                }
                var data = new Observation
                {
                    editorVersion = Application.unityVersion,
                    observedEditorUpdates = count,
                    observedSeconds = EditorApplication.timeSinceStartup - SessionState.GetFloat(PlayState + "started", 0),
                    productAssemblyCount = AppDomain.CurrentDomain.GetAssemblies().Count(
                        assembly => assembly.GetName().Name.StartsWith("HPR", StringComparison.OrdinalIgnoreCase)),
                    assetScriptCount = Directory.GetFiles(Application.dataPath, "*.cs", SearchOption.AllDirectories).Length,
                    graphicsDevice = SystemInfo.graphicsDeviceType.ToString(),
                    graphicsDeviceName = SystemInfo.graphicsDeviceName,
                    completedPlayCycles = SessionState.GetInt(PlayState + "cycles", 0),
                    editSecondsBeforePlay = SessionState.GetFloat(PlayState + "editSeconds", 0),
                    domainReloadDisabled = EditorSettings.enterPlayModeOptionsEnabled &&
                        (EditorSettings.enterPlayModeOptions & EnterPlayModeOptions.DisableDomainReload) != 0,
                    nativeUpdateProbeCompleted = true
                };
                string root = SessionState.GetString(PlayState + "output", "");
                File.WriteAllText(Path.Combine(root, "native-observation.json"), JsonUtility.ToJson(data, true));
                SessionState.SetInt(PlayState, 0);
                EditorApplication.update -= ObservePlay;
                playSubscribed = false;
                EditorApplication.Exit(data.productAssemblyCount == 0 && data.assetScriptCount == 1 ? 0 : 4);
            }
        }
        private static double started;
        private static int updates;
        private static string output;
        public static void Run()
        {
            output = Environment.GetEnvironmentVariable("UNITY_CLEAN_CONTROL_OUTPUT");
            if (!Directory.Exists(output) || File.Exists(Path.Combine(output, "native-observation.json")))
                throw new InvalidOperationException("Expected unused private control output");
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Startup control must stay in Edit mode");
            started = EditorApplication.timeSinceStartup;
            updates = 0;
            EditorApplication.update += Observe;
        }
        private static void Observe()
        {
            updates++;
            double elapsed = EditorApplication.timeSinceStartup - started;
            if (elapsed < 20 || updates < 10) return;
            EditorApplication.update -= Observe;
            var data = new Observation
            {
                editorVersion = Application.unityVersion,
                observedEditorUpdates = updates,
                observedSeconds = elapsed,
                productAssemblyCount = AppDomain.CurrentDomain.GetAssemblies().Count(
                    assembly => assembly.GetName().Name.StartsWith("HPR", StringComparison.OrdinalIgnoreCase)),
                assetScriptCount = Directory.GetFiles(Application.dataPath, "*.cs", SearchOption.AllDirectories).Length,
                graphicsDevice = SystemInfo.graphicsDeviceType.ToString(),
                graphicsDeviceName = SystemInfo.graphicsDeviceName,
                nativeUpdateProbeCompleted = true
            };
            File.WriteAllText(Path.Combine(output, "native-observation.json"), JsonUtility.ToJson(data, true));
            EditorApplication.Exit(data.productAssemblyCount == 0 && data.assetScriptCount == 1 ? 0 : 4);
        }
    }
}
#endif
