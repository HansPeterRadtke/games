using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using HPR.BuildSceneMatrix;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;

internal static class Program
{
    private static string root;
    private static int passed;
    private static readonly DateTimeOffset Capture = new DateTimeOffset(2026,11,25,9,15,33,TimeSpan.Zero);
    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
        passed++;
        Console.WriteLine("PASS " + message);
    }

    private static void Reject(Action action, string message)
    {
        bool rejected = false;
        try { action(); }
        catch (IOException) { rejected = true; }
        catch (InvalidDataException) { rejected = true; }
        catch (ArgumentException) { rejected = true; }
        catch (InvalidOperationException) { rejected = true; }
        Check(rejected, message);
    }

    private static HprSceneProfile Profile(string title = "Original", string id = "global",
        string source = "Shared scene list")
    {
        return new HprSceneProfile { Id = id, Title = title, Source = source,
            AssetPath = "Assets/Profiles/" + id + ".asset", Active = true };
    }

    private static void Add(HprSceneProfile p, string path, string guid, bool enabled = true, bool missing = false)
    {
        p.Rows.Add(new HprSceneRow { Path = path, Guid = guid, Name = Path.GetFileNameWithoutExtension(path),
            ListIndex = p.Rows.Count, BuildIndex = enabled ? p.EnabledCount : -1, Enabled = enabled, Missing = missing });
    }

    private static string P(string name) => Path.Combine(root, name);

    private static void CompareCases()
    {
        string id = new string('a',32);
        var a = Profile();
        Add(a,"Assets/Old/Main.unity",id);
        var b = Profile();
        Add(b,"Assets/New/Main.unity",id);
        var rename = HprSceneMatrix.Compare(a,b).Single();
        Check(rename.Different && rename.Warning && rename.ReferencePath == a.First &&
            rename.ComparedPath == b.First && rename.Path == b.First,"rename matched by GUID; navigation uses live path");

        b.Rows[0].Path = a.First;
        b.Rows[0].Missing = true;
        var lost = HprSceneMatrix.Compare(a,b).Single();
        Check(lost.Different && lost.Warning && lost.A == lost.B && lost.Issue.Contains("(compared)"),
            "reference becomes stale without build index changing");
        var restored = HprSceneMatrix.Compare(b,a).Single();
        Check(restored.Different && restored.Warning && restored.Issue.Contains("(reference)"),
            "historical missing reference becomes valid without index changing");
        b.Rows[0].Missing = false;
        Check(!HprSceneMatrix.Compare(a,b).Single().Different,"unchanged row is not drift");

        var absent = Profile();
        var disabled = Profile();
        Add(disabled,"Assets/Old/Main.unity",id,false);
        var d = HprSceneMatrix.Compare(absent,disabled).Single();
        Check(d.A == "Absent" && d.B == "Disabled" && d.Different,"absent and disabled are distinct");

        Add(b,"Assets/Second/Main.unity",new string('b',32));
        var names = HprSceneMatrix.Compare(a,b);
        Check(names.Count == 2 && names.All(x => x.Warning && x.Issue.Contains("Ambiguous")),
            "different enabled scene identities with duplicate names warned");
        Add(b,"Assets/Old/Main.unity",id);
        Check(HprSceneMatrix.Compare(a,b).Single(x=>x.Key=="guid:"+id).Issue.Contains("Repeated"),
            "repeated scene identity warned");
        var duplicate = Profile();
        Add(duplicate,"Assets/Old/Main.unity",id);
        Add(duplicate,"Assets/Alternate/Main.unity",id);
        var sameDuplicate = HprSceneMatrix.Compare(duplicate,duplicate).Single();
        Check(!sameDuplicate.Different && sameDuplicate.Warning &&
            sameDuplicate.Issue.Contains("Conflicting paths"),"identical malformed duplicate lists warned without false historical drift");
        var repeated = Profile();
        Add(repeated,a.First,id);
        Add(repeated,a.First,id);
        var repetition = HprSceneMatrix.Compare(a,repeated).Single();
        Check(repetition.Different && repetition.Issue.Contains("Repeated") &&
            !repetition.Issue.Contains("Path differs"),"duplicate count change is not falsely labelled a rename");
        var fallback = Profile();
        Add(fallback,"Assets/Unknown.unity","",true,true);
        Check(HprSceneMatrix.Compare(absent,fallback).Single().Key == "path:Assets/Unknown.unity",
            "missing identifier uses path identity");
        var unreadable = Profile();
        unreadable.Error = "Scan failed";
        Reject(()=>HprSceneMatrix.Compare(unreadable,b),"unreadable profile cannot be compared");
    }

    private static void SnapshotCases()
    {
        var a = Profile("Réal \"quoted\" – 初版", "global");
        Add(a,"Assets/Start.unity",new string('c',32));
        Add(a,"Assets/Other.unity",new string('d',32),false);
        Add(a,"Assets/Deleted.unity","",true,true);
        Add(a,"Assets/Start.unity",new string('c',32));
        var file = P("saved.hpr-scenes");
        HprSceneBaseline.SaveNew(file,a,Capture);
        byte[] bytes = File.ReadAllBytes(file);
        var saved = HprSceneBaseline.Load(file);
        Check(saved.CapturedUtc==Capture && saved.Profile.HistoricalCapturedUtc==Capture &&
            saved.Profile.Id==a.Id && saved.Profile.Title==a.Title && saved.Profile.AssetPath==a.AssetPath &&
            saved.Profile.Source==a.Source && !saved.Profile.Active,"snapshot round-trips identity, unicode, time and inactive history");
        Check(saved.Profile.Rows.Count==4 && saved.Profile.Rows.Zip(a.Rows,(x,y)=>
            x.Path==y.Path && x.Guid==y.Guid && x.Name==y.Name && x.ListIndex==y.ListIndex &&
            x.BuildIndex==y.BuildIndex && x.Enabled==y.Enabled && x.Missing==y.Missing).All(x=>x),
            "all scene data including duplicate/disabled/missing states preserved");
        Check(HprSceneMatrix.Compare(saved.Profile,a).All(x=>!x.Different),"snapshot matches original rows");
        Check(File.ReadAllBytes(file).SequenceEqual(bytes),"load leaves snapshot bytes unchanged");
        Reject(()=>HprSceneBaseline.SaveNew(file,a,Capture),"save refuses existing file");
        Check(File.ReadAllBytes(file).SequenceEqual(bytes),"refused overwrite leaves original bytes unchanged");
        a.Rows[0].Path="Assets/Renamed.unity";
        a.Rows[2].Missing=false;
        a.Source="Overrides global scenes";
        var drift=HprSceneMatrix.Compare(saved.Profile,a);
        Check(drift.Count(x=>x.Different)==2 && drift.Any(x=>x.ReferencePath=="Assets/Start.unity" &&
            x.ComparedPath=="Assets/Renamed.unity"),"saved reference detects subsequent rename and missing status change");
        var csv=P("drift.csv");
        HprSceneMatrix.ExportNewCsv(csv,saved.Profile,a);
        string text=File.ReadAllText(csv);
        Check(text.Contains("Reference snapshot UTC") && text.Contains(Capture.ToString("O",CultureInfo.InvariantCulture)) &&
            text.Contains("Profile asset identities") && text.Contains("Reference path: Assets/Start.unity"),
            "historical CSV carries timestamp, identity and previous path");
        Check(text.Contains("\"Scene sources\",\"Shared scene list\",\"Overrides global scenes\",\"Yes\""),
            "historical CSV marks inheritance-source drift");
        Reject(()=>HprSceneMatrix.ExportNewCsv(csv,saved.Profile,a),"comparison export refuses overwrite");

        var evil=Profile("\t=HYPERLINK(\"https://invalid.example\")");
        Add(evil,"=payload.unity",new string('e',32));
        var dangerous=Profile("＝1+1");
        HprSceneMatrix.ExportNewCsv(P("unsafe-cells.csv"),evil,dangerous);
        string csvText=File.ReadAllText(P("unsafe-cells.csv"));
        Check(csvText.Contains("\"'\t=HYPERLINK(") && csvText.Contains("\"'=payload.unity\"") &&
            csvText.Contains("\"'＝1+1\""),"imported strings guarded against spreadsheet formula interpretation");

        void Damaged(string name, byte[] data)
        {
            var path=P(name);
            File.WriteAllBytes(path,data);
            Reject(()=>HprSceneBaseline.Load(path),"reject "+name);
            Check(File.ReadAllBytes(path).SequenceEqual(data),"read-only rejection "+name);
        }
        var invalidMagic=(byte[])bytes.Clone();
        invalidMagic[0]=0;
        Damaged("bad-magic",invalidMagic);
        Damaged("truncated",bytes.Take(bytes.Length-1).ToArray());
        Damaged("trailing",bytes.Concat(new byte[]{1}).ToArray());
        var invalidLength=(byte[])bytes.Clone();
        Array.Copy(BitConverter.GetBytes(int.MaxValue),0,invalidLength,9,4);
        Damaged("oversized-field-length",invalidLength);
        var invalidUtf=(byte[])bytes.Clone();
        invalidUtf[13]=0xff;
        Damaged("invalid-utf8",invalidUtf);
        Damaged("oversized-file",new byte[4*1024*1024+1]);
        var invalidFlag=(byte[])bytes.Clone();
        invalidFlag[invalidFlag.Length-10]=2;
        Damaged("invalid-flag",invalidFlag);
        var invalidIndex=(byte[])bytes.Clone();
        Array.Copy(BitConverter.GetBytes(123),0,invalidIndex,invalidIndex.Length-4,4);
        Damaged("invalid-build-index",invalidIndex);

        var invalid=Profile();
        Add(invalid,"Assets/Test.unity","not-a-guid");
        Reject(()=>HprSceneBaseline.SaveNew(P("invalid.hpr-scenes"),invalid,Capture),"reject invalid GUID at save");
        Check(!File.Exists(P("invalid.hpr-scenes")),"invalid save creates no file");
        invalid.Rows[0].Guid=new string('f',32);
        invalid.Rows[0].ListIndex=10;
        Reject(()=>HprSceneBaseline.SaveNew(P("invalid.hpr-scenes"),invalid,Capture),"reject invalid list order at save");
        var giant=Profile(new string('x',32769));
        Reject(()=>HprSceneBaseline.SaveNew(P("large.hpr-scenes"),giant,Capture),"reject giant text before opening output");
        Check(!File.Exists(P("large.hpr-scenes")),"giant field leaves no partial file");
        var largeRows=Profile();
        for(int i=0;i<20001;i++) largeRows.Rows.Add(new HprSceneRow{ListIndex=i,BuildIndex=-1,Path="Assets/Scene.unity"});
        Reject(()=>HprSceneBaseline.SaveNew(P("large-rows.hpr-scenes"),largeRows,Capture),"reject excess rows before opening output");
        var aggregate=Profile();
        for(int i=0;i<150;i++) aggregate.Rows.Add(new HprSceneRow {
            ListIndex=i,BuildIndex=-1,Path=new string('x',32000),Name="bounded"
        });
        Reject(()=>HprSceneBaseline.SaveNew(P("too-big.hpr-scenes"),aggregate,Capture),
            "reject aggregate oversized snapshot before opening output");
        Check(!File.Exists(P("too-big.hpr-scenes")),"aggregate oversize leaves no partial file");
        var offsetFile=P("timezone.hpr-scenes");
        HprSceneBaseline.SaveNew(offsetFile,Profile(),Capture.ToOffset(TimeSpan.FromHours(2)));
        Check(HprSceneBaseline.Load(offsetFile).CapturedUtc==Capture &&
            HprSceneBaseline.Load(offsetFile).CapturedUtc.Offset==TimeSpan.Zero,"capture timestamp normalized to UTC");
    }

    private static void NativeReceiptReplay(string expected)
    {
        if (string.IsNullOrEmpty(expected)) return;
        const string root = "Assets/HPRPrivateMatrixQA/";
        var g=Profile("Global scenes");
        var o=Profile("Override  [Assets/HPRPrivateMatrixQA/Override.asset]","override","Overrides global scenes");
        Add(g,root+"A/Start.unity",new string('a',32));
        Add(g,root+"B/Start.unity",new string('b',32),false);
        Add(g,root+"Level.unity",new string('c',32));
        Add(o,root+"Level.unity",new string('c',32));
        Add(o,root+"A/Start.unity",new string('a',32));
        Add(o,root+"B/Start.unity",new string('b',32));
        var actual=P("prior-native-receipt-replay.csv");
        HprSceneMatrix.ExportNewCsv(actual,g,o);
        string Normalize(string p)=>File.ReadAllText(p).Replace("\r\n","\n");
        Check(Normalize(expected)==Normalize(actual),
            "offline comparison matches prior actual Unity fixture CSV; not a new native test");
    }

    private static void EditorSyntax(string source)
    {
        foreach (var flags in new[]{new[]{"UNITY_EDITOR"},new[]{"UNITY_EDITOR","UNITY_6000_1_OR_NEWER"}})
        {
            var options=new CSharpParseOptions(LanguageVersion.CSharp8,preprocessorSymbols:flags);
            var errors=CSharpSyntaxTree.ParseText(File.ReadAllText(source),options).GetDiagnostics()
                .Where(x=>x.Severity==DiagnosticSeverity.Error).ToArray();
            Check(errors.Length==0,"editor integration syntax under "+string.Join(",",flags)+": "+string.Join("; ",errors.Select(e=>e.ToString())));
        }
    }

    public static void Main(string[] args)
    {
        root=args[0];
        Directory.CreateDirectory(root);
        CompareCases();
        SnapshotCases();
        NativeReceiptReplay(args.Length>2?args[2]:"");
        EditorSyntax(args[1]);
        if(args.Length>3) EditorSyntax(args[3]);
        Console.WriteLine("HPR_OFFLINE_CORE_PASS assertions="+passed);
    }
}
