// Private cleanroom test fixture, never included in buyer archive.
// Tests the actual Editor diagnostic without opening or changing scenes.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using HPR.GameplaySuite;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

public static class HprSuiteGuidePackageRegistryFixture
{
    public static void Run()
    {
        string path = Environment.GetEnvironmentVariable("HPR_SUITE_GUIDE_TEST_RECEIPT");
        if (string.IsNullOrWhiteSpace(path) || File.Exists(path))
            throw new InvalidOperationException("New private guide test receipt required");
        string expected = Environment.GetEnvironmentVariable("HPR_SUITE_EXPECT_CONFLICT");
        bool conflictExpected = string.Equals(expected, "yes", StringComparison.Ordinal);
        if (!conflictExpected && !string.Equals(expected, "no", StringComparison.Ordinal))
            throw new InvalidOperationException("Expected package state must be yes or no");
        var guide = ScriptableObject.CreateInstance<HprSuiteIntegrationGuide>();
        try
        {
            Type type = typeof(HprSuiteIntegrationGuide);
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
            type.GetField("status", flags).SetValue(guide, new Label());
            type.GetField("advice", flags).SetValue(guide, new Label());
            type.GetMethod("RefreshStatus", flags).Invoke(guide, null);
            string report = (string)type.GetField("lastReport", flags).GetValue(guide);
            if (report == null || report.Contains("Package registry check: Package Manager"))
                throw new InvalidOperationException("Registered package inspection unavailable");
            if (!report.Contains("Runtime modules: 10/10"))
                throw new InvalidOperationException("Imported suite modules not all present");
            bool detected = report.Contains("Registered duplicate standalone modules: com.hpr.save");
            if (detected != conflictExpected)
                throw new InvalidOperationException("Wrong registered package result: " + report);
            string state = ((Label)type.GetField("status", flags).GetValue(guide)).text;
            if (conflictExpected && !state.Contains("DUPLICATE MODULES"))
                throw new InvalidOperationException("The buyer does not see a duplicate warning");
            if (!conflictExpected && state.Contains("DUPLICATE MODULES"))
                throw new InvalidOperationException("False duplicate warning");
            File.WriteAllText(path, (conflictExpected ? "CONFLICT_PASS" : "CLEAN_PASS") +
                "\n" + state + "\n" + report + "\n");
            Debug.Log("HPR_SUITE_GUIDE_REGISTRY_PASS " + (conflictExpected ? "duplicate" : "clean"));
        }
        finally { UnityEngine.Object.DestroyImmediate(guide); }
    }
}
#endif
