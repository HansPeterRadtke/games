// Original Unity Editor integration guide; no project mutation on import.
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.UIElements;

namespace HPR.GameplaySuite
{
    /// <summary>
    /// Read-only entry point for experienced programmers integrating HPR code.
    /// It never installs dependencies, rewrites settings or edits foreign assets.
    /// </summary>
    public sealed class HprSuiteIntegrationGuide : EditorWindow
    {
        private const string Root = "Assets/HPRGameplaySuite";
        private const string Styles = Root + "/Editor/Styles/HprSuiteIntegrationGuide.uss";
        private static readonly string[] Modules = {
            "eventbus", "composition", "save", "stats", "inventory",
            "interaction", "abilities", "weapons", "ai", "world"
        };

        private Label status;
        private Label advice;
        private string lastReport = "No layout check performed";

        [MenuItem("Tools/HPR/Gameplay Suite/Integration Guide")]
        public static void OpenGuide()
        {
            HprSuiteIntegrationGuide window = GetWindow<HprSuiteIntegrationGuide>();
            window.titleContent = new GUIContent("HPR Integration");
            window.minSize = new Vector2(410f, 430f);
            window.Show();
        }

        private void OnEnable()
        {
            EditorApplication.projectChanged += RefreshStatus;
        }

        private void OnDisable()
        {
            EditorApplication.projectChanged -= RefreshStatus;
        }

        public void CreateGUI()
        {
            rootVisualElement.Clear();
            StyleSheet style = AssetDatabase.LoadAssetAtPath<StyleSheet>(Styles);
            if (style != null)
                rootVisualElement.styleSheets.Add(style);

            ScrollView scroll = new ScrollView();
            scroll.AddToClassList("hpr-suite-root");
            rootVisualElement.Add(scroll);

            Label heading = new Label("HPR GAMEPLAY SYSTEMS");
            heading.AddToClassList("hpr-suite-title");
            scroll.Add(heading);

            Label intro = new Label(
                "Source-level Unity components. Integrate only the systems your game needs.");
            intro.AddToClassList("hpr-suite-description");
            scroll.Add(intro);

            status = new Label();
            status.AddToClassList("hpr-suite-status");
            scroll.Add(status);

            advice = new Label();
            advice.AddToClassList("hpr-suite-message");
            scroll.Add(advice);

            AddSection(scroll, "First use",
                "Inspect the included training arena without changing your existing player or scenes.");
            AddButton(scroll, "Open included demo (asks before discarding scene edits)",
                HprGameplaySuiteSceneBuilder.OpenShowcase);
            AddButton(scroll, "Select editable weapon definition",
                () => SelectAsset(Root + "/Samples/DemoRifle.asset"));
            AddButton(scroll, "Select editable healing ability",
                () => SelectAsset(Root + "/Samples/RepairAbility.asset"));

            AddSection(scroll, "Integrate into an existing game",
                "You own your project's controllers and gameplay rules. These modules do not install a controller, Input System package, render pipeline or project settings. Read the architecture document before replacing any existing service.");
            AddButton(scroll, "Select architecture and integration examples",
                () => SelectAsset(Root + "/ARCHITECTURE.md"));
            AddButton(scroll, "Select installation and troubleshooting guide",
                () => SelectAsset(Root + "/QUICKSTART.md"));

            AddSection(scroll, "Compatibility checks",
                "This check examines the imported module and sample files only. It does not claim that your project has passed compilation, Play Mode, input, render pipeline or asset-store validation.");
            AddButton(scroll, "Run read-only package-layout check", RefreshStatus);
            AddButton(scroll, "Copy diagnostic details", () =>
            {
                EditorGUIUtility.systemCopyBuffer = lastReport;
                if (advice != null) advice.text = "Read-only report copied to clipboard.";
            });

            AddSection(scroll, "Demo render pipeline",
                "Built-in sample materials are shipped without third-party dependencies. For URP/HDRP, adaptation is always opt-in and should only touch HPR sample materials.");
            AddButton(scroll, "Adapt HPR demo materials (with confirmation)", () =>
            {
                if (!EditorUtility.DisplayDialog("Modify HPR sample materials?",
                    "This action changes the shader on HPR sample materials only. " +
                    "Your project render pipeline and external assets stay unchanged. Continue?",
                    "Adapt sample materials", "Cancel"))
                {
                    if (advice != null) advice.text = "No materials changed.";
                    return;
                }

                try
                {
                    HprGameplaySuiteSceneBuilder.AdaptDemoMaterials();
                    if (advice != null)
                        advice.text = "HPR sample materials adapted. Verify the scene in Game view.";
                }
                catch (Exception error)
                {
                    Debug.LogException(error);
                    if (advice != null)
                        advice.text = "Conversion failed. Inspect the Console for the exact cause.";
                }
            });

            AddSection(scroll, "Scope",
                "This is a modular C# example toolkit, not a character controller, full inventory editor, NavMesh AI, cloud persistence or multiplayer SDK.");

            RefreshStatus();
        }

        private static void AddSection(VisualElement parent, string title, string description)
        {
            Label header = new Label(title);
            header.AddToClassList("hpr-suite-section");
            parent.Add(header);

            Label body = new Label(description);
            body.AddToClassList("hpr-suite-description");
            parent.Add(body);
        }

        private static void AddButton(VisualElement parent, string label, Action action)
        {
            Button button = new Button(action) { text = label };
            button.AddToClassList("hpr-suite-button");
            parent.Add(button);
        }

        private static void SelectAsset(string path)
        {
            UnityEngine.Object asset = AssetDatabase.LoadMainAssetAtPath(path);
            if (asset == null)
            {
                EditorUtility.DisplayDialog("HPR Suite",
                    "The asset is missing: " + path + "\nImport the complete .unitypackage.", "OK");
                return;
            }
            Selection.activeObject = asset;
            EditorGUIUtility.PingObject(asset);
        }

        private void RefreshStatus()
        {
            if (status == null || advice == null) return;

            var missing = new List<string>();
            int scriptCount = 0;
            int foundModules = 0;
            foreach (string name in Modules)
            {
                string path = Root + "/Modules/com.hpr." + name + "/Runtime";
                string[] scripts = AssetDatabase.FindAssets("t:MonoScript", new[] { path });
                if (scripts.Length == 0) missing.Add(name);
                else { scriptCount += scripts.Length; foundModules++; }
            }
            foreach (string path in new[] {
                Root + "/Demo/GameplaySuiteShowcase.unity",
                Root + "/Samples/DemoRifle.asset",
                Root + "/Samples/RepairAbility.asset",
                Root + "/ARCHITECTURE.md"
            })
            {
                if (AssetDatabase.LoadMainAssetAtPath(path) == null)
                    missing.Add(path);
            }

            RenderPipelineAsset pipeline = GraphicsSettings.currentRenderPipeline;
            string pipelineName = pipeline == null ? "Built-in" : pipeline.GetType().Name;
            lastReport = "HPR Gameplay Suite package layout" +
                "\nUnity Editor: " + Application.unityVersion +
                "\nRender pipeline: " + pipelineName +
                "\nCompilation running: " + EditorApplication.isCompiling +
                "\nRuntime modules: " + foundModules + "/" + Modules.Length +
                "\nRuntime source scripts: " + scriptCount +
                "\nMissing paths/modules: " + (missing.Count == 0 ? "none" : string.Join(", ", missing)) +
                "\nNOTE: This is layout validation only, not runtime or marketplace approval.";

            status.text = "Unity " + Application.unityVersion + "  |  " +
                pipelineName + "  |  " + (missing.Count == 0 ? "PACKAGE FILES PRESENT" : "INCOMPLETE IMPORT");
            advice.text = EditorApplication.isCompiling ?
                "Scripts are compiling; inspect the Console before entering Play mode." :
                missing.Count > 0 ?
                "Missing: " + string.Join(", ", missing) +
                ". Re-import the complete package without deleting existing project assets." :
                "All ten runtime modules and required demo files are present. " +
                "Open the demo and verify gameplay; this is not a runtime test.";
        }
    }
}
#endif
