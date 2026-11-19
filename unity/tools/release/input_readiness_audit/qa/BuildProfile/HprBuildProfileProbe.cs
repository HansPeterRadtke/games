#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEngine;
using HPR.InputReadiness;

// Private, disposable Unity project test. Never included in the buyer archive.
public static class HprBuildProfileProbe
{
    private const string PathInProject = "Assets/HPRPrivateInputQaProfile.asset";
    public static void Run()
    {
        if (!Application.isBatchMode || !string.IsNullOrEmpty(AssetDatabase.AssetPathToGUID(PathInProject)) ||
            BuildProfile.GetActiveBuildProfile() != null)
            throw new InvalidOperationException("Fresh isolated project with no active custom Build Profile required");
        Debug.Log("HPR_BUILD_PROFILE_BEFORE mode=" +
            HprInputReadinessAudit.Analyze(Directory.GetParent(Application.dataPath).FullName).inputHandling);
        // Unity 6.6's supported public BuildProfile API cannot create a configured
        // profile in batchmode. Use its installed internal factory in this PRIVATE
        // test only, never in the shipped auditor.
        var factory = typeof(BuildProfile).GetMethod("CreateInstance",
            BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public, null,
            new[] { typeof(BuildTarget), typeof(StandaloneBuildSubtarget) }, null);
        if (factory == null) throw new InvalidOperationException("Installed Unity lacks the profile factory");
        var profile = (BuildProfile)factory.Invoke(null,
            new object[] { BuildTarget.StandaloneLinux64, StandaloneBuildSubtarget.Player });
        if (profile == null) throw new InvalidOperationException("Configured profile factory returned null");
        Debug.Log("HPR_BUILD_PROFILE_CREATED target=" + profile.name);
        profile.name = "HPR PRIVATE input QA build profile";
        AssetDatabase.CreateAsset(profile, PathInProject);
        AssetDatabase.SaveAssets();
        try
        {
            BuildProfile.SetActiveBuildProfile(profile);
            var active = BuildProfile.GetActiveBuildProfile();
            if (active == null)
                throw new InvalidOperationException("SetActiveBuildProfile did not activate the private custom profile");
            var result = HprInputReadinessAudit.Analyze(Directory.GetParent(Application.dataPath).FullName);
            Debug.Log("HPR_BUILD_PROFILE_ACTUAL_MODE=" + result.inputHandling +
                " status=" + result.result + " active=" + result.activeBuildProfile +
                " flags=" + string.Join(",", result.findings.Select(x => x.rule)));
            if (result.inputHandling != "Unknown" ||
                !result.findings.Any(x => x.rule == "ACTIVE_BUILD_PROFILE_OVERRIDE") ||
                result.result != "RISKS_FOUND")
                throw new InvalidOperationException("Auditor did not fail closed with an actual active custom profile");
            Debug.Log("HPR_BUILD_PROFILE_FAIL_CLOSED_REAL_UNITY_PASS");
        }
        finally
        {
            // Return to platform profile inside the disposable project; never
            // leave a custom profile selected after the QA process exits.
            BuildProfile.SetActiveBuildProfile(null);
            Debug.Log("HPR_BUILD_PROFILE_AFTER cleared=" + (BuildProfile.GetActiveBuildProfile() == null));
        }
    }
}
#endif
