using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using UnityEditor;
using UnityEngine;

public static class AssetStoreImportTools
{
    private static readonly string[] KnownIncompatibleImportPaths =
    {
        "Assets/Survivalist/StarterAssets/Editor",
        "Assets/Flooded_Grounds/PostProcessing/Editor",
        "Assets/NatureStarterKit2/Editor",
        "Assets/NatureStarterKit2/Standard Assets/Effects/ImageEffects/Scripts",
    };

    private static volatile bool s_DownloadFinished;
    private static volatile bool s_DownloadSucceeded;
    private static string s_DownloadPath;
    private static string s_DownloadMessage;
    private static string s_ExpectedFinalPath;
    private static string s_TempDownloadDirectory;
    private static string s_TempDownloadPattern;
    private static DateTime s_DownloadDeadlineUtc;
    private static DateTime s_LastProgressLogUtc;
    private static long s_LastObservedSize = -1;
    private static int s_StableTicks;

    [MenuItem("HPR/Assets/Import Unity Package From Arg")]
    public static void ImportFromArgs()
    {
        var args = Environment.GetCommandLineArgs();
        string packagePath = null;
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "-assetPackage")
            {
                packagePath = args[i + 1];
                break;
            }
        }

        if (string.IsNullOrWhiteSpace(packagePath))
        {
            throw new Exception("Missing -assetPackage <path>");
        }

        ImportPackage(packagePath);
    }

    [MenuItem("HPR/Assets/Apply Known Compatibility Fixes")]
    public static void ApplyKnownCompatibilityFixes()
    {
        bool changed = false;
        foreach (var assetPath in KnownIncompatibleImportPaths)
        {
            if (!AssetDatabase.IsValidFolder(assetPath))
            {
                continue;
            }

            changed |= AssetDatabase.DeleteAsset(assetPath);
        }

        if (!changed)
        {
            Debug.Log("ASSETSTORE compatibility fixes: nothing to remove");
            return;
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        Debug.Log("ASSETSTORE compatibility fixes applied");
    }

    [MenuItem("HPR/Assets/Report Asset Store Loader Path")]
    public static void ReportAssetStoreLoaderPath()
    {
        var coreAssembly = typeof(Editor).Assembly;
        var assetStoreUtilsType = coreAssembly.GetType("UnityEditor.AssetStoreUtils", true);
        var loaderPathMethod = assetStoreUtilsType.GetMethod("GetLoaderPath", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        if (loaderPathMethod == null)
        {
            throw new Exception("Could not resolve AssetStoreUtils.GetLoaderPath");
        }

        var loaderPath = loaderPathMethod.Invoke(null, null) as string;
        Debug.Log($"ASSETSTORE loader path: {loaderPath}");
    }

    [MenuItem("HPR/Assets/Open Asset Store Package From Arg")]
    public static void OpenAssetStorePackageFromArgs()
    {
        var args = ParseArgs(Environment.GetCommandLineArgs());
        var packageToken = RequireArg(args, "assetPackage");
        var packageArgument = File.Exists(packageToken) ? Path.GetFullPath(packageToken) : packageToken;

        var coreAssembly = typeof(Editor).Assembly;
        var contextType = coreAssembly.GetType("UnityEditor.AssetStoreContext", true);
        var getInstance = contextType.GetMethod("GetInstance", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        var openInternal = contextType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)
            .FirstOrDefault(method => method.Name == "OpenPackageInternal" && method.GetParameters().Length == 1);
        var openPackage = contextType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)
            .FirstOrDefault(method => method.Name == "OpenPackage" && method.GetParameters().Length == 1);
        var openPackageWithAction = contextType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)
            .FirstOrDefault(method => method.Name == "OpenPackage" && method.GetParameters().Length == 2);
        if (getInstance == null || openInternal == null)
        {
            throw new Exception("Could not resolve AssetStoreContext.OpenPackageInternal");
        }

        var context = getInstance.Invoke(null, null);
        bool succeeded = false;

        var internalTarget = openInternal.IsStatic ? null : context;
        var internalResult = (bool)openInternal.Invoke(internalTarget, new object[] { packageArgument });
        Debug.Log($"ASSETSTORE open package internal arg={packageArgument} result={internalResult}");
        succeeded |= internalResult;

        if (!succeeded && openPackage != null)
        {
            var openTarget = openPackage.IsStatic ? null : context;
            var openResult = (bool)openPackage.Invoke(openTarget, new object[] { packageArgument });
            Debug.Log($"ASSETSTORE open package arg={packageArgument} result={openResult}");
            succeeded |= openResult;
        }

        if (!succeeded && openPackageWithAction != null)
        {
            var openTarget = openPackageWithAction.IsStatic ? null : context;
            var openResult = (bool)openPackageWithAction.Invoke(openTarget, new object[] { packageArgument, "import" });
            Debug.Log($"ASSETSTORE open package arg={packageArgument} action=import result={openResult}");
            succeeded |= openResult;
        }

        if (!succeeded)
        {
            throw new Exception($"AssetStoreContext.OpenPackage* returned false for {packageArgument}");
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
    }

    [MenuItem("HPR/Assets/Debug Asset Store Download")]
    public static void DebugAssetStoreDownloadFromArgs()
    {
        var args = ParseArgs(Environment.GetCommandLineArgs());
        if (!args.TryGetValue("assetId", out var assetIdValue))
        {
            throw new Exception("Missing -assetId <package id>");
        }

        var assetId = long.Parse(assetIdValue);
        var timeoutSeconds = args.TryGetValue("timeout", out var timeoutValue) ? int.Parse(timeoutValue) : 300;
        var shouldStartDownload = args.TryGetValue("startDownload", out var startValue) && bool.Parse(startValue);

        var coreAssembly = typeof(Editor).Assembly;
        var servicesContainerType = coreAssembly.GetType("UnityEditor.PackageManager.UI.Internal.ServicesContainer", true);
        var container = Activator.CreateInstance(servicesContainerType);
        servicesContainerType.GetMethod("Reload", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.Invoke(container, null);

        var resolveMethod = servicesContainerType.GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            .Single(method => method.Name == "Resolve" && method.IsGenericMethodDefinition && method.GetParameters().Length == 0);

        var downloadManagerType = coreAssembly.GetType("UnityEditor.PackageManager.UI.Internal.AssetStoreDownloadManager", true);
        var downloadManager = resolveMethod.MakeGenericMethod(downloadManagerType).Invoke(container, null);
        if (downloadManager == null)
        {
            throw new Exception("Could not resolve AssetStoreDownloadManager");
        }

        var getOperation = downloadManagerType.GetMethod("GetDownloadOperation", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var downloadMethod = downloadManagerType.GetMethod("Download", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic, null, new[] { typeof(long) }, null);

        if (shouldStartDownload)
        {
            Debug.Log($"Starting Asset Store download for product {assetId}");
            downloadMethod?.Invoke(downloadManager, new object[] { assetId });
        }

        var operationType = coreAssembly.GetType("UnityEditor.PackageManager.UI.Internal.AssetStoreDownloadOperation", true);
        var productIdProperty = operationType.GetProperty("productId", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var stateProperty = operationType.GetProperty("state", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var progressProperty = operationType.GetProperty("progressPercentage", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var errorProperty = operationType.GetProperty("errorMessage", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var newPathProperty = operationType.GetProperty("packageNewPath", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var oldPathProperty = operationType.GetProperty("packageOldPath", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var downloadInfoProperty = operationType.GetProperty("downloadInfo", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var inProgressProperty = operationType.GetProperty("isInProgress", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var inPauseProperty = operationType.GetProperty("isInPause", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);

        var deadline = DateTime.UtcNow.AddSeconds(timeoutSeconds);
        while (DateTime.UtcNow < deadline)
        {
            var operation = getOperation?.Invoke(downloadManager, new object[] { assetId });
            if (operation != null)
            {
                var state = stateProperty?.GetValue(operation);
                var progress = progressProperty?.GetValue(operation);
                var error = errorProperty?.GetValue(operation) as string;
                var isInProgress = (bool?)inProgressProperty?.GetValue(operation) ?? false;
                var isPaused = (bool?)inPauseProperty?.GetValue(operation) ?? false;
                var newPath = newPathProperty?.GetValue(operation) as string;
                var oldPath = oldPathProperty?.GetValue(operation) as string;
                var downloadInfo = downloadInfoProperty?.GetValue(operation);
                Debug.Log($"ASSETSTORE op product={productIdProperty?.GetValue(operation)} state={state} progress={progress} inProgress={isInProgress} paused={isPaused} newPath={newPath} oldPath={oldPath} error={error}");
                if (downloadInfo != null)
                {
                    foreach (var field in downloadInfo.GetType().GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
                    {
                        Debug.Log($"ASSETSTORE downloadInfo.{field.Name}={field.GetValue(downloadInfo)}");
                    }
                }

                if (!isInProgress && !string.IsNullOrWhiteSpace(newPath) && File.Exists(newPath))
                {
                    Debug.Log($"ASSETSTORE download complete at {newPath}");
                    return;
                }

                if (!string.IsNullOrWhiteSpace(error))
                {
                    throw new Exception($"Asset Store download failed: {error}");
                }
            }
            else
            {
                Debug.Log($"ASSETSTORE no active operation for {assetId}");
            }

            Thread.Sleep(1000);
        }

        throw new TimeoutException($"Timed out waiting for Asset Store download {assetId}");
    }

    [MenuItem("HPR/Assets/Direct Asset Store Context Download")]
    public static void DirectAssetStoreContextDownloadFromArgs()
    {
        var args = ParseArgs(Environment.GetCommandLineArgs());
        var assetId = RequireArg(args, "assetId");
        var assetUrl = RequireArg(args, "assetUrl");
        var assetKey = args.TryGetValue("assetKey", out var assetKeyValue) ? assetKeyValue : string.Empty;
        var publisher = RequireArg(args, "publisher");
        var category = RequireArg(args, "category");
        var packageName = RequireArg(args, "packageName");
        var timeoutSeconds = args.TryGetValue("timeout", out var timeoutValue) ? int.Parse(timeoutValue) : 300;

        var coreAssembly = AppDomain.CurrentDomain.GetAssemblies()
            .FirstOrDefault(assembly => assembly.GetType("UnityEditor.AssetStoreContext", false) != null)
            ?? typeof(Editor).Assembly;
        var contextType = coreAssembly.GetType("UnityEditor.AssetStoreContext", true);
        var contextMethods = contextType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static);
        var getInstance = contextMethods.FirstOrDefault(method => method.Name == "GetInstance" && method.GetParameters().Length == 0);
        var packageStorePath = contextMethods.FirstOrDefault(method => method.Name == "PackageStorePath" && method.GetParameters().Length == 5);
        var contextDownloadMethod = contextMethods.FirstOrDefault(method =>
            method.Name == "Download" &&
            method.GetParameters().Length == 7 &&
            method.GetParameters().FirstOrDefault()?.ParameterType == typeof(string));

        var context = getInstance?.Invoke(null, null);
        if (context == null || contextDownloadMethod == null)
        {
            foreach (var method in contextMethods.Where(method => method.Name.Contains("Download") || method.Name.Contains("Package") || method.Name.Contains("GetInstance")))
            {
                Debug.LogError($"ASSETSTORE context method candidate: {method}");
            }
            Debug.LogError($"ASSETSTORE contextType={contextType} getInstance={(getInstance != null)} context={(context != null)} packageStorePath={(packageStorePath != null)} contextDownloadMethod={(contextDownloadMethod != null)}");
            throw new Exception("Could not resolve Asset Store download API");
        }

        string[] destination = new[] { publisher, category, packageName };
        if (packageStorePath != null)
        {
            try
            {
                var guess = new[] { publisher, category, packageName, assetId, assetUrl };
                var result = packageStorePath.Invoke(context, guess) as string[];
                Debug.Log($"ASSETSTORE PackageStorePath({string.Join(", ", guess)}) => {(result == null ? "<null>" : string.Join(" | ", result))}");
                if (result != null && result.Length == 3)
                {
                    destination = result;
                    s_DownloadPath = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                        "unity3d",
                        "Asset Store-5.x",
                        destination[0],
                        destination[1],
                        destination[2] + ".unitypackage");
                    Debug.Log($"ASSETSTORE expected final path {s_DownloadPath}");
                }
            }
            catch (Exception exception)
            {
                Debug.LogWarning($"PackageStorePath probe failed: {exception}");
            }
        }

        s_DownloadFinished = false;
        s_DownloadSucceeded = false;
        s_ExpectedFinalPath = s_DownloadPath;
        s_TempDownloadDirectory = Path.GetDirectoryName(s_ExpectedFinalPath);
        s_TempDownloadPattern = $".*-{assetId}.tmp";
        s_DownloadDeadlineUtc = DateTime.UtcNow.AddSeconds(timeoutSeconds);
        s_LastProgressLogUtc = DateTime.MinValue;
        s_LastObservedSize = -1;
        s_StableTicks = 0;
        s_DownloadPath = string.Empty;
        s_DownloadMessage = string.Empty;

        var callbackType = contextDownloadMethod.GetParameters().Last().ParameterType;
        var callbackMethod = typeof(AssetStoreImportTools).GetMethod(nameof(OnAssetStoreContextDownloadDone), BindingFlags.Static | BindingFlags.NonPublic);
        var callback = Delegate.CreateDelegate(callbackType, callbackMethod);

        Debug.Log($"ASSETSTORE direct download start assetId={assetId} publisher={publisher} category={category} package={packageName} destination={string.Join("/", destination)}");
        var downloadTarget = contextDownloadMethod.IsStatic ? null : context;
        contextDownloadMethod.Invoke(downloadTarget, new object[] { assetId, assetUrl, assetKey, packageName, publisher, category, callback });
        EditorApplication.update -= PollAssetStoreDownload;
        EditorApplication.update += PollAssetStoreDownload;
    }

    public static void ImportPackage(string packagePath)
    {
        packagePath = Path.GetFullPath(packagePath);
        if (!File.Exists(packagePath))
        {
            throw new FileNotFoundException("Unity package not found", packagePath);
        }

        Debug.Log($"Importing unitypackage: {packagePath}");
        var importImmediatelyMethod = typeof(AssetDatabase).GetMethod(
            "ImportPackageImmediately",
            BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic,
            null,
            new[] { typeof(string) },
            null);
        var imported = importImmediatelyMethod != null && (bool)importImmediatelyMethod.Invoke(null, new object[] { packagePath });
        if (!imported)
        {
            Debug.LogWarning($"AssetDatabase.ImportPackageImmediately returned false for {packagePath}; falling back to PackageUtility.");
            var packageUtilityType = typeof(Editor).Assembly.GetType("UnityEditor.PackageUtility", true);
            var extractMethod = packageUtilityType.GetMethod(
                "ExtractAndPrepareAssetList",
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            var importMethod = packageUtilityType.GetMethod(
                "ImportPackageAssetsImmediately",
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            if (extractMethod == null || importMethod == null)
            {
                throw new Exception("Could not resolve PackageUtility fallback");
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
        AssetDatabase.Refresh();
        Debug.Log($"Import complete: {packagePath}");
    }

    [MenuItem("HPR/Assets/Report Third Party Roots")]
    public static void ReportThirdPartyRoots()
    {
        var roots = new DirectoryInfo(Application.dataPath)
            .GetDirectories()
            .Where(dir => dir.Name != "Data" && dir.Name != "Scenes" && dir.Name != "Editor")
            .Select(dir => dir.Name)
            .OrderBy(name => name)
            .ToArray();
        Debug.Log("Third-party roots: " + string.Join(", ", roots));
    }

    [MenuItem("HPR/Assets/Report Prefab Bounds")]
    public static void ReportPrefabBoundsFromArgs()
    {
        var args = ParseArgs(Environment.GetCommandLineArgs());
        var assetPath = RequireArg(args, "assetPath");
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
        if (prefab == null)
        {
            throw new Exception($"Could not load prefab at {assetPath}");
        }

        var instance = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
        if (instance == null)
        {
            throw new Exception($"Could not instantiate prefab at {assetPath}");
        }

        try
        {
            var renderers = instance.GetComponentsInChildren<Renderer>();
            var bounds = renderers.First().bounds;
            foreach (var renderer in renderers.Skip(1))
            {
                bounds.Encapsulate(renderer.bounds);
            }

            Debug.Log($"PREFAB {assetPath} position={instance.transform.position} rotation={instance.transform.rotation.eulerAngles} scale={instance.transform.localScale} bounds_center={bounds.center} bounds_size={bounds.size}");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static Dictionary<string, string> ParseArgs(IEnumerable<string> args)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        string pendingKey = null;
        foreach (var arg in args)
        {
            if (arg.StartsWith("-"))
            {
                pendingKey = arg.TrimStart('-');
                result[pendingKey] = "true";
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
        if (args.TryGetValue(key, out var value) && !string.IsNullOrWhiteSpace(value))
        {
            return value;
        }

        throw new Exception($"Missing -{key} <value>");
    }

    private static void PollAssetStoreDownload()
    {
        if (s_DownloadFinished)
        {
            FinishAssetStoreDownload();
            return;
        }

        if (!string.IsNullOrWhiteSpace(s_ExpectedFinalPath) && File.Exists(s_ExpectedFinalPath))
        {
            var info = new FileInfo(s_ExpectedFinalPath);
            if (info.Length == s_LastObservedSize && info.Length > 0)
            {
                s_StableTicks++;
                if (s_StableTicks >= 3)
                {
                    s_DownloadFinished = true;
                    s_DownloadSucceeded = true;
                    s_DownloadPath = s_ExpectedFinalPath;
                    s_DownloadMessage = $"stableSize={info.Length}";
                    FinishAssetStoreDownload();
                    return;
                }
            }
            else
            {
                s_LastObservedSize = info.Length;
                s_StableTicks = 0;
                Debug.Log($"ASSETSTORE final path size {info.Length}");
            }
        }
        else
        {
            var tempPath = FindActiveTempDownload();
            if (!string.IsNullOrWhiteSpace(tempPath))
            {
                var info = new FileInfo(tempPath);
                if (info.Length != s_LastObservedSize || DateTime.UtcNow - s_LastProgressLogUtc > TimeSpan.FromSeconds(15))
                {
                    s_LastObservedSize = info.Length;
                    s_LastProgressLogUtc = DateTime.UtcNow;
                    Debug.Log($"ASSETSTORE temp path size {info.Length} path={tempPath}");
                }
            }
        }

        if (DateTime.UtcNow >= s_DownloadDeadlineUtc)
        {
            s_DownloadFinished = true;
            s_DownloadSucceeded = false;
            s_DownloadMessage = $"Timed out waiting for direct Asset Store download {s_TempDownloadPattern}";
            FinishAssetStoreDownload();
        }
    }

    private static string FindActiveTempDownload()
    {
        if (string.IsNullOrWhiteSpace(s_TempDownloadDirectory) || string.IsNullOrWhiteSpace(s_TempDownloadPattern) || !Directory.Exists(s_TempDownloadDirectory))
        {
            return null;
        }

        return Directory.GetFiles(s_TempDownloadDirectory, s_TempDownloadPattern)
            .OrderByDescending(path => File.GetLastWriteTimeUtc(path))
            .FirstOrDefault();
    }

    private static void FinishAssetStoreDownload()
    {
        EditorApplication.update -= PollAssetStoreDownload;
        if (!s_DownloadSucceeded &&
            !string.IsNullOrWhiteSpace(s_ExpectedFinalPath) &&
            File.Exists(s_ExpectedFinalPath))
        {
            var info = new FileInfo(s_ExpectedFinalPath);
            if (info.Length > 0)
            {
                s_DownloadSucceeded = true;
                s_DownloadPath = s_ExpectedFinalPath;
                s_DownloadMessage = $"finalPathRecovered={info.Length}";
            }
        }
        Debug.Log($"ASSETSTORE direct download finished success={s_DownloadSucceeded} path={s_DownloadPath} message={s_DownloadMessage}");
        if (Application.isBatchMode)
        {
            EditorApplication.Exit(s_DownloadSucceeded ? 0 : 1);
        }
    }

    private static void OnAssetStoreContextDownloadDone(string downloadId, string destination, int bytes, int resultCode)
    {
        s_DownloadFinished = true;
        s_DownloadSucceeded = resultCode == 0 && !string.IsNullOrWhiteSpace(destination);
        if (!s_DownloadSucceeded &&
            !string.IsNullOrWhiteSpace(s_ExpectedFinalPath) &&
            File.Exists(s_ExpectedFinalPath))
        {
            var info = new FileInfo(s_ExpectedFinalPath);
            if (info.Length > 0)
            {
                s_DownloadSucceeded = true;
                destination = s_ExpectedFinalPath;
            }
        }

        s_DownloadPath = destination ?? string.Empty;
        s_DownloadMessage = $"downloadId={downloadId} bytes={bytes} result={resultCode}";
        Debug.Log($"ASSETSTORE direct callback downloadId={downloadId} destination={destination} bytes={bytes} result={resultCode}");
    }
}
