// Original Unity Editor integration guide; no project mutation on import.
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.UIElements;

namespace HPR.GameplaySuite
{
    /// <summary>
    /// Non-invasive entry point for experienced programmers integrating HPR code.
    /// Reads project structure and offers explicit customer-owned sample copies.
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
            AddButton(scroll, "Create my own editable weapon definition",
                () => PromptCopySample(Root + "/Samples/DemoRifle.asset"));
            AddButton(scroll, "Create my own editable healing ability",
                () => PromptCopySample(Root + "/Samples/RepairAbility.asset"));

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

        private void PromptCopySample(string sourcePath)
        {
            string baseName = Path.GetFileNameWithoutExtension(sourcePath);
            string destination = EditorUtility.SaveFilePanelInProject(
                "Create your own HPR sample asset", baseName + "-MyGame", "asset",
                "Choose a folder belonging to your game, outside Assets/HPRGameplaySuite. " +
                "Vendor-owned sample assets may be replaced by future package updates.",
                "Assets");
            if (string.IsNullOrWhiteSpace(destination))
            {
                if (advice != null) advice.text = "Copy cancelled. No assets changed.";
                return;
            }

            try
            {
                UnityEngine.Object copy = CopySampleToCustomerPath(sourcePath, destination);
                Selection.activeObject = copy;
                EditorGUIUtility.PingObject(copy);
                if (advice != null)
                    advice.text = "Created your own independent copy, including its sample " +
                                  "dependencies and unique IDs. The vendor examples are unchanged.";
            }
            catch (Exception error) when (error is ArgumentException ||
                                          error is IOException ||
                                          error is InvalidOperationException ||
                                          error is UnityException)
            {
                Debug.LogException(error);
                EditorUtility.DisplayDialog("HPR sample copy incomplete", error.Message, "OK");
                if (advice != null)
                    advice.text = "No vendor sample was edited. New customer-owned files may remain; " +
                                  "review the listed paths before trying again. " +
                                  "No automatic cleanup was performed. See the Console.";
            }
        }

        /// <summary>
        /// Copy a ScriptableObject and its packaged ScriptableObject dependencies
        /// into a customer-owned Assets folder. Rebind copied object references and
        /// issue unique runtime Id values. Validate every path before writing any
        /// file. If a later step fails after creating files, preserve the new
        /// files for explicit buyer inspection rather than deleting a path whose
        /// ownership may have changed in the meantime.
        /// Called only from an explicit user action, never upon package import.
        /// </summary>
        internal static UnityEngine.Object CopySampleToCustomerPath(
            string sourcePath, string destinationPath)
        {
            const string vendorSamples = Root + "/Samples/";
            if (string.IsNullOrWhiteSpace(sourcePath) ||
                !sourcePath.StartsWith(vendorSamples, StringComparison.Ordinal) ||
                !sourcePath.EndsWith(".asset", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException(
                    "Expected an included HPR ScriptableObject sample.", nameof(sourcePath));
            if (string.IsNullOrWhiteSpace(destinationPath))
                throw new ArgumentException(
                    "Choose a destination in your own Assets folder.", nameof(destinationPath));

            string normalizedDestination = destinationPath.Replace('\\', '/');
            if (!normalizedDestination.StartsWith("Assets/", StringComparison.Ordinal) ||
                normalizedDestination.StartsWith(Root + "/", StringComparison.Ordinal) ||
                !normalizedDestination.EndsWith(".asset", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException(
                    "Destination must be an .asset file in your own Assets folder, not the HPR vendor root.",
                    nameof(destinationPath));
            foreach (string part in normalizedDestination.Split('/'))
                if (part == "." || part == ".." || string.IsNullOrWhiteSpace(part))
                    throw new ArgumentException("Destination path contains a disallowed segment.", nameof(destinationPath));

            string directory = Path.GetDirectoryName(normalizedDestination)?.Replace('\\', '/');
            if (string.IsNullOrWhiteSpace(directory) || !AssetDatabase.IsValidFolder(directory))
                throw new ArgumentException(
                    "Destination folder is missing; choose an existing folder.", nameof(destinationPath));

            // AssetDatabase.GetDependencies includes runtime MonoScript references,
            // which intentionally remain in the vendor package; only clone authored
            // ScriptableObject sample definitions that an upgrade could replace.
            var sourcePaths = new List<string> { sourcePath };
            foreach (string referencedPath in AssetDatabase.GetDependencies(sourcePath, true))
            {
                if (!referencedPath.StartsWith(vendorSamples, StringComparison.Ordinal) ||
                    string.Equals(referencedPath, sourcePath, StringComparison.Ordinal))
                    continue;
                if (!referencedPath.EndsWith(".asset", StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException(
                        "Sample depends on an unsupported vendor asset: " + referencedPath +
                        ". Nothing has been copied.");
                if (!sourcePaths.Contains(referencedPath))
                    sourcePaths.Add(referencedPath);
            }
            if (sourcePaths.Count > 32)
                throw new InvalidOperationException(
                    "Sample dependency graph exceeds the supported 32 asset limit.");
            sourcePaths.Sort(StringComparer.Ordinal);

            string requestedStem = Path.GetFileNameWithoutExtension(normalizedDestination);
            var destinations = new Dictionary<string, string>(StringComparer.Ordinal);
            var sourceGuids = new Dictionary<string, string>(StringComparer.Ordinal);
            var uniqueDestinations = new HashSet<string>(StringComparer.Ordinal);
            foreach (string source in sourcePaths)
            {
                UnityEngine.Object original = AssetDatabase.LoadMainAssetAtPath(source);
                string sourceGuid = AssetDatabase.AssetPathToGUID(source);
                if (original == null || string.IsNullOrEmpty(sourceGuid))
                    throw new FileNotFoundException("Sample dependency was not found.", source);

                string target = string.Equals(source, sourcePath, StringComparison.Ordinal)
                    ? normalizedDestination
                    : directory + "/" + requestedStem + "__HPR_" +
                      Path.GetFileNameWithoutExtension(source) + ".asset";
                string relative = target.Substring("Assets/".Length);
                string physical = Path.Combine(Application.dataPath, relative);
                if (!uniqueDestinations.Add(target) ||
                    AssetDatabase.LoadMainAssetAtPath(target) != null ||
                    File.Exists(physical) || Directory.Exists(physical) ||
                    File.Exists(physical + ".meta") || Directory.Exists(physical + ".meta"))
                    throw new IOException(
                        "An output asset already exists, or dependencies have conflicting names: " +
                        target + ". Nothing has been copied.");
                destinations.Add(source, target);
                sourceGuids.Add(source, sourceGuid);
            }

            var newlyCreated = new List<string>();
            string lastAttemptedTarget = null;
            try
            {
                // Copy all files first, so every referenced destination exists
                // before any new copy is rewired. Never edit original assets.
                foreach (string source in sourcePaths)
                {
                    string target = destinations[source];
                    // The original preflight can be stale if another importer
                    // created this path while the dependencies were analyzed.
                    // Recheck both the Unity registry and physical asset/meta
                    // immediately before attempting this individual CopyAsset.
                    string physical = Path.Combine(Application.dataPath,
                        target.Substring("Assets/".Length));
                    if (AssetDatabase.LoadMainAssetAtPath(target) != null ||
                        File.Exists(physical) || Directory.Exists(physical) ||
                        File.Exists(physical + ".meta") ||
                        Directory.Exists(physical + ".meta"))
                        throw new IOException("The output became occupied before copying: " + target +
                            ". Inspect the owning GUID; nothing at this path was overwritten by HPR.");
                    lastAttemptedTarget = target;
                    if (!AssetDatabase.CopyAsset(source, target))
                        throw new IOException("Unity could not copy sample asset: " + source +
                            ". The last attempted target may require manual inspection: " + target);
                    newlyCreated.Add(target);
                    lastAttemptedTarget = null;
                }

                foreach (string source in sourcePaths)
                {
                    string target = destinations[source];
                    UnityEngine.Object copy = AssetDatabase.LoadMainAssetAtPath(target);
                    string newGuid = AssetDatabase.AssetPathToGUID(target);
                    if (copy == null || newGuid.Length != 32 ||
                        string.Equals(newGuid, sourceGuids[source], StringComparison.Ordinal))
                        throw new InvalidOperationException(
                            "Unity failed to create a distinct GUID for " + target);

                    var serialized = new SerializedObject(copy);
                    bool dirty = false;
                    SerializedProperty iterator = serialized.GetIterator();
                    if (iterator.NextVisible(true))
                    {
                        do
                        {
                            if (iterator.propertyType != SerializedPropertyType.ObjectReference)
                                continue;
                            UnityEngine.Object dependency = iterator.objectReferenceValue;
                            if (dependency == null)
                                continue;
                            string originalPath = AssetDatabase.GetAssetPath(dependency);
                            if (destinations.TryGetValue(originalPath, out string clonePath))
                            {
                                UnityEngine.Object clonedDependency =
                                    AssetDatabase.LoadMainAssetAtPath(clonePath);
                                if (clonedDependency == null)
                                    throw new InvalidOperationException(
                                        "Copied dependency cannot be resolved: " + clonePath);
                                iterator.objectReferenceValue = clonedDependency;
                                dirty = true;
                            }
                        }
                        while (iterator.NextVisible(true));
                    }

                    SerializedProperty runtimeId = serialized.FindProperty("Id");
                    if (runtimeId != null &&
                        runtimeId.propertyType == SerializedPropertyType.String)
                    {
                        runtimeId.stringValue = "hpr_user_" + newGuid.Substring(0, 16);
                        dirty = true;
                    }
                    if (dirty)
                        serialized.ApplyModifiedPropertiesWithoutUndo();
                }
                // Save only copies authored by this explicit user operation.
                // Unity's global SaveAssets would flush OTHER dirty buyer assets.
                // SaveAssetIfDirty bypasses OnWillSaveAssets callbacks for these
                // named new assets, so VCS integrations need independent review.
                // Nothing else was saved by this operation.
                foreach (string target in destinations.Values)
                {
                    UnityEngine.Object copy = AssetDatabase.LoadMainAssetAtPath(target);
                    if (copy == null)
                        throw new InvalidOperationException("New customer-owned copy cannot be saved: " + target);
                    AssetDatabase.SaveAssetIfDirty(copy);
                }

                // Verify no newly copied object still depends on an original
                // vendor-owned *sample*. Script runtime references are intentional.
                foreach (string target in destinations.Values)
                {
                    UnityEngine.Object copy = AssetDatabase.LoadMainAssetAtPath(target);
                    if (copy == null)
                        throw new InvalidOperationException("Copied asset vanished: " + target);
                    var serialized = new SerializedObject(copy);
                    SerializedProperty iterator = serialized.GetIterator();
                    if (iterator.NextVisible(true))
                    {
                        do
                        {
                            if (iterator.propertyType != SerializedPropertyType.ObjectReference ||
                                iterator.objectReferenceValue == null)
                                continue;
                            string dependency = AssetDatabase.GetAssetPath(iterator.objectReferenceValue);
                            if (dependency.StartsWith(vendorSamples, StringComparison.Ordinal))
                                throw new InvalidOperationException(
                                    "Copied asset retains a vendor-owned sample dependency: " +
                                    dependency);
                        }
                        while (iterator.NextVisible(true));
                    }
                }
                return AssetDatabase.LoadMainAssetAtPath(normalizedDestination);
            }
            catch (Exception copyFailure)
            {
                if (newlyCreated.Count == 0 && lastAttemptedTarget == null)
                    throw;
                // CopyAsset can return false after part of a file operation;
                // that last target might exist despite a false return. Keep
                // confirmed and uncertain outputs for explicit customer review.
                // Automatic deletion by pathname could destroy another
                // importer's replacement if ownership changed concurrently.
                string createdPaths = newlyCreated.Count == 0
                    ? "(none confirmed)" : string.Join(", ", newlyCreated);
                string uncertainPath = lastAttemptedTarget == null ? string.Empty :
                    " The last attempted output may also exist: " + lastAttemptedTarget + ".";
                throw new InvalidOperationException(
                    "A partial HPR asset copy was interrupted. Unity created some assets: " +
                    createdPaths + "." + uncertainPath +
                    " Cause: " + copyFailure.Message + ". No automatic cleanup was performed. " +
                    "Inspect the listed paths and their GUIDs before deletion or retry.",
                    copyFailure);
            }
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
