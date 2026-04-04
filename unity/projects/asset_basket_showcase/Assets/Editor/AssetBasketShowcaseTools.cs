using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace HPR.AssetBasketShowcase
{
    public static class AssetBasketShowcaseTools
    {
        public static void ImportPackageFromArgs()
        {
            var args = ParseArgs(Environment.GetCommandLineArgs());
            var packagePath = RequireArg(args, "assetPackage");
            ImportPackageInternal(packagePath);
        }

        public static void ImportPackagesFromArgs()
        {
            var args = ParseArgs(Environment.GetCommandLineArgs());
            var packageListPath = RequireArg(args, "packageList");
            if (!File.Exists(packageListPath))
            {
                throw new FileNotFoundException($"Package list not found: {packageListPath}");
            }

            foreach (var packagePath in File.ReadAllLines(packageListPath).Select(line => line.Trim()).Where(line => !string.IsNullOrWhiteSpace(line)))
            {
                ImportPackageInternal(packagePath);
            }
        }

        private static void ImportPackageInternal(string packagePath)
        {
            if (!File.Exists(packagePath))
            {
                throw new FileNotFoundException($"Unity package not found: {packagePath}");
            }

            Debug.Log($"SHOWCASE import package: {packagePath}");
            var importImmediatelyMethod = typeof(AssetDatabase).GetMethod(
                "ImportPackageImmediately",
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic,
                null,
                new[] { typeof(string) },
                null);
            var imported = importImmediatelyMethod != null && (bool)importImmediatelyMethod.Invoke(null, new object[] { packagePath });
            if (!imported)
            {
                var packageUtilityType = typeof(Editor).Assembly.GetType("UnityEditor.PackageUtility", true);
                var extractMethod = packageUtilityType.GetMethod(
                    "ExtractAndPrepareAssetList",
                    BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
                var importMethod = packageUtilityType.GetMethod(
                    "ImportPackageAssetsImmediately",
                    BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
                if (extractMethod == null || importMethod == null)
                {
                    throw new Exception($"Could not resolve immediate import path for {packagePath}");
                }

                object[] extractArgs = { packagePath, string.Empty, string.Empty };
                var packageItems = extractMethod.Invoke(null, extractArgs) as Array;
                if (packageItems == null || packageItems.Length == 0)
                {
                    throw new Exception($"No importable items found in package {packagePath}");
                }

                importMethod.Invoke(null, new object[] { packagePath, packageItems });
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Debug.Log($"SHOWCASE import complete: {packagePath}");
        }

        public static void InventoryReportFromArgs()
        {
            var args = ParseArgs(Environment.GetCommandLineArgs());
            var reportPath = RequireArg(args, "reportPath");
            var roots = GetScanRoots(args);
            var lines = new List<string>();
            lines.Add("Asset basket showcase inventory");
            lines.Add($"Generated: {DateTime.UtcNow:O}");
            lines.Add($"Roots: {string.Join(", ", roots)}");
            lines.Add(string.Empty);

            foreach (var root in roots.OrderBy(value => value))
            {
                lines.Add($"[{root}]");
                lines.Add("prefabs=" + AssetDatabase.FindAssets("t:Prefab", new[] { root }).Length);
                lines.Add("models=" + AssetDatabase.FindAssets("t:Model", new[] { root }).Length);
                lines.Add("materials=" + AssetDatabase.FindAssets("t:Material", new[] { root }).Length);
                lines.Add("textures=" + AssetDatabase.FindAssets("t:Texture2D", new[] { root }).Length);
                lines.Add("animations=" + AssetDatabase.FindAssets("t:AnimationClip", new[] { root }).Length);
                lines.Add("scenes=" + AssetDatabase.FindAssets("t:Scene", new[] { root }).Length);
                lines.Add(string.Empty);
            }

            Directory.CreateDirectory(Path.GetDirectoryName(reportPath) ?? ".");
            File.WriteAllLines(reportPath, lines);
            Debug.Log($"SHOWCASE inventory written: {reportPath}");
        }

        public static void StripImportedCodeFromArgs()
        {
            var args = ParseArgs(Environment.GetCommandLineArgs());
            var roots = GetScanRoots(args);
            var deleted = new List<string>();
            var codeExtensions = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                ".cs",
                ".js",
                ".boo",
                ".dll",
                ".asmdef",
                ".asmref",
                ".rsp",
            };

            foreach (var root in roots)
            {
                var absoluteRoot = Path.Combine(Directory.GetParent(Application.dataPath)?.FullName ?? Application.dataPath, root);
                if (!Directory.Exists(absoluteRoot))
                {
                    continue;
                }

                foreach (var file in Directory.GetFiles(absoluteRoot, "*", SearchOption.AllDirectories))
                {
                    if (!codeExtensions.Contains(Path.GetExtension(file)))
                    {
                        continue;
                    }

                    var relative = "Assets" + file.Substring(Application.dataPath.Length).Replace('\\', '/');
                    if (relative.StartsWith("Assets/Editor/", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    if (AssetDatabase.DeleteAsset(relative))
                    {
                        deleted.Add(relative);
                    }
                }

                foreach (var editorDir in Directory.GetDirectories(absoluteRoot, "Editor", SearchOption.AllDirectories).OrderByDescending(path => path.Length))
                {
                    var relative = "Assets" + editorDir.Substring(Application.dataPath.Length).Replace('\\', '/');
                    if (relative.Equals("Assets/Editor", StringComparison.OrdinalIgnoreCase) || relative.StartsWith("Assets/Editor/", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    if (AssetDatabase.IsValidFolder(relative) && AssetDatabase.DeleteAsset(relative))
                    {
                        deleted.Add(relative);
                    }
                }
            }

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Debug.Log($"SHOWCASE stripped code assets: {deleted.Count}");
        }

        public static void RepairUnsupportedMaterialsFromArgs()
        {
            var args = ParseArgs(Environment.GetCommandLineArgs());
            var roots = GetScanRoots(args);
            var repaired = 0;
            var standardShader = Shader.Find("Standard");
            if (standardShader == null)
            {
                throw new Exception("Could not resolve Standard shader");
            }

            foreach (var root in roots)
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { root }))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    var material = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (material == null)
                    {
                        continue;
                    }

                    var shaderName = material.shader != null ? material.shader.name : string.Empty;
                    var needsRepair =
                        material.shader == null ||
                        shaderName.Contains("HDRP", StringComparison.OrdinalIgnoreCase) ||
                        shaderName.Contains("Universal Render Pipeline", StringComparison.OrdinalIgnoreCase) ||
                        shaderName.Contains("URP", StringComparison.OrdinalIgnoreCase) ||
                        shaderName.Contains("Error", StringComparison.OrdinalIgnoreCase);
                    if (!needsRepair)
                    {
                        continue;
                    }

                    var mainTex = GetTexture(material, "_BaseColorMap", "_BaseMap", "_MainTex", "_BaseColorTexture");
                    var bumpTex = GetTexture(material, "_NormalMap", "_BumpMap");
                    var metallicTex = GetTexture(material, "_MaskMap", "_MetallicGlossMap");
                    var emissionTex = GetTexture(material, "_EmissionMap");
                    var color = GetColor(material, "_BaseColor", "_Color");

                    material.shader = standardShader;
                    if (mainTex != null && material.HasProperty("_MainTex"))
                    {
                        material.SetTexture("_MainTex", mainTex);
                    }
                    if (bumpTex != null && material.HasProperty("_BumpMap"))
                    {
                        material.SetTexture("_BumpMap", bumpTex);
                        material.EnableKeyword("_NORMALMAP");
                    }
                    if (metallicTex != null && material.HasProperty("_MetallicGlossMap"))
                    {
                        material.SetTexture("_MetallicGlossMap", metallicTex);
                    }
                    if (emissionTex != null && material.HasProperty("_EmissionMap"))
                    {
                        material.SetTexture("_EmissionMap", emissionTex);
                        material.EnableKeyword("_EMISSION");
                    }
                    if (material.HasProperty("_Color"))
                    {
                        material.SetColor("_Color", color);
                    }

                    EditorUtility.SetDirty(material);
                    repaired++;
                }
            }

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Debug.Log($"SHOWCASE repaired materials: {repaired}");
        }

        public static void ValidateSceneFromArgs()
        {
            var args = ParseArgs(Environment.GetCommandLineArgs());
            var scenePath = RequireArg(args, "scenePath");
            var reportPath = RequireArg(args, "reportPath");

            var scene = EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            var roots = scene.GetRootGameObjects();
            var renderers = UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            var animators = UnityEngine.Object.FindObjectsByType<Animator>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            var particleSystems = UnityEngine.Object.FindObjectsByType<ParticleSystem>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            var terrains = UnityEngine.Object.FindObjectsByType<Terrain>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            var textMeshes = UnityEngine.Object.FindObjectsByType<TextMesh>(FindObjectsInactive.Include, FindObjectsSortMode.None);

            var lines = new List<string>
            {
                "Asset basket showcase scene validation",
                $"Generated: {DateTime.UtcNow:O}",
                $"Scene: {scenePath}",
                $"root_objects={roots.Length}",
                $"renderers={renderers.Length}",
                $"animators={animators.Length}",
                $"particle_systems={particleSystems.Length}",
                $"terrains={terrains.Length}",
                $"labels={textMeshes.Length}",
            };

            Directory.CreateDirectory(Path.GetDirectoryName(reportPath) ?? ".");
            File.WriteAllLines(reportPath, lines);
            Debug.Log($"SHOWCASE scene validation written: {reportPath}");
        }


        public static Dictionary<string, string> ParseArgs(IEnumerable<string> args)
        {
            var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            string pendingKey = null;
            foreach (var arg in args)
            {
                if (arg.StartsWith("-", StringComparison.Ordinal))
                {
                    pendingKey = arg.TrimStart('-');
                    result[pendingKey] = string.Empty;
                    continue;
                }

                if (pendingKey != null)
                {
                    result[pendingKey] = arg;
                    pendingKey = null;
                }
            }
            return result;
        }

        private static string RequireArg(IReadOnlyDictionary<string, string> args, string key)
        {
            if (!args.TryGetValue(key, out var value) || string.IsNullOrWhiteSpace(value))
            {
                throw new Exception($"Missing -{key} <value>");
            }
            return value;
        }

        public static string[] GetScanRoots(IReadOnlyDictionary<string, string> args)
        {
            if (args.TryGetValue("roots", out var rootsValue) && !string.IsNullOrWhiteSpace(rootsValue))
            {
                return rootsValue
                    .Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries)
                    .Select(value => value.Trim())
                    .Where(value => !string.IsNullOrWhiteSpace(value))
                    .ToArray();
            }

            var excluded = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                "Assets/Editor",
                "Assets/Scenes",
                "Assets/Generated",
                "Assets/Settings",
                "Assets/TextMesh Pro",
            };

            return AssetDatabase.GetSubFolders("Assets")
                .Where(path => !excluded.Contains(path))
                .OrderBy(path => path)
                .ToArray();
        }

        private static Texture GetTexture(Material material, params string[] propertyNames)
        {
            foreach (var propertyName in propertyNames)
            {
                if (material.HasProperty(propertyName))
                {
                    var value = material.GetTexture(propertyName);
                    if (value != null)
                    {
                        return value;
                    }
                }
            }

            return null;
        }

        private static Color GetColor(Material material, params string[] propertyNames)
        {
            foreach (var propertyName in propertyNames)
            {
                if (material.HasProperty(propertyName))
                {
                    return material.GetColor(propertyName);
                }
            }

            return Color.white;
        }
    }
}
