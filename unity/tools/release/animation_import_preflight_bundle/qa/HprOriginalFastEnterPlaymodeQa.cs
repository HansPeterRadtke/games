#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using HPR.AnimationImportPreflight;

// Private first-party buyer compatibility QA for official Unity 6.6
// domain-reload-disabled Play Mode requirement. NEVER a buyer asset.
public static class HprOriginalFastEnterPlaymodeQa
{
    private static string receipt;
    private static bool previousOptionsEnabled;
    private static EnterPlayModeOptions previousOptions;
    private static bool entered;
    private static bool exited;
    private static bool started;
    private static bool finished;
    private static DateTime startedUtc;
    private static string originalState;
    private static int logErrors;
    private static string firstError;

    private static void Require(bool valid, string name)
    { if(!valid)throw new InvalidOperationException("HPR_FAST_ENTER_PLAYMODE_QA_FAILURE:"+name); }

    public static void Run()
    {
        receipt = Environment.GetEnvironmentVariable("HPR_ORIGINAL_FAST_PLAYMODE_QA_OUT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(receipt) &&
            receipt.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal) &&
            !File.Exists(receipt),"fresh_private_target");
        Require(Application.unityVersion.StartsWith("6000.6.",StringComparison.Ordinal),"installed_Unity_6_6");
        var pre = HprAnimationImportScan.ScanProject();
        Require(pre!=null && !pre.incomplete && pre.customerModelsChecked==1,
            "real_private_buyer_project_fbx_scanner_before_playmode");
        originalState=pre.status;
        Require(originalState=="POTENTIAL_ANIMATION_IMPORT_ISSUES",
            "private_original_customer_fbx_still_has_source_take_warning");
        previousOptionsEnabled=EditorSettings.enterPlayModeOptionsEnabled;
        previousOptions=EditorSettings.enterPlayModeOptions;
        EditorSettings.enterPlayModeOptionsEnabled=true;
        EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;
        Require(EditorSettings.enterPlayModeOptionsEnabled &&
            EditorSettings.enterPlayModeOptions==EnterPlayModeOptions.DisableDomainReload,
            "actual_Unity_domain_reload_disabled_setting");
        startedUtc=DateTime.UtcNow;
        started=true;
        Application.logMessageReceived += Log;
        EditorApplication.playModeStateChanged += Transition;
        EditorApplication.update += Tick;
        EditorApplication.delayCall += () => { if(!finished)EditorApplication.isPlaying=true; };
        Debug.Log("HPR_ORIGINAL_FAST_PLAYMODE_START");
    }

    private static void Log(string message,string trace,LogType kind)
    {
        if(kind==LogType.Exception || kind==LogType.Error || kind==LogType.Assert)
        { logErrors++; if(firstError==null)firstError=message; }
    }

    private static void Transition(PlayModeStateChange state)
    {
        if(!started || finished)return;
        if(state==PlayModeStateChange.EnteredPlayMode)
        {
            entered=true;
            Debug.Log("HPR_ORIGINAL_FAST_PLAYMODE_ENTERED");
            EditorApplication.delayCall += () => {if(!finished)EditorApplication.isPlaying=false;};
        }
        else if(state==PlayModeStateChange.EnteredEditMode && entered)
        {
            exited=true;
            Debug.Log("HPR_ORIGINAL_FAST_PLAYMODE_EXITED");
            EditorApplication.delayCall += Complete;
        }
    }

    private static void Tick()
    {
        if(!started || finished)return;
        if((DateTime.UtcNow-startedUtc).TotalSeconds>150)
            Complete();
    }

    private static void Complete()
    {
        if(finished)return;
        finished=true;
        Application.logMessageReceived -= Log;
        EditorApplication.playModeStateChanged -= Transition;
        EditorApplication.update -= Tick;
        try
        {
            Require(entered && exited,"actual_native_enter_and_exit_playmode_completed");
            Require(logErrors==0,"no_Unity_player_console_errors_"+(firstError??""));
            var after=HprAnimationImportScan.ScanProject();
            Require(after!=null && !after.incomplete && after.customerModelsChecked==1 &&
                    after.status==originalState && after.unreferencedSourceTakes==1,
                    "same_real_customer_Editor_scan_after_domain_reload_disabled_playmode");
            using(var stream=new FileStream(receipt,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(stream))
            {
                writer.WriteLine("unity_version="+Application.unityVersion);
                writer.WriteLine("domain_reload_disabled_with_scene_reload_default=PASS");
                writer.WriteLine("actual_EnteredPlayMode_EnteredEditMode_callbacks=PASS");
                writer.WriteLine("original_readonly_importer_scan_before_after_playmode_identical=PASS");
                writer.WriteLine("Unity_console_errors_or_exceptions=0");
                writer.WriteLine("this_is_private_batchmode_not_real_human_window_screenshot=TRUE");
            }
            Debug.Log("HPR_ORIGINAL_FAST_PLAYMODE_NATIVE_PASS");
            EditorApplication.Exit(0);
        }
        catch(Exception ex)
        {
            Debug.LogError("HPR_ORIGINAL_FAST_PLAYMODE_NATIVE_FAIL "+ex.GetType().Name+": "+ex.Message);
            EditorApplication.Exit(13);
        }
        finally
        {
            EditorSettings.enterPlayModeOptions=previousOptions;
            EditorSettings.enterPlayModeOptionsEnabled=previousOptionsEnabled;
        }
    }
}
#endif
