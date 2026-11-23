#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE actual Unity 6.6+ buyer acceptance: enter and exit PlayMode with Domain Reload off.
public static class HprProbeQaFastPlaymode
{
    private static bool savedEnabled,entered,exited,completed;
    private static EnterPlayModeOptions savedOptions;
    private static DateTime start;
    private static string original,output;
    private static int errors;
    private static string firstError;
    const string Scene="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    private static void Require(bool okay,string message)
    {if(!okay)throw new InvalidOperationException("HPR_PLAYER_PROBE_FAST_PLAYMODE_FAILURE:"+message);}
    private static string InspectOriginal()
    {
        var scene=EditorSceneManager.OpenScene(Scene,OpenSceneMode.Single);
        Require(scene.isLoaded && scene.rootCount==13,"real_original_demo_scene_loaded");
        var probes=scene.GetRootGameObjects()
            .SelectMany(go=>go.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).ToArray();
        Require(probes.Length==1 && probes[0].checks.Length==2 &&
            probes[0].checks.All(x=>x.source==null),"original_sample_only_resources_paths");
        var result=HprReferenceInspector.Inspect(probes[0].checks,"EDITOR");
        HprReferenceInspector.Validate(result);
        Require(result.checkedCount==2 && result.assignedCount==1 && result.missingCount==1 &&
            result.unsupportedCount==0,"original_direct_reference_before_or_after_enter_playmode");
        return JsonUtility.ToJson(result,false);
    }
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        output=Environment.GetEnvironmentVariable("HPR_PLAYER_PROBE_FAST_PLAYMODE_OUT")??"";
        Require(Application.isBatchMode && Application.unityVersion.StartsWith("6000.6.",
            StringComparison.Ordinal) && Path.IsPathRooted(output) &&
            output.StartsWith(safe,StringComparison.Ordinal) && !File.Exists(output),
            "private_create_only_original_receipt");
        original=InspectOriginal();
        savedEnabled=EditorSettings.enterPlayModeOptionsEnabled;
        savedOptions=EditorSettings.enterPlayModeOptions;
        EditorSettings.enterPlayModeOptionsEnabled=true;
        EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;
        Require(EditorSettings.enterPlayModeOptionsEnabled &&
            EditorSettings.enterPlayModeOptions==EnterPlayModeOptions.DisableDomainReload,
            "domain_reload_disabled_natively");
        start=DateTime.UtcNow;
        Application.logMessageReceived+=Log;
        EditorApplication.playModeStateChanged+=State;
        EditorApplication.update+=Tick;
        EditorApplication.delayCall+=()=>{if(!completed)EditorApplication.isPlaying=true;};
        Debug.Log("HPR_PLAYER_PROBE_FAST_PLAYMODE_STARTED");
    }
    private static void Log(string message,string trace,LogType type)
    {
        if(type==LogType.Error || type==LogType.Assert || type==LogType.Exception)
        {errors++;if(firstError==null)firstError=message;}
    }
    private static void State(PlayModeStateChange mode)
    {
        if(completed)return;
        if(mode==PlayModeStateChange.EnteredPlayMode)
        {
            entered=true;Debug.Log("HPR_PLAYER_PROBE_FAST_PLAYMODE_ENTERED");
            EditorApplication.delayCall+=()=>{if(!completed)EditorApplication.isPlaying=false;};
        }
        else if(mode==PlayModeStateChange.EnteredEditMode && entered)
        {
            exited=true;Debug.Log("HPR_PLAYER_PROBE_FAST_PLAYMODE_EXITED");
            EditorApplication.delayCall+=Finish;
        }
    }
    private static void Tick()
    {
        if(!completed && (DateTime.UtcNow-start).TotalSeconds>155)Finish();
    }
    private static void Finish()
    {
        if(completed)return;completed=true;
        Application.logMessageReceived-=Log;
        EditorApplication.playModeStateChanged-=State;
        EditorApplication.update-=Tick;
        try
        {
            Require(entered && exited,"actual_enter_and_exit_PlayMode_confirmed");
            Require(errors==0,"no_Editor_console_error_"+(firstError??""));
            Require(InspectOriginal()==original,"original_refs_identical_after_domain_reload_disabled");
            using(var file=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(file))
            {
                writer.WriteLine("actual_unity_version="+Application.unityVersion);
                writer.WriteLine("real_enter_and_exit_PlayMode=PASS");
                writer.WriteLine("domain_reload_disabled=PASS");
                writer.WriteLine("original_two_Resources_probe_cases_identical_before_after=PASS");
                writer.WriteLine("Unity_Editor_console_errors=0");
                writer.WriteLine("human_Editor_UI_controls_manually_clicked=FALSE");
            }
            Debug.Log("HPR_PLAYER_PROBE_REAL_UNITY6_FAST_PLAYMODE_NATIVE_PASS");
            EditorApplication.Exit(0);
        }
        catch(Exception ex)
        {
            Debug.LogError("HPR_PLAYER_PROBE_REAL_UNITY6_FAST_PLAYMODE_NATIVE_FAIL "+
                ex.GetType().Name+":"+ex.Message);
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
