#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;
using HPR.PublisherVersionMatrix;

// Private QA, NEVER a buyer asset: native editor runner for authentic imported Unity packages.
public static class HprPublisherVersionMatrixQa
{
    private static void Require(bool ok,string rule)
    { if(!ok) throw new InvalidOperationException("HPR_MATRIX_QA_FAIL:"+rule); }
    public static void Run()
    {
        string roots=Environment.GetEnvironmentVariable("HPR_MATRIX_QA_ROOTS")??"";
        string output=Environment.GetEnvironmentVariable("HPR_MATRIX_QA_OUT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(output) &&
            output.StartsWith("/data/var/marketplace-account-setup/",StringComparison.Ordinal) &&
            !File.Exists(output),"private_create_only_output");
        var result=HprPublisherVersionScan.Scan(roots);
        Require(!result.incomplete && result.assetCount>10 &&
            result.status=="SNAPSHOT_COMPLETE" &&
            result.assets.All(x=>x.guid.Length==32) &&
            result.assets.Any(x=>x.path.Contains("HprAnimationImportPreflight.cs")),
            "real_original_multiple_publisher_assets");
        Require(HprPublisherVersionScan.ValidateRoots(roots).Length==3,
            "three_original_vendor_roots_only");
        HprPublisherVersionScan.ExportNew(result,output);
        bool refused=false;
        try{HprPublisherVersionScan.ExportNew(result,output);}catch(IOException){refused=true;}
        Require(refused && new FileInfo(output).Length>100,
            "create_only_output_refuses_overwrite");
        Debug.Log("HPR_PUBLISHER_VERSION_MATRIX_NATIVE_PASS "+
            Application.unityVersion+" assets="+result.assetCount);
    }
}
#endif
