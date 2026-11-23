#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE consumer QA: actual native C# comparison against an actual built Player receipt.
public static class HprProbeQaCompare
{
    private static void Require(bool okay,string why)
    {if(!okay)throw new InvalidOperationException("HPR_PLAYER_PROBE_COMPARISON_FAIL:"+why);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        var folder=Environment.GetEnvironmentVariable("HPR_PROBE_QA_ROOT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(folder) &&
            folder.StartsWith(safe,StringComparison.Ordinal),"isolated_private_folder");
        var editorPath=Path.Combine(folder,"editor-original-baseline.json");
        var playerPath=Path.Combine(folder,"actual-player-receipt.json");
        var output=Path.Combine(folder,"actual-editor-versus-player-comparison.json");
        Require(File.Exists(editorPath) && File.Exists(playerPath) && !File.Exists(output),
            "nonrepeated_private_original_receipts");
        var editor=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(editorPath));
        var player=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(playerPath));
        HprReferenceInspector.Validate(editor);HprReferenceInspector.Validate(player);
        var result=HprReferenceInspector.Compare(editor,player);
        Require(result.status=="CONSISTENT_NULL_OR_UNSET_FIELDS" &&
            result.checkedCount==3 && result.playerMissingCaseIds.Length==0 &&
            result.playerSourceMissingCaseIds.Length==0 && result.otherDifferences.Length==0,"actual_original_reference_fields_match_expected_qa");
        var changed=JsonUtility.FromJson<HprReferenceReport>(JsonUtility.ToJson(player));
        var missing=changed.cases.Single(x=>x.id=="assigned-prefab");
        missing.status="REFERENCE_NULL_OR_UNSET";missing.referencedType="";missing.referencedName="";
        changed.assignedCount--;changed.missingCount++;
        changed.status="NULL_OR_UNSET_SELECTED_REFERENCE";
        var negative=HprReferenceInspector.Compare(editor,changed);
        Require(negative.status=="PLAYER_REFERENCE_LOSS_REPRODUCED" &&
            negative.playerMissingCaseIds.SequenceEqual(new[]{"assigned-prefab"}),
            "originally_assigned_reference_missing_in_synthetic_player_must_be_detected");
        if(editor.cases[0].sourceLookup.StartsWith("RESOURCES:",StringComparison.Ordinal))
        {
            var missingSource=JsonUtility.FromJson<HprReferenceReport>(JsonUtility.ToJson(player));
            var gone=missingSource.cases.Single(x=>x.id=="assigned-prefab");
            gone.status="SOURCE_NOT_LOADED";
            gone.assetName=gone.sourceLookup.Substring(10);
            gone.referencedType="";
            gone.referencedName="";
            missingSource.assignedCount--;
            missingSource.missingCount++;
            missingSource.status="NULL_OR_UNSET_SELECTED_REFERENCE";
            var missingCompare=HprReferenceInspector.Compare(editor,missingSource);
            Require(missingCompare.status=="PLAYER_SCRIPTABLEOBJECT_SOURCE_NOT_LOADED" &&
                missingCompare.playerSourceMissingCaseIds.SequenceEqual(new[]{"assigned-prefab"}) &&
                missingCompare.playerMissingCaseIds.Length==0,
                "explicit_source_not_loaded_separate_from_missing_prefab_field");
        }
        var malformed=JsonUtility.FromJson<HprReferenceReport>(JsonUtility.ToJson(changed));
        malformed.checkedCount=2;
        bool denied=false;
        try{HprReferenceInspector.Compare(editor,malformed);}catch(ArgumentException){denied=true;}
        Require(denied,"corrupt_player_report_must_be_rejected");
        using(var file=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file))writer.Write(JsonUtility.ToJson(result,true));
        Debug.Log("HPR_PLAYER_REFERENCE_REAL_EDITOR_VS_BUILT_PLAYER_NATIVE_PASS "+
            result.status+" checked="+result.checkedCount+
            " synthetic_missing_detected="+negative.playerMissingCaseIds.Length);
    }
}
#endif
