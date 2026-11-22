#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// Genuine original Unity scene camera capture, separately executed in an
// isolated temporary display. This is NOT a capture of the EditorWindow UI.
// Private QA only, never a customer package component.
public static class HprOriginalScenePreviewCapture
{
    public static void Run()
    {
        string output=Environment.GetEnvironmentVariable("HPR_ORIGINAL_SCENE_PREVIEW_OUT")??"";
        if(!Application.isBatchMode || !Path.IsPathRooted(output) ||
           !output.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal) ||
           !output.EndsWith(".png",StringComparison.Ordinal) || File.Exists(output))
            throw new InvalidOperationException("Fresh original private PNG output required");
        const string scenePath = "Assets/HPRFbxSourceTakes/Samples/Scenes/SourceTakeVisibilityDemo.unity";
        if(AssetDatabase.LoadAssetAtPath<SceneAsset>(scenePath)==null)
            throw new InvalidOperationException("Original Unity buyer scene not installed");
        var source=EditorSceneManager.OpenScene(scenePath,OpenSceneMode.Single);
        if(!source.IsValid() || !source.isLoaded)
            throw new InvalidOperationException("Original Unity scene did not load");
        var cameras=UnityEngine.Object.FindObjectsOfType<Camera>();
        var camera=cameras.FirstOrDefault(c=>c.gameObject.CompareTag("MainCamera")) ?? cameras.FirstOrDefault();
        if(camera==null) throw new InvalidOperationException("Unity scene has no camera");
        const int width=1440,height=900;
        RenderTexture target=new RenderTexture(width,height,24,RenderTextureFormat.ARGB32);
        target.Create();
        if(!target.IsCreated())throw new InvalidOperationException("Real render texture not available in Unity graphics device");
        var earlierCameraTarget=camera.targetTexture;
        var earlierActive=RenderTexture.active;
        Texture2D texture=null;
        try
        {
            camera.targetTexture=target;
            camera.aspect=(float)width/height;
            camera.Render();
            RenderTexture.active=target;
            texture=new Texture2D(width,height,TextureFormat.RGB24,false);
            texture.ReadPixels(new Rect(0,0,width,height),0,0);
            texture.Apply(false);
            byte[] png=texture.EncodeToPNG();
            if(png==null || png.Length < 7000)
                throw new InvalidOperationException("Real Unity scene image missing or implausibly small");
            using(var file = new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
                file.Write(png,0,png.Length);
            Debug.Log("HPR_ORIGINAL_UNITY_SCENE_CAPTURE_PASS "+width+"x"+height+" png="+png.Length);
        }
        finally
        {
            camera.targetTexture=earlierCameraTarget;
            RenderTexture.active=earlierActive;
            if(texture!=null)UnityEngine.Object.DestroyImmediate(texture);
            target.Release(); UnityEngine.Object.DestroyImmediate(target);
        }
    }
}
#endif
