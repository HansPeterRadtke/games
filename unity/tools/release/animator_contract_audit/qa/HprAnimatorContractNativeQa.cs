#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using HPR.AnimatorContract;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class HprAnimatorContractNativeQa
{
    private const string BrokenPath = "Assets/HprAnimatorQaBroken.controller";
    private const string GoodPath = "Assets/HprAnimatorQaGood.controller";
    private static void Check(bool valid, string message)
    { if (!valid) throw new InvalidOperationException("ANIMATOR_AUDIT_QA: " + message); }

    private static string Hash(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "");
    }

    private static AnimatorController MakeController(string path, bool broken)
    {
        var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
        Check(controller != null, "Controller creation failed " + path);
        controller.AddParameter("Walking", AnimatorControllerParameterType.Bool);
        controller.AddParameter("Speed", AnimatorControllerParameterType.Float);
        var root = controller.layers[0].stateMachine;
        var idle = root.AddState("Idle");
        var walk = root.AddState("Walk");
        var go = idle.AddTransition(walk);
        go.hasExitTime = false;
        if (broken)
        {
            go.AddCondition(AnimatorConditionMode.If, 0f, "DeletedParameter");
            go.AddCondition(AnimatorConditionMode.If, 0f, "Speed");
            walk.speedParameterActive = true;
            walk.speedParameter = "MissingSpeed";
            walk.mirrorParameterActive = true;
            walk.mirrorParameter = "Speed"; // A Float is invalid for mirror's Bool value.
            var nested = root.AddStateMachine("Nested Combat");
            var nestedAttack = nested.AddState("Attack");
            var nestedAny = nested.AddAnyStateTransition(nestedAttack);
            nestedAny.AddCondition(AnimatorConditionMode.If, 0f, "DeletedNested");
            nestedAttack.cycleOffsetParameterActive = true;
            nestedAttack.cycleOffsetParameter = "MissingCycleOffset";
            nestedAttack.timeParameterActive = true;
            nestedAttack.timeParameter = "Walking"; // A Bool is invalid for normalized time.
            var any = root.AddAnyStateTransition(walk);
            any.AddCondition(AnimatorConditionMode.If, 0f, "DeletedAnyState");
            var tree = new BlendTree { name = "BrokenBlend", blendType = BlendTreeType.Simple1D,
                blendParameter = "DeletedBlendSpeed" };
            AssetDatabase.AddObjectToAsset(tree, controller);
            idle.motion = tree;
            EditorUtility.SetDirty(tree);
        }
        else
        {
            go.AddCondition(AnimatorConditionMode.If, 0f, "Walking");
            var back = walk.AddTransition(idle);
            back.AddCondition(AnimatorConditionMode.Less, 0.1f, "Speed");
            walk.speedParameterActive = true;
            walk.speedParameter = "Speed";
            walk.mirrorParameterActive = true;
            walk.mirrorParameter = "Walking";
            var tree = new BlendTree { name = "ValidBlend", blendType = BlendTreeType.Simple1D,
                blendParameter = "Speed" };
            AssetDatabase.AddObjectToAsset(tree, controller);
            idle.motion = tree;
            EditorUtility.SetDirty(tree);
        }
        EditorUtility.SetDirty(controller);
        AssetDatabase.SaveAssets();
        return controller;
    }

    public static void Run()
    {
        string dir = Environment.GetEnvironmentVariable("HPR_ANIM_QA_OUT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(dir) &&
              dir.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal) &&
              !Directory.Exists(dir) && !File.Exists(dir), "Fresh private QA output required");
        Check(AssetDatabase.LoadAssetAtPath<AnimatorController>(BrokenPath) == null &&
              AssetDatabase.LoadAssetAtPath<AnimatorController>(GoodPath) == null,
              "Test fixtures must not already exist");
        Directory.CreateDirectory(dir);
        var broken = MakeController(BrokenPath, true);
        var good = MakeController(GoodPath, false);
        string firstHash = Hash(BrokenPath);
        string secondHash = Hash(GoodPath);
        var bad = HprAnimatorContractAudit.ScanController(broken, BrokenPath);
        var clean = HprAnimatorContractAudit.ScanController(good, GoodPath);
        Debug.Log("HPR_ANIM_QA_BAD_RESULT " + bad.status + " " +
                  string.Join(",", bad.findings.Select(x => x.rule + ":" + x.parameter)));
        Debug.Log("HPR_ANIM_QA_GOOD_RESULT " + clean.status + " count=" + clean.definiteFindings);
        Check(bad.findings.Any(x => x.rule == "MISSING_PARAMETER" && x.parameter == "DeletedParameter"),
              "Missed deliberately invalid transition condition");
        Check(bad.findings.Any(x => x.rule == "PARAMETER_TYPE_MISMATCH" && x.parameter == "Speed"),
              "Missed deliberately incompatible float-as-boolean condition");
        Check(bad.findings.Any(x => x.rule == "MISSING_PARAMETER" && x.parameter == "MissingSpeed"),
              "Missed deliberately stale state speed parameter");
        Check(bad.findings.Any(x => x.rule == "MISSING_PARAMETER" && x.parameter == "DeletedNested"),
              "Missed nested state-machine transition");
        Check(bad.findings.Any(x => x.rule == "MISSING_PARAMETER" && x.parameter == "MissingCycleOffset"),
              "Missed nested state cycle-offset parameter");
        Check(bad.findings.Any(x => x.rule == "MISSING_PARAMETER" && x.parameter == "DeletedAnyState"),
              "Missed root Any State transition");
        Check(bad.findings.Any(x => x.rule == "MISSING_PARAMETER" && x.parameter == "DeletedBlendSpeed"),
              "Missed broken Blend Tree parameter binding");
        Check(bad.findings.Any(x => x.rule == "STATE_PARAMETER_TYPE_MISMATCH" &&
            x.parameter == "Speed" && x.scope.EndsWith("/Mirror", StringComparison.Ordinal)),
            "Missed mirror state Float/Bool mismatch");
        Check(bad.findings.Any(x => x.rule == "STATE_PARAMETER_TYPE_MISMATCH" &&
            x.parameter == "Walking" && x.scope.EndsWith("/Time", StringComparison.Ordinal)),
            "Missed normalized time state Bool/Float mismatch");
        Check(clean.status == "NO_ISSUES_IN_CHECKED_CONTRACTS" && clean.definiteFindings == 0,
              "Valid controller produced false positives");
        var project = HprAnimatorContractAudit.ScanProject();
        Check(project.controllersChecked >= 2 && project.definiteFindings >= 3 &&
              project.status == "ISSUES_FOUND", "Real project search missed bad controller");
        Check(firstHash == Hash(BrokenPath) && secondHash == Hash(GoodPath),
              "Audit modified an Animator asset");
        string exportPath = Path.Combine(dir, "user-export.json");
        HprAnimatorContractAudit.SaveReportFresh(bad, exportPath);
        string exported = File.ReadAllText(exportPath);
        Check(exported.Contains("DeletedParameter"), "Explicit JSON report lost a finding");
        bool refusedOverwrite = false;
        try { HprAnimatorContractAudit.SaveReportFresh(clean, exportPath); }
        catch (IOException) { refusedOverwrite = true; }
        Check(refusedOverwrite && File.ReadAllText(exportPath) == exported,
              "JSON report export overwrote an existing report");
        File.WriteAllText(Path.Combine(dir, "broken.json"), JsonUtility.ToJson(bad, true));
        File.WriteAllText(Path.Combine(dir, "valid.json"), JsonUtility.ToJson(clean, true));
        File.WriteAllText(Path.Combine(dir, "project.json"), JsonUtility.ToJson(project, true));
        File.WriteAllText(Path.Combine(dir, "receipt.txt"),
            "native_qa=PASS\nmissing_condition=PASS\ncondition_type_mismatch=PASS\n" +
            "missing_active_speed=PASS\nnested_transition=PASS\n" +
            "nested_cycle_offset=PASS\nany_state_transition=PASS\n" +
            "blend_tree_parameter=PASS\nstate_mirror_requires_bool=PASS\n" +
            "state_time_requires_float=PASS\nvalid_controller=PASS\nwhole_project=PASS\n" +
            "original_controller_bytes_unchanged=PASS\n" +
            "manual_export_creates_new_json_only=PASS\n");
        Debug.Log("HPR_ANIMATOR_CONTRACT_NATIVE_QA_PASS");
    }
}
#endif
