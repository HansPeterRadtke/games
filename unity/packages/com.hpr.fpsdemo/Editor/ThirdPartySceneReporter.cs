using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class ThirdPartySceneReporter
{
    private const string MainScenePath = "Assets/Scenes/Gameplay.unity";
    private const string ArtRootPath = "World/PropsRoot/ThirdPartyArt";

    [MenuItem("HPR/Debug/Report Third-Party Scene Assets")]
    public static void ReportSceneAssetsFromArgs()
    {
        var args = Environment.GetCommandLineArgs();
        string containsFilter = null;
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "-contains")
            {
                containsFilter = args[i + 1];
                break;
            }
        }

        EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
        var artRoot = FindByHierarchyPath(ArtRootPath);
        if (artRoot == null)
        {
            throw new Exception($"{ArtRootPath} not found in Gameplay scene.");
        }

        foreach (var root in artRoot.Cast<Transform>())
        {
            foreach (var instance in EnumerateSelfAndDescendants(root))
            {
                ReportInstance(instance, containsFilter);
            }
        }
    }

    private static void ReportInstance(Transform instance, string containsFilter)
    {
        if (instance == null || instance.GetComponentsInChildren<Renderer>(true).Length == 0)
        {
            return;
        }

        var source = PrefabUtility.GetCorrespondingObjectFromSource(instance.gameObject);
        var sourcePath = source != null ? AssetDatabase.GetAssetPath(source) : "<scene-only>";
        string fullPath = GetPath(instance);
        if (!string.IsNullOrWhiteSpace(containsFilter) &&
            sourcePath.IndexOf(containsFilter, StringComparison.OrdinalIgnoreCase) < 0 &&
            instance.name.IndexOf(containsFilter, StringComparison.OrdinalIgnoreCase) < 0 &&
            fullPath.IndexOf(containsFilter, StringComparison.OrdinalIgnoreCase) < 0)
        {
            return;
        }

        var renderers = instance.GetComponentsInChildren<Renderer>(true);
        Bounds? bounds = null;
        foreach (var renderer in renderers)
        {
            bounds = bounds.HasValue ? Encapsulate(bounds.Value, renderer.bounds) : renderer.bounds;
        }

        string sizeText = bounds.HasValue ? bounds.Value.size.ToString("F3") : "none";
        Debug.Log($"SCENE_ASSET name={fullPath} source={sourcePath} renderers={renderers.Length} size={sizeText}");

        var reportedMaterials = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var renderer in renderers)
        {
            foreach (var material in renderer.sharedMaterials.Where(mat => mat != null))
            {
                string materialKey = $"{renderer.name}:{material.name}";
                if (!reportedMaterials.Add(materialKey))
                {
                    continue;
                }

                var texture = ResolveMainTexture(material);
                Debug.Log(
                    $"SCENE_MATERIAL object={GetPath(renderer.transform)} mat={material.name} shader={material.shader?.name ?? "<null>"} tex={(texture != null ? texture.name : "<none>")}");
            }
        }
    }

    private static Texture ResolveMainTexture(Material material)
    {
        if (material == null)
        {
            return null;
        }

        if (material.HasProperty("_MainTex"))
        {
            var main = material.GetTexture("_MainTex");
            if (main != null)
            {
                return main;
            }
        }

        if (material.HasProperty("_BaseMap"))
        {
            var baseMap = material.GetTexture("_BaseMap");
            if (baseMap != null)
            {
                return baseMap;
            }
        }

        return null;
    }

    private static Bounds Encapsulate(Bounds a, Bounds b)
    {
        a.Encapsulate(b);
        return a;
    }

    private static string GetPath(Transform node)
    {
        var parts = new Stack<string>();
        while (node != null)
        {
            parts.Push(node.name);
            node = node.parent;
        }

        return string.Join("/", parts);
    }

    private static IEnumerable<Transform> EnumerateSelfAndDescendants(Transform root)
    {
        if (root == null)
        {
            yield break;
        }

        yield return root;
        foreach (Transform child in root)
        {
            foreach (var nested in EnumerateSelfAndDescendants(child))
            {
                yield return nested;
            }
        }
    }

    private static Transform FindByHierarchyPath(string hierarchyPath)
    {
        if (string.IsNullOrWhiteSpace(hierarchyPath))
        {
            return null;
        }

        var segments = hierarchyPath.Split('/').Where(segment => !string.IsNullOrWhiteSpace(segment)).ToArray();
        if (segments.Length == 0)
        {
            return null;
        }

        var root = SceneManager.GetActiveScene().GetRootGameObjects()
            .FirstOrDefault(candidate => candidate.name == segments[0]);
        if (root == null)
        {
            return null;
        }

        Transform current = root.transform;
        for (int i = 1; i < segments.Length; i++)
        {
            current = current.Find(segments[i]) ?? FindDescendant(current, segments[i]);
            if (current == null)
            {
                return null;
            }
        }

        return current;
    }

    private static Transform FindDescendant(Transform root, string name)
    {
        foreach (Transform child in root)
        {
            if (child.name == name)
            {
                return child;
            }

            var nested = FindDescendant(child, name);
            if (nested != null)
            {
                return nested;
            }
        }

        return null;
    }
}
