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
    public sealed class HprVersionDifference
    {
        public int schema = 2;
        public string firstUnityVersion;
        public string secondUnityVersion;
        public string rootFolders;
        public string status;
        public string[] missingFromSecond;
        public string[] newInSecond;
        public string[] guidChanges;
        public string[] dependencyChanges;
        public string[] sourceFileChanges;
        public string[] importerMetaChanges;
        public string limitation;
    }

    /// <summary>Two imported Unity Editor receipts; no reimport, resave or editor mutation.</summary>
    public static class HprVersionReceiptCompare
    {
        public const int MaxReceiptBytes = 8000000;
        private const string Limitation = "This read-only comparison checks paths, GUIDs, direct " +
            "dependencies and original on-disk asset/.meta SHA-256 bytes, not imported object " +
            "fields, scene appearances, player builds, animation, native plugins, " +
            "runtime references or Asset Store acceptance. Test actual Player builds.";

        private static bool ValidSha256(string hash)
        {
            return hash!=null && hash.Length==64 &&
                hash.All(ch=>(ch>='0'&&ch<='9')||(ch>='a'&&ch<='f'));
        }

        public static HprVersionReceipt ReadReceipt(string absolutePath)
        {
            if(!Path.IsPathRooted(absolutePath) || !File.Exists(absolutePath) ||
                new FileInfo(absolutePath).Length>MaxReceiptBytes)
                throw new ArgumentException("Source JSON must be a small existing absolute path.");
            var result=JsonUtility.FromJson<HprVersionReceipt>(File.ReadAllText(absolutePath));
            Validate(result);
            return result;
        }

        public static void Validate(HprVersionReceipt report)
        {
            if(report==null || report.schema!=2 || report.incomplete ||
                !string.IsNullOrEmpty(report.failureReason) ||
                report.status!="SNAPSHOT_COMPLETE" ||
                string.IsNullOrWhiteSpace(report.unityVersion) ||
                report.assets==null || report.assetCount!=report.assets.Length ||
                report.assetCount<1 || report.assetCount>HprPublisherVersionScan.MaxAssets)
                throw new ArgumentException("Incomplete or untrusted version snapshot.");
            var roots=HprPublisherVersionScan.ValidateRoots(report.rootFolders);
            if(report.rootFolders!=string.Join(";",roots))
                throw new ArgumentException("Noncanonical publisher root set.");
            var paths=new HashSet<string>(StringComparer.Ordinal);
            var guids=new HashSet<string>(StringComparer.Ordinal);
            foreach(var a in report.assets)
            {
                if(a==null || string.IsNullOrEmpty(a.path) || a.path.Length>1200 ||
                    !roots.Any(root=>a.path.StartsWith(root+"/",StringComparison.Ordinal)) ||
                    a.path.Contains("..") || a.path.Contains("\\") || !paths.Add(a.path) ||
                    string.IsNullOrEmpty(a.guid) || a.guid.Length!=32 ||
                    !a.guid.All(ch=>(ch>='0'&&ch<='9')||(ch>='a'&&ch<='f')) ||
                    !guids.Add(a.guid) ||
                    !ValidSha256(a.sourceFileSha256) ||
                    !ValidSha256(a.metaFileSha256) ||
                    a.directDependencies==null || a.directDependencies.Length>HprPublisherVersionScan.MaxAssets ||
                    a.directDependencies.Any(d=>string.IsNullOrEmpty(d) || d.Length>1200) ||
                    a.directDependencies.Distinct(StringComparer.Ordinal).Count()!=a.directDependencies.Length)
                    throw new ArgumentException("Untrusted asset path, GUID or dependency graph.");
            }
        }

        public static HprVersionDifference Compare(HprVersionReceipt first,
            HprVersionReceipt second)
        {
            Validate(first);Validate(second);
            if(first.rootFolders!=second.rootFolders ||
                first.unityVersion==second.unityVersion)
                throw new ArgumentException("Compare the same publisher roots from two different Unity versions.");
            var a=first.assets.ToDictionary(x=>x.path,StringComparer.Ordinal);
            var b=second.assets.ToDictionary(x=>x.path,StringComparer.Ordinal);
            var missing=a.Keys.Except(b.Keys,StringComparer.Ordinal).OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            var added=b.Keys.Except(a.Keys,StringComparer.Ordinal).OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            var same=a.Keys.Intersect(b.Keys,StringComparer.Ordinal).ToArray();
            var guidChanged=same.Where(x=>a[x].guid!=b[x].guid).OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            var depChanged=same.Where(x=>!a[x].directDependencies.OrderBy(z=>z,StringComparer.Ordinal)
                .SequenceEqual(b[x].directDependencies.OrderBy(z=>z,StringComparer.Ordinal)))
                .OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            var sourceChanged=same.Where(x=>a[x].sourceFileSha256!=b[x].sourceFileSha256)
                .OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            var metaChanged=same.Where(x=>a[x].metaFileSha256!=b[x].metaFileSha256)
                .OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            return new HprVersionDifference
            {
                firstUnityVersion=first.unityVersion,secondUnityVersion=second.unityVersion,
                rootFolders=first.rootFolders,missingFromSecond=missing,newInSecond=added,
                guidChanges=guidChanged,dependencyChanges=depChanged,
                sourceFileChanges=sourceChanged,importerMetaChanges=metaChanged,
                status=missing.Length+added.Length+guidChanged.Length+depChanged.Length+
                    sourceChanged.Length+metaChanged.Length>0 ?
                    "REVIEW_IMPORT_DIFFERENCES" : "MATCHED_IMPORT_INPUT_BYTES_AND_METADATA",
                limitation=Limitation
            };
        }

        public static void ExportNew(HprVersionDifference report,string path)
        {
            if(report==null || !Path.IsPathRooted(path) ||
                report.status!="MATCHED_IMPORT_INPUT_BYTES_AND_METADATA" &&
                report.status!="REVIEW_IMPORT_DIFFERENCES")
                throw new ArgumentException("Only a complete version comparison can be exported.");
            using(var file=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(file,new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report,true));
        }
    }

    public sealed class HprVersionCompareWindow : EditorWindow
    {
        private string sourceOne="";
        private string sourceTwo="";
        private HprVersionDifference result;
        private string notice="Select original JSON receipts exported by two independent Unity versions.";
        private string pathFilter="";
        private Vector2 scroll;

        [MenuItem("Tools/HPR/Compare Publisher Version Receipts")]
        public static void Open()
        {
            var window=GetWindow<HprVersionCompareWindow>("Compare Unity Versions");
            window.minSize=new Vector2(650f,420f);window.Show();
        }

        private void OnGUI()
        {
            GUILayout.Label("COMPARE ORIGINAL PUBLISHER VERSION RECEIPTS",EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Two read-only imported snapshots; never alters an asset. " +
                "Differences need human review and real Player checks. Matching metadata is not full compatibility.",
                MessageType.Info);
            EditorGUILayout.LabelField("First source: "+sourceOne,EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Choose first existing JSON snapshot"))
            {
                var file=EditorUtility.OpenFilePanel("First Unity snapshot", "", "json");
                if(!string.IsNullOrEmpty(file)) {sourceOne=file;result=null;}
            }
            EditorGUILayout.LabelField("Second source: "+sourceTwo,EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Choose second existing JSON snapshot"))
            {
                var file=EditorUtility.OpenFilePanel("Second Unity snapshot", "", "json");
                if(!string.IsNullOrEmpty(file)) {sourceTwo=file;result=null;}
            }
            if(GUILayout.Button("Compare imported paths, GUIDs and direct dependencies",GUILayout.Height(32)))
            {
                result=null;
                try
                {
                    result=HprVersionReceiptCompare.Compare(
                        HprVersionReceiptCompare.ReadReceipt(sourceOne),
                        HprVersionReceiptCompare.ReadReceipt(sourceTwo));
                    notice=result.status=="MATCHED_IMPORT_INPUT_BYTES_AND_METADATA" ?
                        "Original imported files and metadata match. Runtime compatibility is not proven." :
                        "Review the explicit imported asset changes below.";
                }
                catch(Exception ex){notice="No comparison produced: "+ex.Message;}
            }
            EditorGUILayout.HelpBox(notice,result!=null &&
                result.status=="REVIEW_IMPORT_DIFFERENCES" ? MessageType.Warning : MessageType.None);
            if(result==null)return;
            EditorGUILayout.LabelField("Unity "+result.firstUnityVersion+" → "+result.secondUnityVersion+
                " | "+result.status,EditorStyles.boldLabel);
            EditorGUILayout.LabelField("Removed: "+result.missingFromSecond.Length+
                " | Added: "+result.newInSecond.Length+
                " | Changed GUIDs: "+result.guidChanges.Length+
                " | Changed dependencies: "+result.dependencyChanges.Length,
                EditorStyles.wordWrappedLabel);
            EditorGUILayout.LabelField("Changed original asset bytes: "+result.sourceFileChanges.Length+
                " | Changed importer .meta bytes: "+result.importerMetaChanges.Length,
                EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Export NEW comparison JSON"))
            {
                var path=EditorUtility.SaveFilePanel("Save publisher version difference","",
                    "publisher-version-differences.json","json");
                if(!string.IsNullOrEmpty(path))
                {
                    try{HprVersionReceiptCompare.ExportNew(result,path);notice="New comparison saved.";}
                    catch(Exception ex){notice="No existing file overwritten: "+ex.Message;}
                }
            }
            pathFilter=EditorGUILayout.TextField("Find affected asset",pathFilter);
            scroll=EditorGUILayout.BeginScrollView(scroll);
            int shown=0;
            shown=ShowPaths("Removed in second version",result.missingFromSecond,shown);
            shown=ShowPaths("Added in second version",result.newInSecond,shown);
            shown=ShowPaths("GUID changed",result.guidChanges,shown);
            shown=ShowPaths("Direct dependencies changed",result.dependencyChanges,shown);
            shown=ShowPaths("Original asset bytes changed",result.sourceFileChanges,shown);
            shown=ShowPaths("Unity .meta importer bytes changed",result.importerMetaChanges,shown);
            if(shown>=80)EditorGUILayout.HelpBox("Only first eighty matching changes shown; export JSON for all details.",MessageType.Info);
            EditorGUILayout.HelpBox(result.limitation,MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }
        private int ShowPaths(string title,string[] values,int shown)
        {
            if(values==null || values.Length==0 || shown>=80)return shown;
            bool titleShown=false;
            foreach(var path in values)
            {
                if(pathFilter.Length>0 && path.IndexOf(pathFilter,StringComparison.OrdinalIgnoreCase)<0)
                    continue;
                if(!titleShown){EditorGUILayout.LabelField(title,EditorStyles.boldLabel);titleShown=true;}
                EditorGUILayout.LabelField(path,EditorStyles.wordWrappedLabel);
                if(++shown>=80)break;
            }
            return shown;
        }
    }
}
#endif
