#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// PRIVATE first-party test author; never included in buyer asset package.
public static class HprColliderPhysicsAuthorQa
{
    public const string Root="Assets/HPRColliderOriginal";
    public const string Prefab=Root+"/CapsuleAndController.prefab";
    private static void Require(bool condition,string msg)
    {if(!condition)throw new InvalidOperationException("HPR_COLLIDER_AUTHOR_FAIL:"+msg);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string output=Environment.GetEnvironmentVariable("HPR_COLLIDER_AUTHOR_ROOT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(output) &&
                output.StartsWith(safe,StringComparison.Ordinal),"private_disposable_root");
        string fixture=Path.Combine(output,"HPR_ColliderPhysicsOriginal_Qa_Fixture.unitypackage");
        string package=Path.Combine(output,"HPR_ImportedPrefabParity_PhysicsOriginal.unitypackage");
        Require(!File.Exists(fixture) && !File.Exists(package) &&
                !AssetDatabase.IsValidFolder(Root) &&
                AssetDatabase.IsValidFolder("Assets/HPRImportedPrefabParity"),
                "create_only_original_source_and_fixture");
        AssetDatabase.CreateFolder("Assets","HPRColliderOriginal");
        var machine=new GameObject("HPR_Original_Physics_Machine");
        var capsule=machine.AddComponent<CapsuleCollider>();
        capsule.center=new Vector3(.25f,1f,-.5f);
        capsule.radius=.67f;capsule.height=2.75f;capsule.direction=2;
        var player=new GameObject("HPR_Original_ControllerChild");
        player.transform.SetParent(machine.transform,false);
        var controller=player.AddComponent<CharacterController>();
        controller.center=new Vector3(.1f,.8f,.05f);
        controller.radius=.41f;controller.height=1.85f;
        controller.slopeLimit=46f;controller.stepOffset=.24f;controller.skinWidth=.04f;
        var created=PrefabUtility.SaveAsPrefabAsset(machine,Prefab);
        Require(created!=null,"original_physics_prefab_saved");
        UnityEngine.Object.DestroyImmediate(machine);
        AssetDatabase.SaveAssets();AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        AssetDatabase.ExportPackage(new[]{Root},fixture,ExportPackageOptions.Recurse);
        AssetDatabase.ExportPackage(new[]{"Assets/HPRImportedPrefabParity"},package,
            ExportPackageOptions.Recurse);
        Require(File.Exists(fixture) && File.Exists(package) &&
            new FileInfo(fixture).Length>500 && new FileInfo(package).Length>3000,
            "actual_original_unitypackage_exports_present");
        Debug.Log("HPR_COLLIDER_AUTHOR_ORIGINAL_PACKAGES_PASS fixture_bytes="+
            new FileInfo(fixture).Length+" product_bytes="+new FileInfo(package).Length);
    }
}
#endif
