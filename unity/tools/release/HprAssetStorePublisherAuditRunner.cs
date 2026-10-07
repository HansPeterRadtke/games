using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
public static class HprAssetStorePublisherAuditRunner
{
    private const string ControlPath = "/data/tmp/hpr_assetstore_sale/publisher_audit.control";
    private static bool _running;
    private static double _nextCheck;

    static HprAssetStorePublisherAuditRunner()
    {
        if (!Application.isBatchMode)
            EditorApplication.update += Poll;
    }

    private static async void Poll()
    {
        if (_running || EditorApplication.timeSinceStartup < _nextCheck)
            return;
        _nextCheck = EditorApplication.timeSinceStartup + 0.5;
        if (!File.Exists(ControlPath))
            return;

        _running = true;
        var claimed = ControlPath + ".running";
        string resultPath = "/data/tmp/hpr_assetstore_sale/publisher_audit_result.txt";
        try
        {
            if (File.Exists(claimed)) File.Delete(claimed);
            File.Move(ControlPath, claimed);
            var cfg = File.ReadAllLines(claimed)
                .Where(x => !string.IsNullOrWhiteSpace(x) && !x.TrimStart().StartsWith("#"))
                .Select(x => new { Line = x, Index = x.IndexOf('=') })
                .Where(x => x.Index > 0)
                .ToDictionary(x => x.Line.Substring(0, x.Index).Trim(), x => x.Line.Substring(x.Index + 1));
            if (cfg.TryGetValue("result_path", out var rp) && !string.IsNullOrEmpty(rp)) resultPath = rp;
            File.WriteAllText(resultPath, string.Empty);
            await Audit(cfg, resultPath);
        }
        catch (Exception ex)
        {
            Append(resultPath, "result=FAIL");
            Append(resultPath, "error=" + Sanitize(ex.GetBaseException().Message));
            Debug.LogException(ex);
        }
        finally
        {
            try { if (File.Exists(claimed)) File.Delete(claimed); } catch { }
            _running = false;
        }
    }

    private static async Task Audit(System.Collections.Generic.Dictionary<string,string> cfg, string resultPath)
    {
        var expectedName = Require(cfg, "expected_name");
        var expectedPortalId = Require(cfg, "portal_id");
        var cloudUser = CloudProjectSettings.userName ?? string.Empty;
        var cloudToken = CloudProjectSettings.accessToken ?? string.Empty;
        Append(resultPath, "cloud_user=" + Sanitize(cloudUser));
        Append(resultPath, "cloud_token_available=" + (!string.IsNullOrEmpty(cloudToken)));
        if (string.IsNullOrEmpty(cloudToken))
            throw new InvalidOperationException("Unity Hub access token is unavailable in this Editor session");

        var asm = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == "asset-store-tools-editor");
        if (asm == null) throw new InvalidOperationException("Asset Store Tools editor assembly is not loaded");
        var client = Activator.CreateInstance(RequireType(asm, "AssetStoreTools.Api.AssetStoreClient"));
        var api = Activator.CreateInstance(RequireType(asm, "AssetStoreTools.Api.AssetStoreApi"), client);
        var auth = Activator.CreateInstance(RequireType(asm, "AssetStoreTools.Api.CloudTokenAuthentication"), cloudToken);

        var authResponse = await InvokeTaskResultAsync(api, "Authenticate", auth, CancellationToken.None);
        if (!GetBool(authResponse, "Success"))
            throw new InvalidOperationException("Asset Store authentication failed: " + GetExceptionMessage(authResponse));
        var user = GetProperty(authResponse, "User");
        Append(resultPath, "asset_store_auth=OK");
        Append(resultPath, "publisher_id=" + Sanitize(GetString(user, "PublisherId")));
        Append(resultPath, "unity_user_name=" + Sanitize(GetString(user, "Name")));
        Append(resultPath, "publisher_username=" + Sanitize(GetString(user, "Username")));

        var packagesResponse = await InvokeTaskResultAsync(api, "GetPackages", CancellationToken.None);
        if (!GetBool(packagesResponse, "Success"))
            throw new InvalidOperationException("Fetching publisher packages failed: " + GetExceptionMessage(packagesResponse));
        var packages = GetProperty(packagesResponse, "Packages") as IEnumerable;
        if (packages == null) throw new InvalidOperationException("Publisher package list is unavailable");

        object target = null;
        int matches = 0;
        foreach (var package in packages)
        {
            var name = GetString(package, "Name");
            var packageId = GetString(package, "PackageId");
            var versionId = GetString(package, "VersionId");
            if (!string.Equals(name, expectedName, StringComparison.Ordinal)) continue;
            matches++;
            Append(resultPath, "candidate_package_id=" + Sanitize(packageId));
            Append(resultPath, "candidate_version_id=" + Sanitize(versionId));
            Append(resultPath, "candidate_status=" + Sanitize(GetString(package, "Status")));
            Append(resultPath, "candidate_category=" + Sanitize(GetString(package, "Category")));
            Append(resultPath, "candidate_modified=" + Sanitize(GetString(package, "Modified")));
            Append(resultPath, "candidate_size=" + Sanitize(GetString(package, "Size")));
            Append(resultPath, "candidate_icon_available=" + (!string.IsNullOrEmpty(GetString(package, "IconUrl"))));
            if (packageId == expectedPortalId || versionId == expectedPortalId) target = package;
        }
        Append(resultPath, "exact_name_candidates=" + matches);
        if (target == null) throw new InvalidOperationException("Expected package draft was not found");

        var versions = await InvokeTaskResultAsync(api, "GetPackageUploadedVersions", target, CancellationToken.None);
        Append(resultPath, "uploaded_versions_query_success=" + GetBool(versions, "Success"));
        if (!GetBool(versions, "Success"))
            Append(resultPath, "uploaded_versions_error=" + Sanitize(GetExceptionMessage(versions)));
        else
        {
            foreach (var p in versions.GetType().GetProperties(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance))
            {
                if (p.Name == "Exception" || p.Name == "Success") continue;
                object v = null;
                try { v = p.GetValue(versions, null); } catch { }
                if (v is IEnumerable sequence && !(v is string))
                {
                    var items = sequence.Cast<object>()
                        .Select(item => item == null ? string.Empty : item.ToString())
                        .Where(item => !string.IsNullOrEmpty(item));
                    Append(resultPath, "uploaded_versions_" + p.Name.ToLowerInvariant() + "=" + Sanitize(string.Join(",", items)));
                }
                else if (v != null)
                {
                    Append(resultPath, "uploaded_versions_" + p.Name.ToLowerInvariant() + "=" + Sanitize(v.ToString()));
                }
            }
        }
        Append(resultPath, "result=AUDIT_OK");
    }

    private static string Require(System.Collections.Generic.Dictionary<string,string> cfg, string key)
    {
        if (!cfg.TryGetValue(key, out var value) || string.IsNullOrEmpty(value))
            throw new InvalidOperationException("Missing control key: " + key);
        return value;
    }
    private static Type RequireType(Assembly asm, string name) => asm.GetType(name, false) ?? throw new TypeLoadException("Missing type: " + name);
    private static async Task<object> InvokeTaskResultAsync(object target, string name, params object[] args)
    {
        var methods = target.GetType().GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)
            .Where(m => m.Name == name && m.GetParameters().Length == args.Length).ToArray();
        if (methods.Length != 1) throw new MissingMethodException(target.GetType().FullName, name + "(" + args.Length + ")");
        var task = methods[0].Invoke(target, args) as Task;
        if (task == null) throw new InvalidOperationException(name + " did not return Task");
        await task;
        return task.GetType().GetProperty("Result", BindingFlags.Public|BindingFlags.Instance)?.GetValue(task, null);
    }
    private static object GetProperty(object obj, string name) => obj?.GetType().GetProperty(name, BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)?.GetValue(obj, null);
    private static bool GetBool(object obj, string name) => GetProperty(obj, name) is bool b && b;
    private static string GetString(object obj, string name) => GetProperty(obj, name)?.ToString() ?? string.Empty;
    private static string GetExceptionMessage(object response) => (GetProperty(response, "Exception") as Exception)?.GetBaseException().Message ?? "unknown error";
    private static void Append(string path, string line) => File.AppendAllText(path, line + Environment.NewLine);
    private static string Sanitize(string value) => (value ?? string.Empty).Replace("\r", " ").Replace("\n", " ");
}
