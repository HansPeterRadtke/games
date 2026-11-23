using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEngine;

// Original opt-in Unity Player diagnostic. No package manager, network calls, or asset mutation.
namespace HPR.PlayerReferenceProbe
{
    [Serializable]
    public sealed class HprReferenceCase
    {
        public string id="case-one";
        public ScriptableObject source;
        // Optional non-pinning lookup: path relative to Resources, with no extension.
        // Leave source unassigned when using this mode, to avoid masking build inclusion.
        public string resourcesPath="";
        public string fieldName="itemPrefab";
    }

    [Serializable]
    public sealed class HprReferenceResult
    {
        public string id;
        public string assetName;
        public string fieldName;
        public string sourceLookup;
        public string status;
        public string referencedType;
        public string referencedName;
    }

    [Serializable]
    public sealed class HprReferenceReport
    {
        public int schema=2;
        public string origin;
        public string unityVersion;
        public string platform;
        public string status;
        public int checkedCount;
        public int assignedCount;
        public int missingCount;
        public int unsupportedCount;
        public string limitation;
        public HprReferenceResult[] cases;
    }

    [Serializable]
    public sealed class HprReferenceComparison
    {
        public int schema=2;
        public string status;
        public int checkedCount;
        public string[] playerMissingCaseIds;
        public string[] playerSourceMissingCaseIds;
        public string[] otherDifferences;
        public string limitation;
    }

    public static class HprReferenceInspector
    {
        public const int MaxCases=64;
        public const string Scope="Only expressly selected direct UnityEngine.Object fields on ScriptableObjects. " +
            "Does not scan every serialized object, collection, Addressables loading, platform stripping, " +
            "runtime scene ownership, dynamically acquired references, or other game behavior. " +
            "An intentionally empty field must not be described as broken solely because it is null. " +
            "Direct scene ScriptableObject references can themselves change Player asset reachability; " +
            "for Resources sources use a path-only probe with source unassigned. A matching type/name " +
            "does not prove identical Unity asset GUID or all runtime behavior.";
        private static bool SafeName(string value)
        {
            return !string.IsNullOrWhiteSpace(value) && value.Length<=80 &&
                value.All(c=>char.IsLetterOrDigit(c)||c=='-'||c=='_'||c=='.');
        }
        private static bool SafeResourcesPath(string path)
        {
            return !string.IsNullOrWhiteSpace(path) && path.Length<=180 &&
                !path.StartsWith("/",StringComparison.Ordinal) &&
                !path.EndsWith("/",StringComparison.Ordinal) &&
                !path.Contains("..") && !path.Contains("\\") &&
                !path.Contains(":") && !path.Contains("//") &&
                !path.EndsWith(".asset",StringComparison.OrdinalIgnoreCase) &&
                !path.EndsWith(".prefab",StringComparison.OrdinalIgnoreCase) &&
                !path.Any(char.IsControl);
        }
        private static FieldInfo SelectField(Type type,string fieldName)
        {
            for(var cursor=type;cursor!=null && cursor!=typeof(ScriptableObject) &&
                cursor!=typeof(UnityEngine.Object);cursor=cursor.BaseType)
            {
                var field=cursor.GetField(fieldName,BindingFlags.Public|BindingFlags.NonPublic|
                    BindingFlags.Instance|BindingFlags.DeclaredOnly);
                if(field==null)continue;
                if(field.IsStatic || field.IsNotSerialized || field.IsInitOnly ||
                    !(field.IsPublic || Attribute.IsDefined(field,typeof(SerializeField))) ||
                    !typeof(UnityEngine.Object).IsAssignableFrom(field.FieldType))return null;
                return field;
            }
            return null;
        }
        public static HprReferenceReport Inspect(HprReferenceCase[] checks,string origin)
        {
            if(origin!="EDITOR" && origin!="PLAYER")
                throw new ArgumentException("Explicit Editor or Player origin required.");
            if(checks==null || checks.Length==0 || checks.Length>MaxCases)
                throw new ArgumentException("Choose between one and sixty-four explicit reference checks.");
            var used=new HashSet<string>(StringComparer.Ordinal);
            var found=new List<HprReferenceResult>();
            foreach(var check in checks)
            {
                if(check==null || !SafeName(check.id) || !SafeName(check.fieldName) ||
                    !used.Add(check.id))
                    throw new ArgumentException("Invalid or repeated case ID or serialized field name.");
                bool useResources=!string.IsNullOrEmpty(check.resourcesPath);
                if(useResources && (check.source!=null || !SafeResourcesPath(check.resourcesPath)))
                    throw new ArgumentException("Resources-mode cases require a valid path and no direct source pin.");
                var line=new HprReferenceResult{id=check.id,fieldName=check.fieldName,
                    sourceLookup=useResources ? "RESOURCES:"+check.resourcesPath : "DIRECT_SCENE",
                    assetName="",referencedName="",referencedType=""};
                try
                {
                    ScriptableObject source=useResources ?
                        Resources.Load<ScriptableObject>(check.resourcesPath) : check.source;
                    line.assetName=source==null ? (useResources ? check.resourcesPath : "") : source.name;
                    if(source==null)line.status=useResources ? "SOURCE_NOT_LOADED" : "SOURCE_NOT_ASSIGNED";
                    else
                    {
                        var field=SelectField(source.GetType(),check.fieldName);
                        if(field==null)line.status="FIELD_UNSUPPORTED_OR_NOT_SERIALIZED";
                        else
                        {
                            var value=field.GetValue(source) as UnityEngine.Object;
                            if(value==null)line.status="REFERENCE_NULL_OR_UNSET";
                            else
                            {
                                line.status="ASSIGNED";
                                line.referencedType=value.GetType().FullName;
                                line.referencedName=value.name;
                            }
                        }
                    }
                }
                catch(Exception){line.status="INSPECTION_INCOMPLETE";}
                found.Add(line);
            }
            var r=new HprReferenceReport{origin=origin,unityVersion=Application.unityVersion,
                platform=Application.platform.ToString(),cases=found.ToArray(),
                checkedCount=found.Count,assignedCount=found.Count(v=>v.status=="ASSIGNED"),
                missingCount=found.Count(v=>v.status=="SOURCE_NOT_ASSIGNED" ||
                    v.status=="SOURCE_NOT_LOADED" || v.status=="REFERENCE_NULL_OR_UNSET"),
                unsupportedCount=found.Count(v=>v.status=="FIELD_UNSUPPORTED_OR_NOT_SERIALIZED" ||
                    v.status=="INSPECTION_INCOMPLETE"),limitation=Scope};
            r.status=r.unsupportedCount>0 ? "INSPECTION_INCOMPLETE" :
                r.missingCount>0 ? "NULL_OR_UNSET_SELECTED_REFERENCE" :
                "ALL_SELECTED_DIRECT_REFERENCES_ASSIGNED";
            return r;
        }
        public static void Validate(HprReferenceReport report)
        {
            if(report==null || report.schema!=2 || (report.origin!="EDITOR" && report.origin!="PLAYER") ||
                string.IsNullOrEmpty(report.unityVersion) || report.cases==null ||
                report.cases.Length==0 || report.cases.Length>MaxCases ||
                report.checkedCount!=report.cases.Length || report.limitation!=Scope)
                throw new ArgumentException("Unsupported or incomplete reference report.");
            var ids=new HashSet<string>(StringComparer.Ordinal);
            int assigned=0,missing=0,unsupported=0;
            foreach(var entry in report.cases)
            {
                if(entry==null || !SafeName(entry.id) || !SafeName(entry.fieldName) ||
                    !ids.Add(entry.id) || entry.assetName==null || entry.referencedName==null ||
                    entry.referencedType==null || entry.sourceLookup==null ||
                    !(entry.sourceLookup=="DIRECT_SCENE" ||
                      (entry.sourceLookup.StartsWith("RESOURCES:",StringComparison.Ordinal) &&
                       SafeResourcesPath(entry.sourceLookup.Substring(10)))) ||
                    entry.assetName.Length>256 ||
                    entry.referencedName.Length>256 || entry.referencedType.Length>256)
                    throw new ArgumentException("Invalid or repeated serialized reference entry.");
                if(entry.status=="ASSIGNED")
                {
                    if(string.IsNullOrEmpty(entry.referencedType) ||
                        string.IsNullOrEmpty(entry.referencedName))
                        throw new ArgumentException("Assigned reference without identity.");
                    assigned++;
                }
                else if(entry.status=="REFERENCE_NULL_OR_UNSET" ||
                    entry.status=="SOURCE_NOT_ASSIGNED" ||
                    entry.status=="SOURCE_NOT_LOADED")
                {
                    if((entry.status=="SOURCE_NOT_LOADED" &&
                        !entry.sourceLookup.StartsWith("RESOURCES:",StringComparison.Ordinal)) ||
                       (entry.status=="SOURCE_NOT_ASSIGNED" && entry.sourceLookup!="DIRECT_SCENE"))
                        throw new ArgumentException("Source-missing status inconsistent with lookup mode.");
                    missing++;
                }
                else if(entry.status=="FIELD_UNSUPPORTED_OR_NOT_SERIALIZED" ||
                    entry.status=="INSPECTION_INCOMPLETE")unsupported++;
                else throw new ArgumentException("Unsupported reference status.");
            }
            if(report.assignedCount!=assigned || report.missingCount!=missing ||
                report.unsupportedCount!=unsupported ||
                report.status!=(unsupported>0?"INSPECTION_INCOMPLETE":
                missing>0?"NULL_OR_UNSET_SELECTED_REFERENCE":
                "ALL_SELECTED_DIRECT_REFERENCES_ASSIGNED"))
                throw new ArgumentException("Reference report summary inconsistent with original entries.");
        }
        public static HprReferenceComparison Compare(HprReferenceReport editor,HprReferenceReport player)
        {
            Validate(editor);Validate(player);
            if(editor.origin!="EDITOR" || player.origin!="PLAYER")
                throw new ArgumentException("Compare an actual Editor baseline against an actual Player report.");
            if(editor.unityVersion!=player.unityVersion)
                throw new ArgumentException("Editor and Player must use the identical Unity version.");
            var a=editor.cases.ToDictionary(v=>v.id,StringComparer.Ordinal);
            var b=player.cases.ToDictionary(v=>v.id,StringComparer.Ordinal);
            if(!a.Keys.OrderBy(v=>v,StringComparer.Ordinal).SequenceEqual(
                b.Keys.OrderBy(v=>v,StringComparer.Ordinal)))
                throw new ArgumentException("Editor and Player case IDs must match exactly.");
            var lost=new List<string>();var sourceLost=new List<string>();
            var changed=new List<string>();bool incomplete=false;
            foreach(var id in a.Keys.OrderBy(v=>v,StringComparer.Ordinal))
            {
                var left=a[id];var right=b[id];
                if(left.fieldName!=right.fieldName || left.sourceLookup!=right.sourceLookup ||
                    (left.assetName!=right.assetName && right.status!="SOURCE_NOT_LOADED") ||
                    left.status=="INSPECTION_INCOMPLETE" || right.status=="INSPECTION_INCOMPLETE" ||
                    left.status=="FIELD_UNSUPPORTED_OR_NOT_SERIALIZED" ||
                    right.status=="FIELD_UNSUPPORTED_OR_NOT_SERIALIZED")
                {incomplete=true;changed.Add(id);continue;}
                if(left.status=="ASSIGNED" && right.status=="SOURCE_NOT_LOADED" &&
                    left.sourceLookup.StartsWith("RESOURCES:",StringComparison.Ordinal))
                    sourceLost.Add(id);
                else if(left.status=="ASSIGNED" && right.status=="REFERENCE_NULL_OR_UNSET")
                    lost.Add(id);
                else if(left.status!=right.status || left.referencedName!=right.referencedName ||
                    left.referencedType!=right.referencedType)changed.Add(id);
            }
            return new HprReferenceComparison{
                status=incomplete ? "REVIEW_INCOMPLETE_SELECTED_FIELDS" :
                    sourceLost.Count>0 ? "PLAYER_SCRIPTABLEOBJECT_SOURCE_NOT_LOADED" :
                    lost.Count>0 ? "PLAYER_REFERENCE_LOSS_REPRODUCED" :
                    changed.Count>0 ? "REVIEW_EDITOR_PLAYER_REFERENCE_DIFFERENCES" :
                    editor.missingCount+player.missingCount>0 ? "CONSISTENT_NULL_OR_UNSET_FIELDS" :
                    "MATCHED_SELECTED_DIRECT_REFERENCES",
                checkedCount=a.Count,playerMissingCaseIds=lost.ToArray(),
                playerSourceMissingCaseIds=sourceLost.ToArray(),otherDifferences=changed.ToArray(),
                limitation=Scope};
        }
        public static void WriteNew(HprReferenceReport report,string path)
        {
            Validate(report);
            if(string.IsNullOrEmpty(path) || !Path.IsPathRooted(path))
                throw new ArgumentException("A new absolute filename is required.");
            using(var stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer=new StreamWriter(stream,new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report,true));
        }
    }

    [DisallowMultipleComponent]
    public sealed class HprPlayerReferenceProbe : MonoBehaviour
    {
        public HprReferenceCase[] checks=Array.Empty<HprReferenceCase>();
        public bool writePrivateLocalReport=true;
        // Default false preserves the behavior of scenes saved before this field existed.
        public bool manualOnly=false;
        // Bounds output even if an integration accidentally calls CaptureNow each frame.
        public int maxCaptures=8;
        private int captureCount;
        private bool limitWarningEmitted;

        private void Start()
        {
            if(!manualOnly)CaptureNow();
        }

        // Call from a game event after the suspected loss. Returns true if a receipt was
        // recorded, NOT if every inspected reference was assigned or the game is healthy.
        public bool CaptureNow()
        {
            if(Application.isEditor)return false; // Editor baseline comes from the Editor window.
            var limit=maxCaptures<=0 ? 8 : Mathf.Clamp(maxCaptures,1,32);
            if(captureCount>=limit)
            {
                if(!limitWarningEmitted)
                {
                    limitWarningEmitted=true;
                    Debug.LogWarning("HPR_PLAYER_REFERENCE_CAPTURE_LIMIT_REACHED; no further reports recorded");
                }
                return false;
            }
            captureCount++; // Failed inspections also count, preventing unlimited repeated errors.
            try
            {
                var report=HprReferenceInspector.Inspect(checks,"PLAYER");
                Debug.Log("HPR_PLAYER_REFERENCE_RECEIPT="+JsonUtility.ToJson(report));
                if(writePrivateLocalReport)
                {
                    string folder=Application.persistentDataPath;
                    if(string.IsNullOrEmpty(folder))
                        throw new IOException("Player persistent data path unavailable.");
                    string path=Path.Combine(folder,"HprPlayerReferenceProbe-"+
                        Guid.NewGuid().ToString("N")+".json");
                    HprReferenceInspector.WriteNew(report,path);
                    Debug.Log("HPR_PLAYER_REFERENCE_REPORT_CREATED="+path);
                }
                return true;
            }
            catch(Exception error)
            {
                Debug.LogError("HPR_PLAYER_REFERENCE_PROBE_INCOMPLETE="+error.GetType().Name);
                return false;
            }
        }
    }
}
