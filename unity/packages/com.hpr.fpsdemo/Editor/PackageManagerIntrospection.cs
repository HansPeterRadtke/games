using System;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace HPR
{
    public static class PackageManagerIntrospection
    {
        [MenuItem("Tools/HPR/Debug/List Asset Store Types")]
        public static void ListAssetStoreTypes()
        {
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies().OrderBy(a => a.FullName))
            {
                Type[] types;
                try
                {
                    types = assembly.GetTypes();
                }
                catch (ReflectionTypeLoadException ex)
                {
                    types = ex.Types.Where(t => t != null).ToArray();
                }

                var interesting = types.Where(t =>
                    t.FullName.IndexOf("AssetStore", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    t.FullName.IndexOf("PackageManager", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    t.FullName.IndexOf("Kharma", StringComparison.OrdinalIgnoreCase) >= 0)
                    .OrderBy(t => t.FullName)
                    .ToArray();
                if (interesting.Length == 0)
                {
                    continue;
                }

                Debug.Log($"ASSEMBLY {assembly.FullName}");
                foreach (var type in interesting.Take(80))
                {
                    Debug.Log($"TYPE {type.FullName}");
                }
            }
        }

        [MenuItem("Tools/HPR/Debug/Describe Type")]
        public static void DescribeTypeFromArgs()
        {
            var args = Environment.GetCommandLineArgs();
            string typeName = null;
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "-describeType")
                {
                    typeName = args[i + 1];
                    break;
                }
            }

            if (string.IsNullOrWhiteSpace(typeName))
            {
                throw new Exception("Missing -describeType <typename>");
            }

            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                var type = assembly.GetType(typeName, false);
                if (type == null)
                {
                    continue;
                }

                Debug.Log($"TYPE {type.FullName} from {assembly.FullName}");
                foreach (var method in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
                {
                    var parameters = string.Join(", ", method.GetParameters().Select(parameter => $"{parameter.ParameterType.Name} {parameter.Name}"));
                    Debug.Log($"METHOD {method.ReturnType.Name} {method.Name}({parameters})");
                }
                foreach (var prop in type.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
                {
                    Debug.Log($"PROP {prop.PropertyType.Name} {prop.Name}");
                }
                foreach (var field in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
                {
                    Debug.Log($"FIELD {field.FieldType.Name} {field.Name}");
                }
                return;
            }

            throw new Exception($"Type not found: {typeName}");
        }
    }
}
