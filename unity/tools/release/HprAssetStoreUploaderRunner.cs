using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

public static class HprAssetStoreUploaderRunner
{
    public static void RunFromEnvironment()
    {
        var resultPath = Environment.GetEnvironmentVariable("HPR_UPLOAD_RESULT") ?? "/tmp/hpr_asset_store_upload_result.txt";
        try
        {
            Run(resultPath);
        }
        catch (Exception ex)
        {
            Append(resultPath, "result=FAIL");
            Append(resultPath, "error=" + Sanitize(ex.GetBaseException().Message));
            Debug.LogException(ex);
            throw;
        }
    }

    private static void Run(string resultPath)
    {
        File.WriteAllText(resultPath, string.Empty);
        var packagePath = RequireEnv("HPR_UPLOAD_PACKAGE_PATH");
        var expectedName = RequireEnv("HPR_UPLOAD_EXPECTED_NAME");
        var expectedPortalId = RequireEnv("HPR_UPLOAD_PORTAL_ID");
        var execute = string.Equals(Environment.GetEnvironmentVariable("HPR_UPLOAD_EXECUTE"), "1", StringComparison.Ordinal);

        if (!File.Exists(packagePath))
            throw new FileNotFoundException("Upload package not found", packagePath);

        var toolsAssembly = AppDomain.CurrentDomain.GetAssemblies()
            .FirstOrDefault(a => string.Equals(a.GetName().Name, "asset-store-tools-editor", StringComparison.Ordinal));
        if (toolsAssembly == null)
            throw new InvalidOperationException("Asset Store Tools editor assembly is not loaded");

        var cloudUser = CloudProjectSettings.userName ?? string.Empty;
        var cloudToken = CloudProjectSettings.accessToken ?? string.Empty;
        Append(resultPath, "cloud_user=" + Sanitize(cloudUser));
        Append(resultPath, "cloud_auth_available=" + (!string.IsNullOrEmpty(cloudToken) && !string.Equals(cloudUser, "anonymous", StringComparison.OrdinalIgnoreCase)));
        if (string.IsNullOrEmpty(cloudToken) || string.Equals(cloudUser, "anonymous", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Unity cloud login is unavailable in this Editor session");

        var clientType = RequireType(toolsAssembly, "AssetStoreTools.Api.AssetStoreClient");
        var apiType = RequireType(toolsAssembly, "AssetStoreTools.Api.AssetStoreApi");
        var cloudAuthType = RequireType(toolsAssembly, "AssetStoreTools.Api.CloudTokenAuthentication");
        var uploadSettingsType = RequireType(toolsAssembly, "AssetStoreTools.Api.UnityPackageUploadSettings");
        var uploaderType = RequireType(toolsAssembly, "AssetStoreTools.Api.UnityPackageUploader");

        var client = Activator.CreateInstance(clientType);
        var api = Activator.CreateInstance(apiType, client);
        var cloudAuth = Activator.CreateInstance(cloudAuthType, cloudToken);

        var authResponse = InvokeTaskResult(api, "Authenticate", cloudAuth, CancellationToken.None);
        if (!GetBool(authResponse, "Success"))
            throw new InvalidOperationException("Asset Store cloud authentication failed: " + GetExceptionMessage(authResponse));
        Append(resultPath, "asset_store_auth=OK");

        var packagesResponse = InvokeTaskResult(api, "GetPackages", CancellationToken.None);
        if (!GetBool(packagesResponse, "Success"))
            throw new InvalidOperationException("Fetching publisher packages failed: " + GetExceptionMessage(packagesResponse));

        var packages = GetProperty(packagesResponse, "Packages") as IEnumerable;
        if (packages == null)
            throw new InvalidOperationException("Publisher package list is unavailable");

        object target = null;
        var exactNameCount = 0;
        foreach (var package in packages)
        {
            var name = GetString(package, "Name");
            var packageId = GetString(package, "PackageId");
            var versionId = GetString(package, "VersionId");
            var status = GetString(package, "Status");
            if (!string.Equals(name, expectedName, StringComparison.Ordinal))
                continue;

            exactNameCount++;
            Append(resultPath, "candidate_name=" + Sanitize(name));
            Append(resultPath, "candidate_package_id=" + Sanitize(packageId));
            Append(resultPath, "candidate_version_id=" + Sanitize(versionId));
            Append(resultPath, "candidate_status=" + Sanitize(status));

            var idMatches = string.Equals(packageId, expectedPortalId, StringComparison.Ordinal) ||
                            string.Equals(versionId, expectedPortalId, StringComparison.Ordinal);
            if (idMatches && string.Equals(status, "draft", StringComparison.OrdinalIgnoreCase))
            {
                if (target != null)
                    throw new InvalidOperationException("More than one exact draft matched the requested portal id");
                target = package;
            }
        }

        Append(resultPath, "exact_name_candidates=" + exactNameCount);
        if (target == null)
            throw new InvalidOperationException("No exact draft matched both expected name and portal id");

        var targetPackageId = GetString(target, "PackageId");
        var targetVersionId = GetString(target, "VersionId");
        Append(resultPath, "target_package_id=" + Sanitize(targetPackageId));
        Append(resultPath, "target_version_id=" + Sanitize(targetVersionId));
        Append(resultPath, "package_size_bytes=" + new FileInfo(packagePath).Length);

        if (!execute)
        {
            Append(resultPath, "result=DRY_RUN_OK");
            Debug.Log("HPR Asset Store uploader dry run passed");
            return;
        }

        var settings = Activator.CreateInstance(uploadSettingsType);
        SetProperty(settings, "VersionId", targetVersionId);
        SetProperty(settings, "UnityPackagePath", packagePath);
        SetProperty(settings, "RootGuid", string.Empty);
        SetProperty(settings, "RootPath", string.Empty);
        SetProperty(settings, "ProjectPath", packagePath);
        var uploader = Activator.CreateInstance(uploaderType, settings);

        var lastBucket = -1;
        var progress = new Progress<float>(value =>
        {
            var bucket = (int)(value / 10f);
            if (bucket == lastBucket) return;
            lastBucket = bucket;
            Append(resultPath, "upload_progress=" + value.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture));
        });

        Append(resultPath, "upload_started=true");
        var uploadResponse = InvokeTaskResult(api, "UploadPackage", uploader, progress, CancellationToken.None);
        var statusValue = GetProperty(uploadResponse, "Status");
        Append(resultPath, "upload_status=" + Sanitize(statusValue == null ? string.Empty : statusValue.ToString()));
        if (!GetBool(uploadResponse, "Success"))
            throw new InvalidOperationException("Asset Store upload failed: " + GetExceptionMessage(uploadResponse));

        Append(resultPath, "result=UPLOAD_OK");
        Debug.Log("HPR Asset Store upload completed successfully");
    }

    private static Type RequireType(Assembly assembly, string name)
    {
        var type = assembly.GetType(name, false);
        if (type == null) throw new TypeLoadException("Missing type: " + name);
        return type;
    }

    private static object InvokeTaskResult(object target, string name, params object[] args)
    {
        var methods = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
            .Where(m => m.Name == name && m.GetParameters().Length == args.Length).ToArray();
        if (methods.Length != 1)
            throw new MissingMethodException(target.GetType().FullName, name + "(" + args.Length + ")");
        var task = methods[0].Invoke(target, args) as Task;
        if (task == null) throw new InvalidOperationException(name + " did not return Task");
        task.GetAwaiter().GetResult();
        var resultProperty = task.GetType().GetProperty("Result", BindingFlags.Public | BindingFlags.Instance);
        return resultProperty == null ? null : resultProperty.GetValue(task, null);
    }

    private static object GetProperty(object obj, string name)
    {
        if (obj == null) return null;
        var prop = obj.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        return prop == null ? null : prop.GetValue(obj, null);
    }

    private static void SetProperty(object obj, string name, object value)
    {
        var prop = obj.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (prop == null) throw new MissingMemberException(obj.GetType().FullName, name);
        prop.SetValue(obj, value, null);
    }

    private static bool GetBool(object obj, string name)
    {
        var value = GetProperty(obj, name);
        return value is bool && (bool)value;
    }

    private static string GetString(object obj, string name)
    {
        var value = GetProperty(obj, name);
        return value == null ? string.Empty : value.ToString();
    }

    private static string GetExceptionMessage(object response)
    {
        var ex = GetProperty(response, "Exception") as Exception;
        return ex == null ? "unknown error" : Sanitize(ex.GetBaseException().Message);
    }

    private static string RequireEnv(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrEmpty(value)) throw new InvalidOperationException("Missing environment variable " + name);
        return value;
    }

    private static void Append(string path, string line)
    {
        File.AppendAllText(path, line + Environment.NewLine);
    }

    private static string Sanitize(string value)
    {
        return (value ?? string.Empty).Replace("\r", " ").Replace("\n", " ");
    }
}
