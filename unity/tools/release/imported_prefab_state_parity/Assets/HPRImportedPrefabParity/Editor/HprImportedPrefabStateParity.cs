#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace HPR.ImportedPrefabParity
{
    [Serializable] public sealed class HprPrefabInput
    {
        public string path;
        public string sourceSha256;
        public string metaSha256;
    }
    [Serializable] public sealed class HprPrefabDependency
    {
        public string path;
        public string guid;
        public string sourceSha256;
        public string metaSha256;
    }
    [Serializable] public sealed class HprPrefabValue
    {
        public string key;
        public string value;
    }
    [Serializable] public sealed class HprPrefabReceipt
    {
        public int schema=2;
        public string unityVersion;
        public string status;
        public bool incomplete;
        public string failureReason;
        public int valuesCaptured;
        public int unsupportedComponents;
        public HprPrefabInput[] inputs;
        public HprPrefabDependency[] dependencies;
        public string[] unverifiedDependencyPaths;
        public HprPrefabValue[] values;
        public string limitation;
    }
    [Serializable] public sealed class HprPrefabComparison
    {
        public int schema=2;
        public string firstUnityVersion;
        public string secondUnityVersion;
        public string status;
        public string[] sourceDifferences;
        public string[] dependencyDifferences;
        public string[] unverifiedDependencyPaths;
        public string[] removedValueKeys;
        public string[] addedValueKeys;
        public string[] changedValueKeys;
        public int unsupportedComponents;
        public string limitation;
    }

    /// <summary>First-party, read-only snapshot of bounded high-impact prefab state.</summary>
    public static class HprPrefabStateScan
    {
        public const int MaxPrefabs=24;
        public const int MaxValues=25000;
        public const int MaxDependencies=512;
        public const int MaxUnverifiedDependencyPaths=64;
        public const long MaxSourceBytes=67108864L;
        public const long MaxTotalBytes=268435456L;
        private const string Scope="Checks imported prefab hierarchy, object active/layer/tag, " +
            "Transform, Renderer/material/mesh/sprite, TextMesh, Animator, Collider and Rigidbody fields and component " +
            "types. Recursively referenced original Assets/ dependency bytes and .meta input " +
            "are checked, but built-in and package dependencies may remain unverified. " +
            "Other scripts, project settings and fields are NOT inspected; this never " +
            "proves identical Unity serialization, graphics, animation or runtime behavior.";
        private static readonly StringComparer Order=StringComparer.Ordinal;

        public static string[] ValidatePaths(string input)
        {
            if(string.IsNullOrWhiteSpace(input))
                throw new ArgumentException("Select one or more real original Assets/... .prefab files.");
            // Unity's buyer window accepts one path per line as well as legacy semicolons.
            var paths=input.Split(new[]{';','\r','\n'},StringSplitOptions.RemoveEmptyEntries)
                .Select(v=>v.Trim()).Where(v=>v.Length>0).ToArray();
            if(paths.Length<1 || paths.Length>MaxPrefabs || paths.Any(p=>
                !p.StartsWith("Assets/",StringComparison.Ordinal) ||
                !p.EndsWith(".prefab",StringComparison.OrdinalIgnoreCase) ||
                p.Length>500 || p.Contains("..") || p.Contains("\\") ||
                p.Contains(":") || p.Contains("//") || p.Any(char.IsControl)) ||
                paths.Distinct(StringComparer.OrdinalIgnoreCase).Count()!=paths.Length)
                throw new ArgumentException("Only unique, bounded, exact Assets/... .prefab paths are supported.");
            Array.Sort(paths,Order);
            return paths;
        }

        private static string Sha256(string path,ref long total,string root)
        {
            string full=Path.GetFullPath(path);
            if(!full.StartsWith(root+Path.DirectorySeparatorChar,StringComparison.Ordinal))
                throw new IOException("Source asset path outside the current project.");
            var file=new FileInfo(full);
            if(!file.Exists || (file.Attributes & FileAttributes.ReparsePoint)!=0 ||
                file.Length>MaxSourceBytes || file.Length>MaxTotalBytes-total)
                throw new IOException("Missing, linked or oversized source asset or importer metadata.");
            long length=file.Length;
            DateTime originalTime=file.LastWriteTimeUtc;
            string digest;
            using(var stream=new FileStream(full,FileMode.Open,FileAccess.Read,FileShare.Read))
            using(var sha=SHA256.Create())
                digest=BitConverter.ToString(sha.ComputeHash(stream)).Replace("-","").ToLowerInvariant();
            file.Refresh();
            if(!file.Exists || file.Length!=length || file.LastWriteTimeUtc!=originalTime)
                throw new IOException("Original source changed during read.");
            total+=length;
            return digest;
        }

        private static bool RealAssetPath(string path)
        {
            return !string.IsNullOrEmpty(path) && path.Length<=500 &&
                path.StartsWith("Assets/",StringComparison.Ordinal) &&
                !path.Contains("..") && !path.Contains("\\") &&
                !path.Contains(":") && !path.Contains("//") &&
                !path.Any(char.IsControl);
        }
        private static string Float(float value)
            => value.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
        private static string Vec3(Vector3 v)=>Float(v.x)+","+Float(v.y)+","+Float(v.z);
        private static string QuaternionText(Quaternion q)
            => Float(q.x)+","+Float(q.y)+","+Float(q.z)+","+Float(q.w);
        private static string CleanKey(string text)
            => Uri.EscapeDataString(text??"");
        private static void Add(List<HprPrefabValue> list,string key,string value)
        {
            if(list.Count>=MaxValues || key.Length>1100 || value==null || value.Length>1100)
                throw new InvalidOperationException("Snapshot value capacity exceeded.");
            list.Add(new HprPrefabValue{key=key,value=value});
        }
        private static string RefKey(UnityEngine.Object obj)
        {
            if(obj==null)return "none";
            string guid;long localId;
            if(AssetDatabase.TryGetGUIDAndLocalFileIdentifier(obj,out guid,out localId) &&
                !string.IsNullOrEmpty(guid))return guid+":"+localId;
            // Never use per-process instance identifiers as cross-editor evidence.
            throw new InvalidOperationException("Unstable reference to a non-persistent Unity object.");
        }
        private static void Visit(GameObject obj,string hierarchy,List<HprPrefabValue> list,
            ref int unsupported)
        {
            Add(list,hierarchy+"/@name",obj.name);
            Add(list,hierarchy+"/@active",obj.activeSelf ? "true":"false");
            Add(list,hierarchy+"/@layer",obj.layer.ToString());
            Add(list,hierarchy+"/@tag",obj.tag);
            Add(list,hierarchy+"/@static",obj.isStatic ? "true":"false");
            var transform=obj.transform;
            Add(list,hierarchy+"/Transform/position",Vec3(transform.localPosition));
            Add(list,hierarchy+"/Transform/rotation",QuaternionText(transform.localRotation));
            Add(list,hierarchy+"/Transform/scale",Vec3(transform.localScale));
            var byType=new Dictionary<string,int>(Order);
            foreach(var part in obj.GetComponents<Component>())
            {
                if(part==null)
                    throw new InvalidOperationException("Prefab has a missing script component.");
                string type=part.GetType().FullName??part.GetType().Name;
                int ordinal;
                byType.TryGetValue(type,out ordinal);
                byType[type]=ordinal+1;
                string key=hierarchy+"/Component/"+CleanKey(type)+"["+ordinal+"]";
                Add(list,key+"/type",type);
                if(part is Transform)continue;
                if(part is Renderer)
                {
                    var renderer=(Renderer)part;
                    Add(list,key+"/enabled",renderer.enabled ? "true":"false");
                    Add(list,key+"/materials-count",renderer.sharedMaterials.Length.ToString());
                    var materials=renderer.sharedMaterials;
                    for(int i=0;i<materials.Length;i++)
                        Add(list,key+"/material["+i+"]",RefKey(materials[i]));
                    Add(list,key+"/receiveShadows",renderer.receiveShadows ? "true":"false");
                    if(part is SkinnedMeshRenderer)
                        Add(list,key+"/skinnedMesh",RefKey(((SkinnedMeshRenderer)part).sharedMesh));
                    if(part is SpriteRenderer)
                        Add(list,key+"/sprite",RefKey(((SpriteRenderer)part).sprite));
                }
                else if(part is MeshFilter)
                    Add(list,key+"/sharedMesh",RefKey(((MeshFilter)part).sharedMesh));
                else if(part is TextMesh)
                {
                    var text=(TextMesh)part;
                    Add(list,key+"/text",text.text);
                    Add(list,key+"/font",RefKey(text.font));
                    Add(list,key+"/fontSize",text.fontSize.ToString());
                    Add(list,key+"/characterSize",Float(text.characterSize));
                    Add(list,key+"/fontStyle",text.fontStyle.ToString());
                    Add(list,key+"/anchor",text.anchor.ToString());
                    Add(list,key+"/alignment",text.alignment.ToString());
                    Add(list,key+"/color",Float(text.color.r)+","+Float(text.color.g)+","+
                        Float(text.color.b)+","+Float(text.color.a));
                }
                else if(part is Animator)
                {
                    var animator=(Animator)part;
                    Add(list,key+"/enabled",animator.enabled ? "true":"false");
                    Add(list,key+"/controller",RefKey(animator.runtimeAnimatorController));
                    Add(list,key+"/avatar",RefKey(animator.avatar));
                    Add(list,key+"/rootMotion",animator.applyRootMotion ? "true":"false");
                    Add(list,key+"/cullingMode",animator.cullingMode.ToString());
                }
                else if(part is Collider)
                {
                    var collider=(Collider)part;
                    Add(list,key+"/enabled",collider.enabled ? "true":"false");
                    Add(list,key+"/trigger",collider.isTrigger ? "true":"false");
                    if(collider is BoxCollider)
                    {
                        var box=(BoxCollider)collider;
                        Add(list,key+"/center",Vec3(box.center));
                        Add(list,key+"/size",Vec3(box.size));
                    }
                    else if(collider is SphereCollider)
                    {
                        var sphere=(SphereCollider)collider;
                        Add(list,key+"/center",Vec3(sphere.center));
                        Add(list,key+"/radius",Float(sphere.radius));
                    }
                    else if(collider is MeshCollider)
                        Add(list,key+"/mesh",RefKey(((MeshCollider)collider).sharedMesh));
                }
                else if(part is Rigidbody)
                {
                    var body=(Rigidbody)part;
                    Add(list,key+"/mass",Float(body.mass));
                    Add(list,key+"/kinematic",body.isKinematic ? "true":"false");
                    Add(list,key+"/gravity",body.useGravity ? "true":"false");
                }
                else
                {
                    unsupported++;
                    Add(list,key+"/coverage","COMPONENT_TYPE_RECORDED_VALUES_NOT_COVERED");
                }
            }
            for(int i=0;i<transform.childCount;i++)
            {
                var child=transform.GetChild(i);
                Visit(child.gameObject,hierarchy+"/"+i.ToString("D4")+"-"+CleanKey(child.name),list,ref unsupported);
            }
        }

        public static HprPrefabReceipt Scan(string paths,Func<int,int,bool> cancel=null)
        {
            var names=ValidatePaths(paths);
            var report=new HprPrefabReceipt{unityVersion=Application.unityVersion,
                status="INCOMPLETE",incomplete=true,failureReason="",
                inputs=new HprPrefabInput[0],dependencies=new HprPrefabDependency[0],
                unverifiedDependencyPaths=new string[0],values=new HprPrefabValue[0],limitation=Scope};
            var files=new List<HprPrefabInput>();
            var dependencies=new Dictionary<string,HprPrefabDependency>(Order);
            var unverified=new HashSet<string>(Order);
            var rootNames=new HashSet<string>(names,Order);
            var values=new List<HprPrefabValue>();
            long total=0;
            int unsupported=0;
            string root=Path.GetFullPath(Directory.GetParent(Application.dataPath).FullName);
            for(int i=0;i<names.Length;i++)
            {
                if(cancel!=null && cancel(i,names.Length))
                {report.failureReason="Canceled; no complete evidence.";return report;}
                string path=names[i];
                if(!File.Exists(Path.Combine(root,path)) ||
                    AssetDatabase.LoadAssetAtPath<GameObject>(path)==null)
                {report.failureReason="Missing or unimported prefab: "+path;return report;}
                GameObject contents=null;
                try
                {
                    files.Add(new HprPrefabInput{path=path,
                        sourceSha256=Sha256(Path.Combine(root,path),ref total,root),
                        metaSha256=Sha256(Path.Combine(root,path+".meta"),ref total,root)});
                    // Capture transitive referenced source inputs, not only prefab YAML.
                    // AssetDatabase may report package or built-in pseudo-assets: record
                    // their paths as unverified and never claim a clean input match.
                    var referenced=AssetDatabase.GetDependencies(path,true);
                    foreach(string dep in referenced.OrderBy(v=>v,Order))
                    {
                        if(string.IsNullOrEmpty(dep) || rootNames.Contains(dep))continue;
                        if(!RealAssetPath(dep) ||
                            !File.Exists(Path.Combine(root,dep)) ||
                            !File.Exists(Path.Combine(root,dep+".meta")))
                        {
                            if(dep.Length>500)
                                throw new InvalidOperationException("Unverifiable dependency path too long.");
                            unverified.Add(dep);
                            if(unverified.Count>MaxUnverifiedDependencyPaths)
                                throw new InvalidOperationException("Unverifiable dependency list too large.");
                            continue;
                        }
                        if(dependencies.ContainsKey(dep))continue;
                        if(dependencies.Count>=MaxDependencies)
                            throw new InvalidOperationException("Referenced dependency scan limit exceeded.");
                        string guid=AssetDatabase.AssetPathToGUID(dep);
                        if(string.IsNullOrEmpty(guid) || guid.Length!=32)
                            throw new InvalidOperationException("Referenced source has no stable Unity GUID: "+dep);
                        dependencies.Add(dep,new HprPrefabDependency{path=dep,guid=guid,
                            sourceSha256=Sha256(Path.Combine(root,dep),ref total,root),
                            metaSha256=Sha256(Path.Combine(root,dep+".meta"),ref total,root)});
                    }
                    contents=PrefabUtility.LoadPrefabContents(path);
                    if(contents==null)throw new InvalidOperationException("Could not load isolated prefab contents.");
                    Visit(contents,"Prefab/"+CleanKey(path),values,ref unsupported);
                }
                catch(Exception error)
                {report.failureReason=path+": "+error.GetType().Name+" "+error.Message;return report;}
                finally
                {
                    if(contents!=null)PrefabUtility.UnloadPrefabContents(contents);
                }
            }
            values.Sort((a,b)=>Order.Compare(a.key,b.key));
            for(int i=1;i<values.Count;i++)
                if(values[i].key==values[i-1].key)
                {report.failureReason="Ambiguous component property identity.";return report;}
            report.inputs=files.ToArray();
            report.dependencies=dependencies.Values.OrderBy(v=>v.path,Order).ToArray();
            report.unverifiedDependencyPaths=unverified.OrderBy(v=>v,Order).ToArray();
            report.values=values.ToArray();
            report.valuesCaptured=values.Count;report.unsupportedComponents=unsupported;
            report.status="CAPTURED_COVERED_PREFAB_VALUES";report.incomplete=false;
            return report;
        }
        public static void ExportNew(HprPrefabReceipt report,string file)
        {
            if(report==null || report.incomplete || report.status!="CAPTURED_COVERED_PREFAB_VALUES" ||
                !Path.IsPathRooted(file))
                throw new ArgumentException("A complete original prefab snapshot and new absolute file path are required.");
            using(var stream=new FileStream(file,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(stream,new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report,true));
        }
    }

    /// <summary>Compare original editor-imported fields, never repair or rewrite a prefab.</summary>
    public static class HprPrefabStateCompare
    {
        public static void Validate(HprPrefabReceipt receipt)
        {
            if(receipt==null || receipt.schema!=2 || receipt.incomplete ||
                receipt.status!="CAPTURED_COVERED_PREFAB_VALUES" ||
                string.IsNullOrEmpty(receipt.unityVersion) || receipt.inputs==null ||
                receipt.dependencies==null || receipt.unverifiedDependencyPaths==null ||
                receipt.values==null || receipt.inputs.Length<1 ||
                receipt.dependencies.Length>HprPrefabStateScan.MaxDependencies ||
                receipt.unverifiedDependencyPaths.Length>HprPrefabStateScan.MaxUnverifiedDependencyPaths ||
                receipt.inputs.Length>HprPrefabStateScan.MaxPrefabs ||
                receipt.values.Length>HprPrefabStateScan.MaxValues ||
                receipt.valuesCaptured!=receipt.values.Length || receipt.unsupportedComponents<0)
                throw new ArgumentException("Incomplete or malformed prefab state receipt.");
            var seen=new HashSet<string>(StringComparer.Ordinal);
            foreach(var input in receipt.inputs)
            {
                if(input==null || HprPrefabStateScan.ValidatePaths(input.path).Length!=1 ||
                    !ShaValid(input.sourceSha256) || !ShaValid(input.metaSha256) || !seen.Add(input.path))
                    throw new ArgumentException("Invalid input prefab or source fingerprint.");
            }
            var inputs=new HashSet<string>(seen,StringComparer.Ordinal);
            seen.Clear();
            foreach(var dep in receipt.dependencies)
                if(dep==null || string.IsNullOrEmpty(dep.path) || dep.path.Length>500 ||
                    !dep.path.StartsWith("Assets/",StringComparison.Ordinal) ||
                    dep.path.Contains("..") || dep.path.Contains("\\") ||
                    dep.path.Contains(":") || dep.path.Contains("//") ||
                    dep.path.Any(char.IsControl) || inputs.Contains(dep.path) ||
                    !seen.Add(dep.path) || dep.guid==null || dep.guid.Length!=32 ||
                    !dep.guid.All(c=>(c>='0'&&c<='9')||(c>='a'&&c<='f')) ||
                    !ShaValid(dep.sourceSha256) || !ShaValid(dep.metaSha256))
                    throw new ArgumentException("Invalid or duplicate referenced dependency evidence.");
            foreach(string unknown in receipt.unverifiedDependencyPaths)
                if(string.IsNullOrEmpty(unknown) || unknown.Length>500 ||
                    inputs.Contains(unknown) || !seen.Add(unknown))
                    throw new ArgumentException("Invalid, duplicate or ambiguous unverified dependency.");
            seen.Clear();
            var prefixes=receipt.inputs.Select(input=>"Prefab/"+Uri.EscapeDataString(input.path)+"/")
                .ToArray();
            foreach(var value in receipt.values)
                if(value==null || string.IsNullOrEmpty(value.key) || value.key.Length>1100 ||
                    value.value==null || value.value.Length>1100 || !seen.Add(value.key) ||
                    !prefixes.Any(prefix=>value.key.StartsWith(prefix,StringComparison.Ordinal)))
                    throw new ArgumentException("Malformed, out-of-scope or duplicate imported prefab field.");
        }
        private static bool ShaValid(string hash)
            => hash!=null && hash.Length==64 && hash.All(c=>(c>='0'&&c<='9')||(c>='a'&&c<='f'));
        public static HprPrefabComparison Compare(HprPrefabReceipt first,HprPrefabReceipt second)
        {
            Validate(first);Validate(second);
            if(first.unityVersion==second.unityVersion)
                throw new ArgumentException("Two distinct installed Unity Editor versions are required.");
            var a=first.inputs.ToDictionary(v=>v.path,StringComparer.Ordinal);
            var b=second.inputs.ToDictionary(v=>v.path,StringComparer.Ordinal);
            if(!a.Keys.OrderBy(v=>v,StringComparer.Ordinal).SequenceEqual(
                    b.Keys.OrderBy(v=>v,StringComparer.Ordinal)))
                throw new ArgumentException("The original two prefab scopes must match exactly.");
            var sourceDiff=a.Keys.Where(k=>a[k].sourceSha256!=b[k].sourceSha256 ||
                a[k].metaSha256!=b[k].metaSha256).OrderBy(k=>k,StringComparer.Ordinal).ToArray();
            var ad=first.dependencies.ToDictionary(v=>v.path,StringComparer.Ordinal);
            var bd=second.dependencies.ToDictionary(v=>v.path,StringComparer.Ordinal);
            var dependencyDiff=ad.Keys.Union(bd.Keys,StringComparer.Ordinal).Where(k=>
                !ad.ContainsKey(k) || !bd.ContainsKey(k) ||
                ad[k].guid!=bd[k].guid || ad[k].sourceSha256!=bd[k].sourceSha256 ||
                ad[k].metaSha256!=bd[k].metaSha256).OrderBy(k=>k,StringComparer.Ordinal).ToArray();
            var unknown=first.unverifiedDependencyPaths.Union(second.unverifiedDependencyPaths,
                StringComparer.Ordinal).OrderBy(k=>k,StringComparer.Ordinal).ToArray();
            var x=first.values.ToDictionary(v=>v.key,v=>v.value,StringComparer.Ordinal);
            var y=second.values.ToDictionary(v=>v.key,v=>v.value,StringComparer.Ordinal);
            var removed=x.Keys.Except(y.Keys,StringComparer.Ordinal).OrderBy(k=>k,StringComparer.Ordinal).ToArray();
            var added=y.Keys.Except(x.Keys,StringComparer.Ordinal).OrderBy(k=>k,StringComparer.Ordinal).ToArray();
            var changed=x.Keys.Intersect(y.Keys,StringComparer.Ordinal).Where(k=>x[k]!=y[k])
                .OrderBy(k=>k,StringComparer.Ordinal).ToArray();
            var result=new HprPrefabComparison{firstUnityVersion=first.unityVersion,
                secondUnityVersion=second.unityVersion,sourceDifferences=sourceDiff,
                dependencyDifferences=dependencyDiff,unverifiedDependencyPaths=unknown,
                removedValueKeys=removed,addedValueKeys=added,changedValueKeys=changed,
                unsupportedComponents=first.unsupportedComponents+second.unsupportedComponents,
                limitation="Only declared covered imported prefab fields and verified referenced Assets/ " +
                    "input bytes; built-in/package inputs, project settings and Player behavior may be unverified."};
            result.status=sourceDiff.Length>0 ? "SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE" :
                dependencyDiff.Length>0 ? "DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE" :
                unknown.Length>0 ? "DEPENDENCIES_UNVERIFIED_NO_EDITOR_INFERENCE" :
                removed.Length+added.Length+changed.Length>0 ? "REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES" :
                result.unsupportedComponents>0 ? "COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS" :
                "MATCHED_COVERED_IMPORTED_PREFAB_VALUES";
            return result;
        }
        public static void ExportNew(HprPrefabComparison comparison,string absolutePath)
        {
            if(comparison==null || !Path.IsPathRooted(absolutePath) ||
                (comparison.status!="SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE" &&
                 comparison.status!="DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE" &&
                 comparison.status!="DEPENDENCIES_UNVERIFIED_NO_EDITOR_INFERENCE" &&
                 comparison.status!="REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES" &&
                 comparison.status!="COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS" &&
                 comparison.status!="MATCHED_COVERED_IMPORTED_PREFAB_VALUES"))
                throw new ArgumentException("A complete comparison and new absolute file path are required.");
            using(var file=new FileStream(absolutePath,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(file,new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(comparison,true));
        }
        public static HprPrefabReceipt ReadReceipt(string absolutePath)
        {
            if(!Path.IsPathRooted(absolutePath) || !File.Exists(absolutePath) ||
                new FileInfo(absolutePath).Length>8000000L)
                throw new ArgumentException("Missing or oversized original prefab receipt.");
            var receipt=JsonUtility.FromJson<HprPrefabReceipt>(File.ReadAllText(absolutePath));
            Validate(receipt);return receipt;
        }
    }

    public sealed class HprPrefabStateParityWindow : EditorWindow
    {
        private string paths="Assets/YourPublisherAssets/Example.prefab";
        private string first="",second="",notice="Enter actual publisher prefab paths; no files will be modified.";
        private HprPrefabReceipt captured;
        private HprPrefabComparison comparison;
        private Vector2 scroll;
        private GUIStyle multilinePaths;

        private static string ReceiptLabel(string file)
        {
            if(string.IsNullOrEmpty(file))return "Not selected";
            string parent=Path.GetFileName(Path.GetDirectoryName(file));
            return parent+" / "+Path.GetFileName(file);
        }
        [MenuItem("Tools/HPR/Imported Prefab State Parity")]
        public static void Open()
        {
            var window=GetWindow<HprPrefabStateParityWindow>("Imported Prefab State Parity");
            window.minSize=new Vector2(690f,480f);window.Show();
        }
        private void OnGUI()
        {
            GUILayout.Label("IMPORTED PREFAB STATE PARITY",EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Compare a bounded subset of actual loaded prefab values in two independent Unity Editors. " +
                "The original file contents must match. This is not a complete serialization, gameplay or Player build test.",MessageType.Info);
            if(multilinePaths==null)
                multilinePaths=new GUIStyle(EditorStyles.textArea){wordWrap=true};
            EditorGUILayout.LabelField("Original prefab paths — one per line, or separate with semicolons:",
                EditorStyles.wordWrappedLabel);
            paths=EditorGUILayout.TextArea(paths,multilinePaths,GUILayout.MinHeight(80f));
            if(GUILayout.Button("Scan imported prefabs (read only)",GUILayout.Height(30)))
            {
                captured=null;comparison=null;
                try
                {
                    captured=HprPrefabStateScan.Scan(paths,(i,n)=>
                        EditorUtility.DisplayCancelableProgressBar("Imported Prefab State Parity",
                            "Read-only prefab inspection "+(i+1)+" / "+n,n>0 ? (float)i/n:0f));
                    notice=captured.incomplete ? "INCOMPLETE: "+captured.failureReason :
                        "Captured "+captured.valuesCaptured+" covered values; "+
                        captured.dependencies.Length+" source dependencies verified; "+
                        captured.unverifiedDependencyPaths.Length+" not fully verified; "+
                        captured.unsupportedComponents+" component types not fully inspected.";
                }
                catch(Exception ex){notice="No scan: "+ex.Message;}
                finally{EditorUtility.ClearProgressBar();}
            }
            if(captured!=null && !captured.incomplete && GUILayout.Button("Export NEW prefab snapshot JSON"))
            {
                var file=EditorUtility.SaveFilePanel("Save captured prefab state","","prefab-state.json","json");
                if(!string.IsNullOrEmpty(file))try{HprPrefabStateScan.ExportNew(captured,file);notice="New snapshot exported.";}
                catch(Exception ex){notice="Export refused: "+ex.Message;}
            }
            EditorGUILayout.LabelField(new GUIContent("First Unity snapshot: "+ReceiptLabel(first),first),
                EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Choose first existing snapshot"))
            {
                var file=EditorUtility.OpenFilePanel("First prefab snapshot","","json");
                if(!string.IsNullOrEmpty(file)){first=file;comparison=null;}
            }
            EditorGUILayout.LabelField(new GUIContent("Second Unity snapshot: "+ReceiptLabel(second),second),
                EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Choose second existing snapshot"))
            {
                var file=EditorUtility.OpenFilePanel("Second prefab snapshot","","json");
                if(!string.IsNullOrEmpty(file)){second=file;comparison=null;}
            }
            if(GUILayout.Button("Compare genuine imported prefab states",GUILayout.Height(30)))
            {
                comparison=null;
                try
                {
                    comparison=HprPrefabStateCompare.Compare(HprPrefabStateCompare.ReadReceipt(first),
                        HprPrefabStateCompare.ReadReceipt(second));
                    notice=comparison.status=="MATCHED_COVERED_IMPORTED_PREFAB_VALUES" ?
                        "Covered values and checked source dependencies match. Review other fields and Player builds." :
                        comparison.status=="COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS" ?
                        "Covered values match, but "+comparison.unsupportedComponents+
                        " custom or other component occurrences contain UNINSPECTED values. Do not treat as full compatibility." :
                        comparison.status=="SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE" ?
                        "Original prefab files differ. Cannot attribute differences to a Unity version." :
                        comparison.status=="DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE" ?
                        "Referenced asset or importer bytes differ. Unity-version attribution is unsafe." :
                        comparison.status=="DEPENDENCIES_UNVERIFIED_NO_EDITOR_INFERENCE" ?
                        "Some package or built-in dependencies cannot be checked. No clean result." :
                        "Imported covered values differ. Inspect the affected keys before a release.";
                }
                catch(Exception ex){notice="Comparison refused: "+ex.Message;}
            }
            EditorGUILayout.HelpBox(notice,comparison!=null && comparison.status!=
                "MATCHED_COVERED_IMPORTED_PREFAB_VALUES" ? MessageType.Warning:MessageType.None);
            if(comparison!=null)
            {
                EditorGUILayout.LabelField("Comparison: "+notice,EditorStyles.boldLabel);
                EditorGUILayout.LabelField(comparison.status,EditorStyles.miniLabel);
                EditorGUILayout.LabelField("Original source changes: "+comparison.sourceDifferences.Length+
                    " | Dependency changes: "+comparison.dependencyDifferences.Length+
                    " | Unverified dependencies: "+comparison.unverifiedDependencyPaths.Length,
                    EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField("Component occurrences with uninspected values: "+
                    comparison.unsupportedComponents,EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField("Added: "+comparison.addedValueKeys.Length+" | Removed: "+
                    comparison.removedValueKeys.Length+" | Changed: "+comparison.changedValueKeys.Length,
                    EditorStyles.wordWrappedLabel);
                if(GUILayout.Button("Export NEW comparison JSON"))
                {
                    var p=EditorUtility.SaveFilePanel("Save imported prefab differences","",
                        "imported-prefab-differences.json","json");
                    if(!string.IsNullOrEmpty(p))try{HprPrefabStateCompare.ExportNew(comparison,p);notice="New report saved.";}
                    catch(Exception ex){notice="No original report replaced: "+ex.Message;}
                }
                scroll=EditorGUILayout.BeginScrollView(scroll);
                foreach(var key in comparison.sourceDifferences.Take(12))
                    EditorGUILayout.LabelField("Different source: "+key,EditorStyles.wordWrappedLabel);
                foreach(var key in comparison.dependencyDifferences.Take(12))
                    EditorGUILayout.LabelField("Referenced source changed: "+key,EditorStyles.wordWrappedLabel);
                foreach(var key in comparison.unverifiedDependencyPaths.Take(12))
                    EditorGUILayout.LabelField("Unverified dependency: "+key,EditorStyles.wordWrappedLabel);
                foreach(var key in comparison.changedValueKeys.Take(24))
                    EditorGUILayout.LabelField("Changed imported value: "+key,EditorStyles.wordWrappedLabel);
                foreach(var key in comparison.addedValueKeys.Take(12))
                    EditorGUILayout.LabelField("Added: "+key,EditorStyles.wordWrappedLabel);
                foreach(var key in comparison.removedValueKeys.Take(12))
                    EditorGUILayout.LabelField("Removed: "+key,EditorStyles.wordWrappedLabel);
                EditorGUILayout.HelpBox(comparison.limitation,MessageType.Warning);
                EditorGUILayout.EndScrollView();
            }
        }
    }
}
#endif
