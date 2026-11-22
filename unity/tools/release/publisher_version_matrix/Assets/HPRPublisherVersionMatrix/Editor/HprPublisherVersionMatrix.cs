#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace HPR.PublisherVersionMatrix
{
    [Serializable]
    public sealed class HprVersionAsset
    {
        public string path;
        public string guid;
        public string[] directDependencies;
    }

    [Serializable]
    public sealed class HprVersionReceipt
    {
        public int schema = 1;
        public string unityVersion;
        public string rootFolders;
        public string status;
        public bool incomplete;
        public int assetCount;
        public HprVersionAsset[] assets;
        public string limitation;
    }

    /// <summary>Read-only imported project snapshot; never forces reimport or asset save.</summary>
    public static class HprPublisherVersionScan
    {
        public const int MaxAssets = 4000;
        private const string Scope = "Current imported AssetDatabase paths and GUIDs and direct " +
            "dependencies only; not a serialization, graphical, player or Play Mode " +
            "compatibility certification. Validate real exported packages separately.";

        public static string[] ValidateRoots(string folders)
        {
            if(string.IsNullOrWhiteSpace(folders))
                throw new ArgumentException("At least one publisher-owned Assets folder is required.");
            var names=folders.Split(';').Select(s=>s.Trim()).ToArray();
            if(names.Length==0 || names.Length>12 || names.Any(s=>s.Length<=7 ||
                !s.StartsWith("Assets/",StringComparison.Ordinal) ||
                s.Contains("\\") || s.Contains("..") || s.Contains("//") ||
                s.EndsWith("/",StringComparison.Ordinal) || s.Contains(":") ||
                s.Any(char.IsControl)))
                throw new ArgumentException("Specify up to twelve exact Assets/... folder paths.");
            if(names.Distinct(StringComparer.OrdinalIgnoreCase).Count()!=names.Length)
                throw new ArgumentException("Duplicate publisher roots are not allowed.");
            Array.Sort(names,StringComparer.Ordinal);
            for(int i=0;i<names.Length;i++)
                for(int j=i+1;j<names.Length;j++)
                    if(names[j].StartsWith(names[i]+"/",StringComparison.OrdinalIgnoreCase))
                        throw new ArgumentException("Nested roots would duplicate assets.");
            return names;
        }

        public static HprVersionReceipt Scan(string folders)
        {
            var roots=ValidateRoots(folders);
            var result=new HprVersionReceipt { unityVersion=Application.unityVersion,
                rootFolders=string.Join(";",roots), status="INCOMPLETE", incomplete=true,
                limitation=Scope, assets=new HprVersionAsset[0] };
            if(roots.Any(folder=>!AssetDatabase.IsValidFolder(folder)))return result;
            var list=new List<HprVersionAsset>();
            var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach(string folder in roots)
            {
                string[] ids=AssetDatabase.FindAssets("",new[]{folder});
                if(ids.Length>MaxAssets || list.Count+ids.Length>MaxAssets)return result;
                foreach(var id in ids)
                {
                    var path=AssetDatabase.GUIDToAssetPath(id);
                    if(string.IsNullOrEmpty(path) ||
                        !(path==folder || path.StartsWith(folder+"/",StringComparison.Ordinal)) ||
                        !seen.Add(path))return result;
                    if(AssetDatabase.IsValidFolder(path))continue;
                    var checkId=AssetDatabase.AssetPathToGUID(path);
                    if(string.IsNullOrEmpty(checkId) || checkId!=id)return result;
                    string[] dependencies;
                    try
                    {
                        dependencies=AssetDatabase.GetDependencies(path,false)
                            .Where(item=>item!=path).Distinct(StringComparer.Ordinal)
                            .OrderBy(item=>item,StringComparer.Ordinal).ToArray();
                    }
                    catch(Exception) {return result;}
                    list.Add(new HprVersionAsset {path=path,guid=id,directDependencies=dependencies});
                }
            }
            list.Sort((x,y)=>StringComparer.Ordinal.Compare(x.path,y.path));
            result.assets=list.ToArray();result.assetCount=result.assets.Length;
            result.incomplete=false;
            result.status=result.assetCount>0 ? "SNAPSHOT_COMPLETE" : "EMPTY_PUBLISHER_ROOTS";
            return result;
        }

        public static void ExportNew(HprVersionReceipt receipt,string absoluteFile)
        {
            if(receipt==null || receipt.incomplete || !Path.IsPathRooted(absoluteFile))
                throw new ArgumentException("Complete report and new absolute output path required.");
            using(var file=new FileStream(absoluteFile,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(file,new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(receipt,true));
        }
    }

    public sealed class HprPublisherVersionMatrixWindow : EditorWindow
    {
        private string roots="Assets/MyPublisherPackage";
        private string notice="Scan an already imported package in a disposable project.";
        private HprVersionReceipt result;
        private Vector2 scroll;
        private string assetFilter="";
        [MenuItem("Tools/HPR/Publisher Version Matrix")]
        public static void Open()
        {
            var window=GetWindow<HprPublisherVersionMatrixWindow>("Publisher Version Matrix");
            window.minSize=new Vector2(640f,410f);window.Show();
        }
        private void OnGUI()
        {
            GUILayout.Label("PUBLISHER VERSION MATRIX",EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Read-only imported package evidence for this Unity version. " +
                "Repeat in a fresh project with another Unity Editor version and compare new JSON receipts. " +
                "This does not validate gameplay, complete serialization or Player builds.",MessageType.Info);
            roots=EditorGUILayout.TextField("Original Assets root(s)",roots);
            if(GUILayout.Button("Compare two previously exported Unity receipts",GUILayout.Height(30)))
                HprVersionCompareWindow.Open();
            if(GUILayout.Button("Scan imported publisher assets",GUILayout.Height(32)))
            {
                result=null;
                try
                {
                    result=HprPublisherVersionScan.Scan(roots);
                    notice=result.incomplete ? "INCOMPLETE. No compatible result can be claimed." :
                        "Read-only imported publisher snapshot complete.";
                }
                catch(Exception ex) {notice="Unable to scan: "+ex.Message;}
            }
            EditorGUILayout.HelpBox(notice,result!=null && result.incomplete ? MessageType.Error : MessageType.None);
            if(result==null)return;
            EditorGUILayout.LabelField("Unity "+result.unityVersion+" | "+result.status+
                " | Assets: "+result.assetCount,EditorStyles.boldLabel);
            if(!result.incomplete && result.assetCount>0 &&
                GUILayout.Button("Export NEW JSON compatibility receipt"))
            {
                var file=EditorUtility.SaveFilePanel("Save original publisher version snapshot","",
                    "publisher-version-snapshot.json","json");
                if(!string.IsNullOrEmpty(file))
                {
                    try{HprPublisherVersionScan.ExportNew(result,file);notice="New report exported.";}
                    catch(Exception ex){notice="Report not overwritten: "+ex.Message;}
                }
            }
            assetFilter=EditorGUILayout.TextField("Find imported asset",assetFilter);
            scroll=EditorGUILayout.BeginScrollView(scroll);
            if(result.assets!=null)
            {
                var filtered=result.assets.Where(asset=>asset.path.IndexOf(assetFilter,
                    StringComparison.OrdinalIgnoreCase)>=0).ToArray();
                if(filtered.Length==0)
                    EditorGUILayout.HelpBox("No imported publisher assets match this filter.",MessageType.Info);
                else
                    EditorGUILayout.LabelField("Matching assets: "+filtered.Length,
                        EditorStyles.boldLabel);
                foreach(var asset in filtered.Take(80))
                {
                    EditorGUILayout.LabelField(asset.path,EditorStyles.boldLabel);
                    EditorGUILayout.LabelField("GUID: "+asset.guid+" | Direct dependencies: "+
                        asset.directDependencies.Length,EditorStyles.miniLabel);
                }
                if(filtered.Length>80)
                    EditorGUILayout.HelpBox("Only first eighty matches shown. Narrow the search or export the complete JSON receipt.",
                        MessageType.Info);
            }
            EditorGUILayout.HelpBox(result.limitation,MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
