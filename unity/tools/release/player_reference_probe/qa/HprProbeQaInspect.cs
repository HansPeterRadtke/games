#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;
using HPR.PlayerReferenceProbe;

public static class HprProbeQaInspect
{
    public static void Run()
    {
        string path="Assets/HPRProbeTest/Resources/";
        var good=AssetDatabase.LoadAssetAtPath<HprProbeQaItem>(path+"OriginalAssignedItem.asset");
        var unset=AssetDatabase.LoadAssetAtPath<HprProbeQaItem>(path+"OriginalEmptyItem.asset");
        if(good==null || unset==null)throw new InvalidOperationException("Missing original private fixtures");
        var checks=new[]{
            new HprReferenceCase{id="assigned-prefab",source=good,fieldName="itemPrefab"},
            new HprReferenceCase{id="private-serialized",source=good,fieldName="privatePrefab"},
            new HprReferenceCase{id="intentionally-null",source=unset,fieldName="itemPrefab"}
        };
        var report=HprReferenceInspector.Inspect(checks,"EDITOR");
        Debug.Log("HPR_PROBE_QA_ORIGINAL_INSPECTION_DIAG "+JsonUtility.ToJson(report));
    }
}
#endif
