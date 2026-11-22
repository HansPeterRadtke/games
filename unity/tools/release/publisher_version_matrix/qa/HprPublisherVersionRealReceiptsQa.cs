#if UNITY_EDITOR
using System;
using System.IO;
using UnityEngine;
using HPR.PublisherVersionMatrix;

// PRIVATE genuine two-native-version comparator acceptance. No buyer source writes.
public static class HprPublisherVersionRealReceiptsQa
{
    private static void Require(bool yes,string rule)
    { if(!yes)throw new InvalidOperationException("HPR_MATRIX_REAL_VERSION_COMPARE_FAILURE:"+rule); }

    public static void Run()
    {
        string first=Environment.GetEnvironmentVariable("HPR_MATRIX_REAL_FIRST")??"";
        string second=Environment.GetEnvironmentVariable("HPR_MATRIX_REAL_SECOND")??"";
        string output=Environment.GetEnvironmentVariable("HPR_MATRIX_REAL_COMPARISON_OUT")??"";
        string root="/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1/";
        Require(Application.isBatchMode && first.StartsWith(root,StringComparison.Ordinal) &&
            second.StartsWith(root,StringComparison.Ordinal) &&
            output.StartsWith(root,StringComparison.Ordinal) && Path.IsPathRooted(output) &&
            !File.Exists(output) && first!=second,"original_immutable_private_inputs");
        var a=HprVersionReceiptCompare.ReadReceipt(first);
        var b=HprVersionReceiptCompare.ReadReceipt(second);
        Require(a.unityVersion=="2022.3.22f1" && b.unityVersion=="6000.6.8f1" &&
            a.assetCount==18 && b.assetCount==18,"real_version_pair_and_original_FBX_assets");
        var result=HprVersionReceiptCompare.Compare(a,b);
        Require(result.status=="MATCHED_IMPORT_METADATA" &&
            result.missingFromSecond.Length==0 && result.newInSecond.Length==0 &&
            result.guidChanges.Length==0 && result.dependencyChanges.Length==0,
            "original_buyer_assets_same_metadata_in_two_real_editors");
        HprVersionReceiptCompare.ExportNew(result,output);
        bool refused=false;
        try{HprVersionReceiptCompare.ExportNew(result,output);}catch(IOException){refused=true;}
        Require(refused,"refuse_replace_existing_report");
        Debug.Log("HPR_MATRIX_REAL_TWO_EDITOR_COMPARE_PASS source_assets="+a.assetCount);
    }
}
#endif
