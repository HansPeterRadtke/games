#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using HPR.PublisherVersionMatrix;

// Private QA: the altered GUID and second version are synthetic NEGATIVE cases only.
// Real cross-version source scans must be separately obtained from actual Editors.
public static class HprPublisherVersionCompareNativeQa
{
    private static void Require(bool condition,string name)
    {if(!condition)throw new InvalidOperationException("HPR_PUBLISHER_DIFF_QA_FAILURE:"+name);}

    public static void Run()
    {
        string output=Environment.GetEnvironmentVariable("HPR_PUBLISHER_DIFF_QA_OUT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(output) &&
            output.StartsWith("/data/var/marketplace-account-setup/",StringComparison.Ordinal) &&
            !File.Exists(output),"private_output_precondition");
        var root="Assets/HPRPublisherVersionMatrix";
        var actual=HprPublisherVersionScan.Scan(root);
        Require(!actual.incomplete && actual.assetCount>=4,"real_vendor_asset_scan");
        var other=JsonUtility.FromJson<HprVersionReceipt>(JsonUtility.ToJson(actual));
        other.unityVersion="synthetic-different-version-for-negative-QA";
        var matched=HprVersionReceiptCompare.Compare(actual,other);
        Require(matched.status=="MATCHED_IMPORT_METADATA" &&
            matched.guidChanges.Length==0 && matched.dependencyChanges.Length==0,
            "same_real_import_source_in_fake_second_version_is_equal");
        other.assets[0].guid="ffffffffffffffffffffffffffffffff";
        var changed=HprVersionReceiptCompare.Compare(actual,other);
        Require(changed.status=="REVIEW_IMPORT_DIFFERENCES" && changed.guidChanges.Length==1,
            "synthetic_guid_mismatch_is_flagged_not_clean");
        bool rejected=false;
        try{HprVersionReceiptCompare.Compare(actual,actual);}catch(ArgumentException){rejected=true;}
        Require(rejected,"same_version_refused");
        other=JsonUtility.FromJson<HprVersionReceipt>(JsonUtility.ToJson(actual));
        other.unityVersion="synthetic-different-version-for-negative-QA";
        other.rootFolders="Assets/SomeOtherPackage";
        rejected=false;
        try{HprVersionReceiptCompare.Compare(actual,other);}catch(ArgumentException){rejected=true;}
        Require(rejected,"wrong_package_scopes_rejected");
        HprVersionReceiptCompare.ExportNew(changed,output);
        rejected=false;
        try{HprVersionReceiptCompare.ExportNew(changed,output);}catch(IOException){rejected=true;}
        Require(rejected,"comparison_export_create_only");
        Debug.Log("HPR_PUBLISHER_VERSION_COMPARE_NATIVE_PASS "+Application.unityVersion+
            " original_asset_count="+actual.assetCount);
    }
}
#endif
