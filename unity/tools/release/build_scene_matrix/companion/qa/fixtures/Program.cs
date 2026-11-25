using System;
using System.IO;
using HPR.BuildSceneMatrix;

internal static class Fixtures
{
    private static readonly DateTimeOffset ReferenceTime =
        new DateTimeOffset(2026, 11, 25, 9, 0, 0, TimeSpan.Zero);
    private static string output;
    private static readonly string A = new string('a', 32);
    private static readonly string B = new string('b', 32);
    private static readonly string C = new string('c', 32);
    private static readonly string D = new string('d', 32);

    private static HprSceneProfile Profile(string id = "global", string source = "Shared scene list")
    {
        return new HprSceneProfile
        {
            Id = id, Title = "Example configuration — not a real Unity scan",
            AssetPath = "Assets/Build Profiles/Example.asset", Source = source
        };
    }

    private static void Add(HprSceneProfile profile, string name, string guid, bool enabled, bool missing = false)
    {
        profile.Rows.Add(new HprSceneRow
        {
            Path = name, Guid = guid, Name = Path.GetFileNameWithoutExtension(name),
            ListIndex = profile.Rows.Count, BuildIndex = enabled ? profile.EnabledCount : -1,
            Enabled = enabled, Missing = missing
        });
    }

    private static HprSceneProfile Standard(bool renamed = false, bool stale = false,
        bool swapEnabled = false, bool reorderDisabled = false, bool empty = false)
    {
        var p = Profile();
        string first = renamed ? "Assets/Scenes/StartRenamed.unity" : "Assets/Scenes/Start.unity";
        if (reorderDisabled) Add(p, "Assets/Scenes/Test.unity", C, false);
        if (swapEnabled) Add(p, "Assets/Scenes/Level.unity", B, !empty);
        Add(p, first, A, !empty, stale);
        if (!reorderDisabled) Add(p, "Assets/Scenes/Test.unity", C, false);
        if (!swapEnabled) Add(p, "Assets/Scenes/Level.unity", B, !empty);
        return p;
    }

    private static void Save(string name, HprSceneProfile profile, int minutes = 5)
    {
        HprSceneBaseline.SaveNew(Path.Combine(output, name + ".hpr-scenes"),
            profile, ReferenceTime.AddMinutes(minutes));
    }

    private static void Main(string[] args)
    {
        output = args[0];
        Directory.CreateDirectory(output);
        Save("approved", Standard(), 0);
        Save("same", Standard());
        Save("renamed", Standard(renamed:true));
        Save("missing", Standard(stale:true));
        Save("reordered", Standard(swapEnabled:true));
        Save("disabled-reordered", Standard(reorderDisabled:true));
        Save("empty", Standard(empty:true));
        Save("older", Standard(), -5);
        var other = Standard();
        other.Id = "different-profile";
        Save("other-profile", other);
        var inherited = Standard();
        inherited.Source = "Overrides global scenes";
        Save("override", inherited);
        var movedProfile = Standard();
        movedProfile.AssetPath = "Assets/Build Profiles/ExampleMoved.asset";
        Save("moved-profile", movedProfile);
        var duplicate = Standard();
        Add(duplicate, "Assets/Scenes/Start.unity", A, true);
        Save("duplicate", duplicate);
        var ambiguous = Standard();
        Add(ambiguous, "Assets/Other/Start.unity", D, true);
        Save("ambiguous", ambiguous);
        var warning = Standard(stale:true);
        Save("warning-baseline", warning, 0);
        Save("warning-current", warning);
        var added = Standard();
        Add(added, "Assets/Scenes/Bonus.unity", D, false);
        Save("added", added);
        var removed = Profile();
        Add(removed, "Assets/Scenes/Start.unity", A, true);
        Add(removed, "Assets/Scenes/Level.unity", B, true);
        Save("removed", removed);
        var unicode = Standard();
        unicode.Title = "日本語 & \"quoted\" \u001b[31m";
        Save("unicode", unicode);
        byte[] raw = File.ReadAllBytes(Path.Combine(output, "approved.hpr-scenes"));
        Array.Resize(ref raw, raw.Length-1);
        File.WriteAllBytes(Path.Combine(output, "truncated.hpr-scenes"), raw);
        File.WriteAllBytes(Path.Combine(output, "oversized.hpr-scenes"), new byte[4*1024*1024+1]);
        File.WriteAllText(Path.Combine(output, "bad-magic.hpr-scenes"), "wrong format");
    }
}
