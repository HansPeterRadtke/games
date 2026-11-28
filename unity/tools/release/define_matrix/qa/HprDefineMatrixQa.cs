// PRIVATE QA fixture. Excluded from customer .unitypackage. Tests actual Unity
// profiles without changing a customer's installed packages or build settings.
#if UNITY_EDITOR && UNITY_6000_1_OR_NEWER
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEngine;
using HPR.DefineMatrix;

public static class HprDefineMatrixQa
{
    private const string FixtureRoot = "Assets/HPRPrivateDefineMatrixQA";
    private static string Sha(string path) => Convert.ToBase64String(SHA256.Create().ComputeHash(File.ReadAllBytes(path)));
    private static void Require(bool ok, string issue) { if (!ok) throw new InvalidOperationException(issue); }

    public static void Export()
    {
        Require(Application.isBatchMode, "Private export fixture only");
        string output = Environment.GetEnvironmentVariable("HPR_DEFINES_ARCHIVE");
        Require(!string.IsNullOrEmpty(output) && !File.Exists(output), "New private export path required");
        AssetDatabase.ExportPackage("Assets/HPRDefineMatrix", output, ExportPackageOptions.Recurse);
        Require(new FileInfo(output).Length > 5000, "Unity package not created correctly");
        Debug.Log("HPR_DEFINES_EXPORT_PASS");
    }

    private static BuildProfile Create(string name, string[] symbols)
    {
        // Installed Unity 6 internal factory is used for *test fixture creation
        // only*. Production product uses ONLY documented, public Editor APIs.
        var factory = typeof(BuildProfile).GetMethod("CreateInstance",
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static, null,
            new[] { typeof(BuildTarget), typeof(StandaloneBuildSubtarget) }, null);
        Require(factory != null, "Private test factory not available in this Editor version");
        var asset = (BuildProfile)factory.Invoke(null,
            new object[] { BuildTarget.StandaloneLinux64, StandaloneBuildSubtarget.Player });
        Require(asset != null, "Native Unity did not create a profile");
        asset.name = name;
        asset.scriptingDefines = symbols;
        AssetDatabase.CreateAsset(asset, FixtureRoot + "/" + name + ".asset");
        return asset;
    }

    public static void Run()
    {
        Require(Application.isBatchMode && !AssetDatabase.IsValidFolder(FixtureRoot), "Fresh buyer project required");
        string receipt = Environment.GetEnvironmentVariable("HPR_DEFINES_RECEIPT");
        Require(!string.IsNullOrEmpty(receipt) && !File.Exists(receipt), "New private receipt required");
        Directory.CreateDirectory(FixtureRoot);
        AssetDatabase.Refresh();
        var release = Create("HPR_Release_Test", new[] { "FEATURE_SHARED", "RELEASE_BUILD" });
        var demo = Create("HPR_Demo_Test", new[] { "FEATURE_SHARED", "DEMO_BUILD" });
        AssetDatabase.SaveAssets();
        string beforeRelease = Sha(FixtureRoot + "/HPR_Release_Test.asset");
        string beforeDemo = Sha(FixtureRoot + "/HPR_Demo_Test.asset");
        string manifest = Sha("Packages/manifest.json");
        string active = BuildProfile.GetActiveBuildProfile() == null ? "none" :
            AssetDatabase.GetAssetPath(BuildProfile.GetActiveBuildProfile());

        var all = HprDefineMatrix.Scan();
        var a = all.Single(x => x.Path == FixtureRoot + "/HPR_Release_Test.asset");
        var b = all.Single(x => x.Path == FixtureRoot + "/HPR_Demo_Test.asset");
        Require(a.Readable && b.Readable && a.Symbols.Count == 2 && b.Symbols.Count == 2,
            "Real Build Profile scriptingDefines were not read correctly");
        var diff = HprDefineMatrix.Compare(a, b);
        Require(diff.Count == 3 && diff.Count(x => x.Status == "Both") == 1 &&
            diff.Single(x => x.Symbol == "RELEASE_BUILD").Status == "Left only" &&
            diff.Single(x => x.Symbol == "DEMO_BUILD").Status == "Right only",
            "Real profile difference results incorrect");

        // Source-side invalid/duplicate handling must not quietly normalize a
        // user's serialized setting and claim the raw configuration was clean.
        var malformed = new DefineProfile();
        HprDefineMatrix.ParseDeclared(malformed, new[] { "FEATURE_SHARED", "FEATURE_SHARED", "", "NOT LEGAL" });
        Require(malformed.Symbols.Count == 1 && malformed.Warnings.Count == 3,
            "Malformed or duplicate define warnings missing");
        string csv = Path.ChangeExtension(receipt, ".csv");
        HprDefineMatrix.ExportNewCsv(csv, a, b);
        Require(File.ReadAllText(csv).Contains("RELEASE_BUILD") &&
                File.ReadAllText(csv).Contains("DEMO_BUILD"), "Export missing expected differences");
        string warningCsv = Path.Combine(Path.GetDirectoryName(receipt), "define-warnings-private.csv");
        HprDefineMatrix.ExportNewCsv(warningCsv, malformed, b);
        Require(File.ReadAllText(warningCsv).Contains("Reference warning") &&
                File.ReadAllText(warningCsv).Contains("Repeated scripting define"),
                "CSV concealed invalid or repeated scripting defines");
        var unsafeProfile = new DefineProfile { Name = "Untrusted", Id = "untrusted",
            Path = " ＝HYPERLINK(\"https://untrusted.invalid\")" };
        unsafeProfile.Symbols.Add("VALID_DEFINE");
        string unsafeCsv = Path.Combine(Path.GetDirectoryName(receipt), "unsafe-define-report.csv");
        HprDefineMatrix.ExportNewCsv(unsafeCsv, unsafeProfile, b);
        Require(File.ReadAllText(unsafeCsv).Contains("\"' ＝HYPERLINK"),
            "Export does not guard spreadsheet formula-like profile path");
        string beforeCsv = Sha(csv);
        bool refused = false;
        try { HprDefineMatrix.ExportNewCsv(csv, a, b); }
        catch (IOException) { refused = true; }
        Require(refused && Sha(csv) == beforeCsv, "Create-only export overwrote an existing report");

        // Capture a true release-like reference without changing any profile;
        // then verify it survives a subsequent actual saved-profile change.
        string baselinePath = Path.ChangeExtension(receipt, ".hpr-defines");
        DateTimeOffset captured = DateTimeOffset.UtcNow;
        HprDefineBaseline.SaveNew(baselinePath, b, captured);
        string baselineSha = Sha(baselinePath);
        string forbiddenProjectFile = "ProjectSettings/HprForbiddenReference.hpr-defines";
        bool refusedProjectLocation = false;
        try { HprDefineBaseline.SaveNew(forbiddenProjectFile, b, captured); }
        catch (IOException) { refusedProjectLocation = true; }
        Require(refusedProjectLocation && !File.Exists(forbiddenProjectFile),
            "Reference writer allowed unexpected in-project ProjectSettings file");
        var historical = HprDefineBaseline.Load(baselinePath);
        Require(historical.Profile.Id == b.Id && historical.Profile.Path == b.Path &&
                historical.Profile.HistoricalCapturedUtc.HasValue &&
                historical.CapturedUtc == captured &&
                HprDefineMatrix.Compare(historical.Profile, b).All(d => d.Left == d.Right),
                "Native saved scripting-define reference failed roundtrip");
        bool refusedSavedReference = false;
        try { HprDefineBaseline.SaveNew(baselinePath, b, captured); }
        catch (IOException) { refusedSavedReference = true; }
        Require(refusedSavedReference && Sha(baselinePath) == baselineSha,
                "Native saved reference silently overwrote an existing file");
        string invalidBaseline = Path.Combine(Path.GetDirectoryName(receipt), "invalid-define-reference.hpr-defines");
        File.WriteAllText(invalidBaseline, "{\"format\":\"not-our-format\"}");
        bool invalidRefused = false;
        try { HprDefineBaseline.Load(invalidBaseline); }
        catch (InvalidDataException) { invalidRefused = true; }
        Require(invalidRefused, "Malformed external reference was incorrectly accepted");

        // Instantiate the real installed Editor window, not a fake UI-model.
        var window = HprDefineMatrixWindow.OpenWindow();
        Require(window != null, "Unity Editor window failed to open");
        try
        {
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
            typeof(HprDefineMatrixWindow).GetField("baseline", flags).SetValue(window, historical);
            var reflected = (HprDefineBaseline)typeof(HprDefineMatrixWindow)
                .GetField("baseline", flags).GetValue(window);
            Require(reflected != null && reflected.Profile.Id == b.Id,
                "Native EditorWindow did not accept the saved historical reference");
        }
        finally { window.Close(); }
        Require(beforeRelease == Sha(FixtureRoot + "/HPR_Release_Test.asset") &&
                beforeDemo == Sha(FixtureRoot + "/HPR_Demo_Test.asset") &&
                manifest == Sha("Packages/manifest.json") &&
                active == (BuildProfile.GetActiveBuildProfile() == null ? "none" :
                   AssetDatabase.GetAssetPath(BuildProfile.GetActiveBuildProfile())),
                "Read-only scan, UI or export mutated Unity settings or test source");
        // Deliberate saved profile update on this disposable buyer fixture.
        demo.scriptingDefines = new[] { "FEATURE_SHARED", "RELEASE_BUILD" };
        EditorUtility.SetDirty(demo);
        AssetDatabase.SaveAssets();
        var updated = HprDefineMatrix.Scan().Single(x => x.Path == FixtureRoot + "/HPR_Demo_Test.asset");
        var changed = HprDefineMatrix.Compare(historical.Profile, updated);
        Require(changed.Count == 3 &&
            changed.Single(x => x.Symbol == "DEMO_BUILD").Status == "Left only" &&
            changed.Single(x => x.Symbol == "RELEASE_BUILD").Status == "Right only",
            "Native historical reference missed an actual subsequent define change");
        string historyCsv = Path.Combine(Path.GetDirectoryName(receipt), "historical-define-delta.csv");
        HprDefineMatrix.ExportNewCsv(historyCsv, historical.Profile, updated);
        string exportedHistory = File.ReadAllText(historyCsv);
        Require(exportedHistory.Contains("Reference captured UTC") &&
                exportedHistory.Contains("Reference asset identity changed") &&
                exportedHistory.Contains("DEMO_BUILD") && exportedHistory.Contains("RELEASE_BUILD") &&
                Sha(baselinePath) == baselineSha && manifest == Sha("Packages/manifest.json"),
                "Historical CSV omitted provenance or changed original saved reference");
        File.WriteAllText(receipt, "HPR_DEFINES_NATIVE_PASS\n" +
            "Unity=" + Application.unityVersion + "\n" +
            "profiles=2\nshared=1\nleft_only=1\nright_only=1\n" +
            "malformed_warnings=3\ncreate_only_csv=PASS\ncsv_formula_guard=PASS\nwindow_opened=PASS\n" +
            "saved_reference_roundtrip=PASS\nproject_write_refused=PASS\n" +
            "reference_overwrite_refused=PASS\n" +
            "malformed_reference_rejected=PASS\nactual_profile_change_detected=PASS\n" +
            "historical_csv_includes_provenance=PASS\n" +
            "original_assets_unchanged_before_deliberate_fixture_change=PASS\n");
        Debug.Log("HPR_DEFINES_NATIVE_PASS");
    }
}
#endif
