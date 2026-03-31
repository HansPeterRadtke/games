using System;
using System.IO;
using System.Linq;
using UnityEditor;

public static class HprPackageExportRunner
{
    public static void ExportFromEnvironment()
    {
        try
        {
            var outputPath = RequireEnv("HPR_EXPORT_OUTPUT");
            var assetPaths = RequireEnv("HPR_EXPORT_ASSET_PATHS")
                .Split(new[] {';'}, StringSplitOptions.RemoveEmptyEntries)
                .Select(path => path.Trim())
                .Where(path => !string.IsNullOrWhiteSpace(path))
                .ToArray();

            if (assetPaths.Length == 0)
            {
                throw new InvalidOperationException("HPR_EXPORT_ASSET_PATHS did not provide any asset roots.");
            }

            foreach (var assetPath in assetPaths)
            {
                if (!AssetDatabase.IsValidFolder(assetPath) && AssetDatabase.LoadMainAssetAtPath(assetPath) == null)
                {
                    throw new FileNotFoundException($"Export asset path not found in project: {assetPath}");
                }
            }

            var outputDirectory = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrWhiteSpace(outputDirectory))
            {
                Directory.CreateDirectory(outputDirectory);
            }

            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            AssetDatabase.ExportPackage(assetPaths, outputPath, ExportPackageOptions.Recurse);

            if (!File.Exists(outputPath))
            {
                throw new FileNotFoundException($"Unity did not create the expected export: {outputPath}");
            }

            var info = new FileInfo(outputPath);
            Console.WriteLine($"Exported package: {info.FullName}");
            Console.WriteLine($"Export size: {info.Length} bytes");
            EditorApplication.Exit(0);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            EditorApplication.Exit(1);
        }
    }

    private static string RequireEnv(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"Missing required environment variable: {name}");
        }

        return value;
    }
}
