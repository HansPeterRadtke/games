#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE actual built Player-only missing-link negative, not a claimed Unity bug.
public static class HprProbeQaCompareLoss
{
    private static void Require(bool pass,string reason)
    {if(!pass)throw new InvalidOperationException("HPR_PROBE_NATIVE_PLAYER_LOSS_QA_FAILURE:"+reason);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string root=Environment.GetEnvironmentVariable("HPR_PROBE_QA_ROOT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(root) &&
            root.StartsWith(safe,StringComparison.Ordinal),"private_actual_buyer_test");
        string e=Path.Combine(root,"editor-original-baseline.json");
        string p=Path.Combine(root,"actual-player-receipt.json");
        string output=Path.Combine(root,"real-player-reference-loss-comparison.json");
        Require(File.Exists(e) && File.Exists(p) && !File.Exists(output),"create_only_original_receipts");
        var baseline=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(e));
        var player=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(p));
        var verdict=HprReferenceInspector.Compare(baseline,player);
        Require(verdict.status=="PLAYER_REFERENCE_LOSS_REPRODUCED" &&
            verdict.playerMissingCaseIds.SequenceEqual(new[]{"assigned-prefab"}) &&
            verdict.otherDifferences.Length==0,
            "actual_player_only_original_reference_loss_detected");
        using(var file=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file))writer.Write(JsonUtility.ToJson(verdict,true));
        Debug.Log("HPR_PLAYER_REFERENCE_REAL_PLAYER_LOSS_NEGATIVE_NATIVE_PASS "+
            verdict.status+" missing="+verdict.playerMissingCaseIds[0]);
    }
}
#endif
