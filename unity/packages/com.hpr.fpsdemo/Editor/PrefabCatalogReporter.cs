using System;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace HPR
{
    public static class PrefabCatalogReporter
    {
        [MenuItem("Tools/HPR/Debug/Report Prefab Catalog")]
        public static void ReportPrefabCatalogFromArgs()
        {
            var args = Environment.GetCommandLineArgs();
            string folder = null;
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "-assetFolder")
                {
                    folder = args[i + 1];
                    break;
                }
            }

            if (string.IsNullOrWhiteSpace(folder))
            {
                throw new Exception("Missing -assetFolder <Assets/...>");
            }

            var guids = AssetDatabase.FindAssets("t:GameObject", new[] { folder });
            foreach (var guid in guids.OrderBy(guid => AssetDatabase.GUIDToAssetPath(guid)))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase) &&
                    !path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab == null)
                {
                    continue;
                }

                var instance = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
                if (instance == null)
                {
                    continue;
                }

                try
                {
                    var renderers = instance.GetComponentsInChildren<Renderer>(true);
                    if (renderers.Length == 0)
                    {
                        Debug.Log($"CATALOG {path} renderers=0");
                        continue;
                    }

                    var bounds = renderers[0].bounds;
                    foreach (var renderer in renderers.Skip(1))
                    {
                        bounds.Encapsulate(renderer.bounds);
                    }

                    Debug.Log($"CATALOG {path} size={bounds.size} center={bounds.center} children={instance.GetComponentsInChildren<Transform>(true).Length - 1}");
                }
                finally
                {
                    UnityEngine.Object.DestroyImmediate(instance);
                }
            }
        }
    }
}
