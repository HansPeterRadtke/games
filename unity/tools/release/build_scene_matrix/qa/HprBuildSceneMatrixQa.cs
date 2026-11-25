#if UNITY_EDITOR && UNITY_6000_1_OR_NEWER
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.BuildSceneMatrix;

// These mutations are private fixture creation ONLY, excluded from buyer package.
public static class HprBuildSceneMatrixQa
{
    const string Root = "Assets/HPRPrivateMatrixQA";
    static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
    static string Receipt => Environment.GetEnvironmentVariable("HPR_MATRIX_RECEIPT");
    static string Sha(string path) => Convert.ToBase64String(SHA256.Create().ComputeHash(File.ReadAllBytes(path)));

    public static void Export()
    {
        Require(Application.isBatchMode, "Private native exporter only");
        string archive = Environment.GetEnvironmentVariable("HPR_MATRIX_ARCHIVE");
        Require(!string.IsNullOrEmpty(archive) && !File.Exists(archive), "Fresh output archive required");
        AssetDatabase.ExportPackage("Assets/HPRBuildSceneMatrix", archive, ExportPackageOptions.Recurse);
        Require(File.Exists(archive) && new FileInfo(archive).Length > 0, "Package not created");
        Debug.Log("HPR_MATRIX_EXPORT_PASS " + archive);
    }

    private static string Scene(string name)
    {
        string path = Root + "/" + name + ".unity";
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        Require(EditorSceneManager.SaveScene(scene, path), "Fixture scene save failed");
        return path;
    }

    private static BuildProfile Profile(string name, bool over, EditorBuildSettingsScene[] scenes)
    {
        // Installed editor's internal factory used ONLY to construct real QA fixtures.
        var factory = typeof(BuildProfile).GetMethod("CreateInstance",
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static, null,
            new[] { typeof(BuildTarget), typeof(StandaloneBuildSubtarget) }, null);
        Require(factory != null, "Installed native fixture factory unavailable");
        var p = (BuildProfile)factory.Invoke(null, new object[] { BuildTarget.StandaloneLinux64, StandaloneBuildSubtarget.Player });
        Require(p != null, "No configured Build Profile");
        p.name = name;
        p.overrideGlobalScenes = over;
        p.scenes = scenes;
        AssetDatabase.CreateAsset(p, Root + "/" + name + ".asset");
        return p;
    }

    public static void Run()
    {
        Require(Application.isBatchMode && !AssetDatabase.IsValidFolder(Root) && BuildProfile.GetActiveBuildProfile() == null,
            "Fresh disposable buyer project required");
        Require(!string.IsNullOrEmpty(Receipt) && !File.Exists(Receipt), "Create-only receipt required");
        Directory.CreateDirectory(Root + "/A");
        Directory.CreateDirectory(Root + "/B");
        AssetDatabase.Refresh();
        string a = Scene("A/Start"), b = Scene("B/Start"), c = Scene("Level");
        var all = new[] { new EditorBuildSettingsScene(a, true), new EditorBuildSettingsScene(b, false),
            new EditorBuildSettingsScene(c, true) };
        EditorBuildSettings.globalScenes = all;
        var inherited = Profile("Inherited", false, new[] { new EditorBuildSettingsScene(b, true) });
        var custom = Profile("Override", true, new[] { new EditorBuildSettingsScene(c, true),
            new EditorBuildSettingsScene(a, true), new EditorBuildSettingsScene(b, true) });
        AssetDatabase.SaveAssets();
        BuildProfile.SetActiveBuildProfile(custom);
        AssetDatabase.SaveAssets();
        try
        {
            Require(BuildProfile.GetActiveBuildProfile() == custom, "Actual profile not active");
            string[] paths = { "ProjectSettings/EditorBuildSettings.asset", Root + "/Inherited.asset",
                Root + "/Override.asset", a, b, c };
            var before = paths.Select(Sha).ToArray();
            var profiles = HprSceneMatrix.Scan();
            var g = profiles.Single(p => p.Id == HprSceneMatrix.GlobalId);
            var i = profiles.Single(p => p.AssetPath == Root + "/Inherited.asset");
            var o = profiles.Single(p => p.AssetPath == Root + "/Override.asset");
            Require(g.Readable && i.Readable && o.Readable && o.Active && !g.Active, "Real lists not all readable");
            Require(g.Rows.Count == 3 && g.EnabledCount == 2 && g.First == a, "Global list incorrectly resolved");
            Require(i.Rows.Count == 3 && i.First == a && !i.Rows[1].Enabled &&
                HprSceneMatrix.Compare(g, i).All(d => !d.Different), "Inherited profile differs from actual global");
            Require(o.Rows.Count == 3 && o.EnabledCount == 3 && o.First == c, "Override list/order incorrectly resolved");
            var diff = HprSceneMatrix.Compare(g, o);
            Require(diff.Count == 3 && diff.All(d => d.Different), "Expected three actual differences");
            Require(diff.Single(d => d.Path == b).A == "Disabled" && diff.Single(d => d.Path == b).B == "#2",
                "Disabled scene confused with absence or wrong build index");
            Require(diff.Count(d => d.Warning && d.Issue.Contains("Ambiguous")) == 2,
                "Two different enabled scenes with same name not detected");
            Require(!diff.Any(d => d.Issue.Contains("Missing")), "Valid imported scene misclassified as missing");
            string csv = Path.ChangeExtension(Receipt, ".csv");
            HprSceneMatrix.ExportNewCsv(csv, g, o);
            string exported = Sha(csv);
            bool refused = false;
            try { HprSceneMatrix.ExportNewCsv(csv, g, o); } catch (IOException) { refused = true; }
            Require(refused && Sha(csv) == exported, "CSV overwrote an existing file");
            // Test deliberately absent and missing rows with explicit negative controls.
            var negative = new HprSceneProfile { Id = "negative" };
            negative.Rows.Add(new HprSceneRow { Path = "Assets/Nonexistent.unity", Guid = "", Name = "Nonexistent",
                Missing = true, Enabled = true, BuildIndex = 0 });
            var missing = HprSceneMatrix.Compare(g, negative).Single(d => d.Path == "Assets/Nonexistent.unity");
            Require(missing.A == "Absent" && missing.B == "#0" && missing.Warning, "Negative missing/absent comparison failed");
            Require(BuildProfile.GetActiveBuildProfile() == custom && paths.Select(Sha).SequenceEqual(before),
                "Read-only scan/export changed source assets, settings or active profile");
            string baselinePath = Path.ChangeExtension(Receipt, ".hpr-scenes");
            DateTimeOffset capture = DateTimeOffset.UtcNow;
            HprSceneBaseline.SaveNew(baselinePath, o, capture);
            string baselineHash = Sha(baselinePath);
            var baseline = HprSceneBaseline.Load(baselinePath);
            Require(baseline.Profile.Id == o.Id && baseline.CapturedUtc == capture &&
                !baseline.Profile.Active && HprSceneMatrix.Compare(baseline.Profile,o).All(d=>!d.Different),
                "Native scanned profile did not round-trip as historical reference");
            Require(BuildProfile.GetActiveBuildProfile() == custom && paths.Select(Sha).SequenceEqual(before),
                "Saving/loading reference changed the Unity project");

            // Change ONLY the disposable fixture's real profile, not any customer project.
            custom.scenes = new[] { new EditorBuildSettingsScene(a, true),
                new EditorBuildSettingsScene(c, true), new EditorBuildSettingsScene(b, false) };
            EditorUtility.SetDirty(custom);
            AssetDatabase.SaveAssets();
            var changedBefore = paths.Select(Sha).ToArray();
            var changed = HprSceneMatrix.Scan().Single(p=>p.Id == o.Id);
            var history = HprSceneMatrix.Compare(baseline.Profile, changed);
            Require(history.Count == 3 && history.All(d => d.Different) &&
                history.Single(d=>d.Path==b).A == "#2" && history.Single(d=>d.Path==b).B == "Disabled",
                "Historical reference failed to detect actual profile changes");
            Require(Sha(baselinePath) == baselineHash &&
                BuildProfile.GetActiveBuildProfile() == custom && paths.Select(Sha).SequenceEqual(changedBefore),
                "Historical comparison changed the saved baseline, current profile or project");

            File.WriteAllText(Receipt, "HPR_MATRIX_REAL_PROFILE_PASS\nActual global, inherited, override, enabled order, duplicate names, create-only CSV, read-only asset identity, missing/absent negative control, historical reference and actual changed profile comparison.\nUnity=" + Application.unityVersion);
            Debug.Log("HPR_MATRIX_REAL_PROFILE_PASS");
        }
        finally
        {
            BuildProfile.SetActiveBuildProfile(null);
        }
    }
}
#endif
