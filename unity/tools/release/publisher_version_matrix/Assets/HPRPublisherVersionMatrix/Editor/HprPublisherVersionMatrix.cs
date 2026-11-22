#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;

namespace HPR.PublisherVersionMatrix
{
    [Serializable]
    public sealed class HprVersionAsset
    {
        public string path;
        public string guid;
        public string sourceFileSha256;
        public string metaFileSha256;
        public string[] directDependencies;
    }

    [Serializable]
    public sealed class HprVersionReceipt
    {
        public int schema = 2;
        public string unityVersion;
        public string rootFolders;
        public string status;
        public bool incomplete;
        public int assetCount;
        public HprVersionAsset[] assets;
        public string failureReason;
        public string limitation;
    }

    /// <summary>Read-only imported project snapshot; never forces reimport or asset save.</summary>
    public static class HprPublisherVersionScan
    {
        public const int MaxAssets = 4000;
        public const long MaxFileBytes = 1073741824L;  // 1 GiB; never read unlimited data
        public const long MaxTotalBytes = 4294967296L; // 4 GiB across both file types
        private const string Scope = "Read-only current imported paths, GUIDs, direct " +
            "dependencies and SHA-256 of actual asset and .meta source bytes. " +
            "This is not a test of imported in-memory object fields, Player builds, " +
            "graphical output, runtime behavior or future Unity compatibility.";

        /// <summary>Bounded streaming read from an imported source file, no writes.</summary>
        private static bool TryHashFile(string filename,ref long total,string projectRoot,
            out string digest)
        {
            digest=null;
            string full=Path.GetFullPath(filename);
            if(!full.StartsWith(projectRoot+Path.DirectorySeparatorChar,
                StringComparison.Ordinal))return false;
            var before=new FileInfo(full);
            if(!before.Exists || (before.Attributes & FileAttributes.ReparsePoint)!=0 ||
                before.Length>MaxFileBytes || before.Length>MaxTotalBytes-total)return false;
            long length=before.Length;
            DateTime modified=before.LastWriteTimeUtc;
            using(var stream=new FileStream(full,FileMode.Open,FileAccess.Read,FileShare.Read))
            using(var hash=SHA256.Create())
                digest=BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "")
                    .ToLowerInvariant();
            before.Refresh();
            if(!before.Exists || before.Length!=length || before.LastWriteTimeUtc!=modified)
            { digest=null;return false; }
            total+=length;
            return true;
        }

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

        public static HprVersionReceipt Scan(string folders,
            Func<int,int,bool> canceled=null)
        {
            var roots=ValidateRoots(folders);
            var result=new HprVersionReceipt { unityVersion=Application.unityVersion,
                rootFolders=string.Join(";",roots), status="INCOMPLETE", incomplete=true,
                failureReason="", limitation=Scope, assets=new HprVersionAsset[0] };
            if(roots.Any(folder=>!AssetDatabase.IsValidFolder(folder)))
            { result.failureReason="One or more publisher roots do not exist.";return result; }
            var candidates=new List<KeyValuePair<string,string>>();
            foreach(string folder in roots)
            {
                string[] ids=AssetDatabase.FindAssets("",new[]{folder});
                if(ids.Length>MaxAssets || candidates.Count+ids.Length>MaxAssets)
                { result.failureReason="The four-thousand-asset scan limit was reached.";return result; }
                foreach(var id in ids)candidates.Add(new KeyValuePair<string,string>(folder,id));
            }
            candidates.Sort((x,y)=>StringComparer.Ordinal.Compare(x.Value,y.Value));
            var list=new List<HprVersionAsset>();
            var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var seenGuids=new HashSet<string>(StringComparer.Ordinal);
            long bytesHashed=0;
            string projectRoot=Path.GetFullPath(Directory.GetParent(Application.dataPath).FullName);
            for(int i=0;i<candidates.Count;i++)
            {
                var id=candidates[i].Value;
                string folder=candidates[i].Key;
                if(canceled!=null && canceled(i,candidates.Count))
                { result.failureReason="Canceled by the reviewer; no complete result.";return result; }
                string path=AssetDatabase.GUIDToAssetPath(id);
                if(string.IsNullOrEmpty(path) || path.Contains("..") || path.Contains("\\") ||
                    !path.StartsWith("Assets/",StringComparison.Ordinal) ||
                    !path.StartsWith(folder+"/",StringComparison.Ordinal) ||
                    !seen.Add(path) || !seenGuids.Add(id))
                { result.failureReason="Invalid or duplicate imported source path or GUID.";return result; }
                if(AssetDatabase.IsValidFolder(path))continue;
                var checkId=AssetDatabase.AssetPathToGUID(path);
                if(string.IsNullOrEmpty(checkId) || checkId!=id)
                { result.failureReason="Asset database identity changed during scanning.";return result; }
                try
                {
                    string dataHash,metaHash;
                    if(!TryHashFile(Path.Combine(projectRoot,path),ref bytesHashed,
                            projectRoot,out dataHash) ||
                        !TryHashFile(Path.Combine(projectRoot,path+".meta"),ref bytesHashed,
                            projectRoot,out metaHash))
                    {
                        result.failureReason="Source or importer metadata missing, changed, linked or exceeded bounded hashing limit: "+path;
                        return result;
                    }
                    string[] dependencies=AssetDatabase.GetDependencies(path,false)
                        .Where(item=>item!=path).Distinct(StringComparer.Ordinal)
                        .OrderBy(item=>item,StringComparer.Ordinal).ToArray();
                    list.Add(new HprVersionAsset {path=path,guid=id,
                        sourceFileSha256=dataHash,metaFileSha256=metaHash,
                        directDependencies=dependencies});
                }
                catch(Exception error)
                {
                    result.failureReason="Source data could not be read for "+path+": "+error.GetType().Name;
                    return result;
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
                    result=HprPublisherVersionScan.Scan(roots,(i,n)=>
                        EditorUtility.DisplayCancelableProgressBar("Publisher Version Matrix",
                            "Hashing original asset and importer metadata "+(i+1)+" / "+n,
                            n>0 ? (float)i/n : 0f));
                    notice=result.incomplete ? "INCOMPLETE: "+result.failureReason :
                        "Imported assets, metadata bytes and dependencies verified without changes.";
                }
                catch(Exception ex) {notice="Unable to scan: "+ex.Message;}
                finally {EditorUtility.ClearProgressBar();}
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
                    EditorGUILayout.LabelField("Original source SHA-256: "+
                        asset.sourceFileSha256.Substring(0,16)+"... | .meta: "+
                        asset.metaFileSha256.Substring(0,16)+"...",EditorStyles.miniLabel);
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
