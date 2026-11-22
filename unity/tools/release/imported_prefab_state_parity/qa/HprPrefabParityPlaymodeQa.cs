#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE native buyer test for Unity 6.6 Domain Reload disabled.
// Not part of the original version-matrix buyer package.
public static class HprPrefabParityPlaymodeQa
{
    private static bool savedEnabled,started,entered,exited,completed;
    private static EnterPlayModeOptions savedOptions;
    private static DateTime begun;
    private static string before;
    private static string output;
    private static int errors;
    private static string firstError;
    private const string OriginalPrefabs="Assets/HPRFbxClipIdentity/Samples/Prefabs/OriginalMotionTeachingPrefab.prefab;"+
        "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab;"+
        "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab";

    private static void Require(bool okay,string label)
    {if(!okay)throw new InvalidOperationException("HPR_PREFAB_PLAYMODE_FAILURE:"+label);}

    public static void Run()
    {
        output=Environment.GetEnvironmentVariable("HPR_PREFAB_PLAYMODE_OUT")??"";
        Require(Application.isBatchMode && Application.unityVersion.StartsWith("6000.6.",StringComparison.Ordinal) &&
            Path.IsPathRooted(output) &&
            output.StartsWith("/data/var/marketplace-account-setup/unity-prefab-state-parity-20261122-wave59/",StringComparison.Ordinal) &&
            !File.Exists(output),"private_new_receipt");
        var receipt=HprPrefabStateScan.Scan(OriginalPrefabs);
        Require(!receipt.incomplete && receipt.valuesCaptured>=100 && receipt.unsupportedComponents==0,"original_native_three_prefabs_covered_scan");
        before=JsonUtility.ToJson(receipt,false);
        savedEnabled=EditorSettings.enterPlayModeOptionsEnabled;
        savedOptions=EditorSettings.enterPlayModeOptions;
        EditorSettings.enterPlayModeOptionsEnabled=true;
        EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;
        Require(EditorSettings.enterPlayModeOptionsEnabled &&
            EditorSettings.enterPlayModeOptions==EnterPlayModeOptions.DisableDomainReload,
            "domain_reload_disabled_setting_applied");
        started=true;begun=DateTime.UtcNow;
        Application.logMessageReceived += Log;
        EditorApplication.playModeStateChanged += State;
        EditorApplication.update += Tick;
        EditorApplication.delayCall += () => {if(!completed)EditorApplication.isPlaying=true;};
        Debug.Log("HPR_PREFAB_PLAYMODE_STARTED");
    }

    private static void Log(string message,string trace,LogType type)
    {
        if(type==LogType.Error || type==LogType.Assert || type==LogType.Exception)
        {errors++;if(firstError==null)firstError=message;}
    }

    private static void State(PlayModeStateChange state)
    {
        if(!started||completed)return;
        if(state==PlayModeStateChange.EnteredPlayMode)
        {
            entered=true;Debug.Log("HPR_PREFAB_PLAYMODE_ENTERED");
            EditorApplication.delayCall += () => {if(!completed)EditorApplication.isPlaying=false;};
        }
        else if(state==PlayModeStateChange.EnteredEditMode && entered)
        {
            exited=true;Debug.Log("HPR_PREFAB_PLAYMODE_EXITED");
            EditorApplication.delayCall += Complete;
        }
    }

    private static void Tick()
    {if(started&&!completed && (DateTime.UtcNow-begun).TotalSeconds>150)Complete();}

    private static void Complete()
    {
        if(completed)return;completed=true;
        Application.logMessageReceived-=Log;
        EditorApplication.playModeStateChanged-=State;
        EditorApplication.update-=Tick;
        try
        {
            Require(entered&&exited,"real_enter_and_exit_observed");
            Require(errors==0,"no_console_errors_"+(firstError??""));
            var after=HprPrefabStateScan.Scan(OriginalPrefabs);
            Require(!after.incomplete && before==JsonUtility.ToJson(after,false),
                "original_loaded_prefab_state_identical_before_after_playmode");
            using(var file=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(file))
            {
                writer.WriteLine("unity_version="+Application.unityVersion);
                writer.WriteLine("actual_enter_and_exit_Play_Mode=PASS");
                writer.WriteLine("Domain_Reload_disabled=PASS");
                writer.WriteLine("original_imported_vendor_scan_unchanged=PASS");
                writer.WriteLine("Unity_console_errors=0");
                writer.WriteLine("batchmode_QA_not_human_GUI_acceptance=TRUE");
            }
            Debug.Log("HPR_PREFAB_PLAYMODE_NATIVE_PASS");
            EditorApplication.Exit(0);
        }
        catch(Exception ex)
        {
            Debug.LogError("HPR_PREFAB_PLAYMODE_NATIVE_FAIL "+ex.GetType().Name+": "+ex.Message);
            EditorApplication.Exit(13);
        }
        finally
        {
            EditorSettings.enterPlayModeOptions=savedOptions;
            EditorSettings.enterPlayModeOptionsEnabled=savedEnabled;
        }
    }
}
#endif
