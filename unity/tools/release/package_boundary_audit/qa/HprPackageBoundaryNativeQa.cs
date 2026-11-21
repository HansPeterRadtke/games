#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using HPR.PackageBoundary;
using UnityEditor;
using UnityEngine;

// PRIVATE native consumer QA, never distributed with the product.
public static class HprPackageBoundaryNativeQa
{
    static void Check(bool okay, string why)
    { if (!okay) throw new InvalidOperationException("HPR_BOUNDARY_QA_FAIL " + why); }

    static void AddMaterial(string folder, string name, Shader shader)
    {
        AssetDatabase.CreateAsset(new Material(shader), folder + "/" + name + ".mat");
    }

    static void AddPrefab(string folder, string name, string materialPath)
    {
        var obj = GameObject.CreatePrimitive(PrimitiveType.Cube);
        try
        {
            obj.name = name;
            var render = obj.GetComponent<Renderer>();
            render.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            Check(render.sharedMaterial != null, "fixture material not found " + materialPath);
            var saved = PrefabUtility.SaveAsPrefabAsset(obj, folder + "/" + name + ".prefab");
            Check(saved != null, "prefab did not save");
        }
        finally { UnityEngine.Object.DestroyImmediate(obj); }
    }

    public static void Run()
    {
        string evidence = Environment.GetEnvironmentVariable("HPR_BOUNDARY_QA_OUT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(evidence) &&
            Path.IsPathRooted(evidence) &&
            evidence.StartsWith("/data/var/marketplace-account-setup/unity-20261121-afternoon/", StringComparison.Ordinal) &&
            !Directory.Exists(evidence) && !File.Exists(evidence), "fresh QA evidence path required");
        const string root = "Assets/HPRBoundaryPrivateFixture";
        const string outside = "Assets/HPRBoundaryOutsideFixture";
        Check(!AssetDatabase.IsValidFolder(root) && !AssetDatabase.IsValidFolder(outside),
            "QA fixtures already exist; disposable fresh project required");
        Directory.CreateDirectory(evidence);
        AssetDatabase.CreateFolder("Assets", "HPRBoundaryPrivateFixture");
        AssetDatabase.CreateFolder("Assets", "HPRBoundaryOutsideFixture");
        var shader = Shader.Find("Standard") ?? Shader.Find("Sprites/Default") ?? Shader.Find("Unlit/Color");
        Check(shader != null, "no default Unity shader available");
        AddMaterial(outside, "OutsideOne", shader);
        AddMaterial(outside, "OutsideTwo", shader);
        AddMaterial(root, "Inside", shader);
        AddPrefab(root, "UsesOutsideOne", outside + "/OutsideOne.mat");
        AddPrefab(root, "UsesOutsideTwo", outside + "/OutsideTwo.mat");
        AddPrefab(root, "UsesInside", root + "/Inside.mat");
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        var report = HprPackageBoundaryScanner.Scan(root);
        Check(report != null && report.assetsChecked >= 4, "did not scan all fixture assets");
        Check(report.externalAssets >= 2 && report.status == "REVIEW_EXTERNAL_DEPENDENCIES",
            "missing outside dependencies or incorrectly classified clean");
        Check(report.findings.Any(f => f.category == "EXTERNAL_ASSET" &&
              f.asset.EndsWith("UsesOutsideOne.prefab") && f.dependency.EndsWith("OutsideOne.mat")),
              "first real prefab outside-material dependency absent");
        Check(report.findings.Any(f => f.category == "EXTERNAL_ASSET" &&
              f.asset.EndsWith("UsesOutsideTwo.prefab") && f.dependency.EndsWith("OutsideTwo.mat")),
              "second real prefab outside-material dependency absent");
        Check(!report.findings.Any(f => f.dependency.EndsWith("Inside.mat")),
              "false-positive for dependency inside selected export root");
        var capped = HprPackageBoundaryScanner.Scan(root, 1, 100);
        Check(capped.incomplete && capped.status == "INCOMPLETE", "asset cap failed open");
        var findingsCapped = HprPackageBoundaryScanner.Scan(root, 100, 1);
        Check(findingsCapped.incomplete && findingsCapped.status == "INCOMPLETE",
            "findings cap failed open");
        var absent = HprPackageBoundaryScanner.Scan("Assets/HPRPackageBoundary");
        Check(absent.status == "NO_RESOLVED_EXTERNAL_DEPENDENCIES_FOUND" && !absent.incomplete,
            "original buyer package contains unexpected explicit cross-boundary references");
        bool invalidRejected = false;
        try { HprPackageBoundaryScanner.Scan("Assets"); }
        catch (ArgumentException) { invalidRejected = true; }
        Check(invalidRejected, "full project root was not rejected");
        string output = Path.Combine(evidence, "native-boundary-report.json");
        HprPackageBoundaryScanner.ExportNewJson(report, output);
        string first = File.ReadAllText(output);
        Check(first.Contains("EXTERNAL_ASSET") && first.Contains("OutsideOne.mat"),
              "JSON report does not describe actual finding");
        bool overwriteRejected = false;
        try { HprPackageBoundaryScanner.ExportNewJson(report, output); }
        catch (IOException) { overwriteRejected = true; }
        Check(overwriteRejected && File.ReadAllText(output) == first,
            "existing evidence overwritten");
        File.WriteAllText(Path.Combine(evidence, "receipt.txt"),
            "real_prefab_external_dependency_one=PASS\n" +
            "real_prefab_external_dependency_two=PASS\n" +
            "contained_dependency_no_false_positive=PASS\n" +
            "asset_truncation_fails_closed=PASS\n" +
            "finding_truncation_fails_closed=PASS\n" +
            "vendor_root_scans_clean=PASS\n" +
            "root_validation=PASS\n" +
            "json_export_create_only=PASS\n" +
            "unity_version=" + Application.unityVersion + "\n");
        Debug.Log("HPR_BOUNDARY_NATIVE_QA_PASS unity=" + Application.unityVersion +
                  " outside=" + report.externalAssets + " assets=" + report.assetsChecked);
    }
}
#endif
