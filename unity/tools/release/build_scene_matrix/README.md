# Build Scene Matrix — private original product candidate
Separate from input readiness, archive/prefab audits and the Player Reference Probe. All buyer content is below Assets/HPRBuildSceneMatrix; private QA is excluded. Native author export, clean buyer installation, actual Build Profile fixture and native window interaction must pass before release-ready claims. No publication or external action is authorized.

The saved-reference feature and core comparisons are independently exercised by the offline .NET harness in `qa/offline`. This is not a Unity import or graphical receipt. The previously native-tested archive remains at its original source revision; export and validate the new exact package, including real GUI actions, before replacing it.

The separate `companion/` source provides the private HPR Scene Gate command-line
utility, compiled and tested independently without invoking Unity. It compares
saved snapshots and can capture the observed saved project-text formats. Its
`check` command reads the selected saved project configuration afresh, compares
in memory, and gives a human-readable result or JSON without creating a current
snapshot. Input operations currently require Linux x86-64 with statx; nonregular
files are rejected before opening. This is a stable-local-file check, not protection
against hostile concurrent replacement. The companion is
not included in the native Unity buyer archive; retain exact package and runtime
acceptance boundaries. The editor-source correction also reports full declared
list sequence changes (including disabled entries) separately from enabled build
indices; native GUI acceptance remains required.

For offline QA, the command-line companion requires the .NET 10 SDK with
a current security patch. The editor-core compatibility harness additionally
requires the .NET Standard 2.1 targeting pack; the isolated .NET 10 SDK does
not include it by default. Use an already installed, verified reference pack
or an explicitly authorized supported installation. No Unity executable,
Unity assemblies or external NuGet packages are needed for these offline
checks. The companion package itself needs only the .NET 10 runtime.
