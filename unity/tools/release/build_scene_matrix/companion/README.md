# HPR Scene Gate — offline Build Scene Matrix companion

This tool compares two explicitly saved Build Scene Matrix scene-list snapshots
without starting Unity. It is intended for review or a release pipeline that
needs a machine-readable result and nonzero exit status when scene declarations
change unexpectedly. It is not a scene editor, automatic build, project crawler,
or certification of the generated game.

Use the Build Scene Matrix editor tool's **Save live reference** action once
for the approved list, and again after a fresh scan of the corresponding
current profile. The editor snapshot feature is a new source-level increment
and has not yet completed native Unity acceptance. Earlier native packages
do not contain it. The current independent companion does not resolve that
release hold.

With .NET 10.0.15 or a newer .NET 10 security patch installed (runtime not
included), run from the extracted companion:
```
dotnet HprSceneGate.dll --version
dotnet HprSceneGate.dll --help
```
Then compare your snapshots:

    dotnet HprSceneGate.dll compare approved.hpr-scenes current.hpr-scenes

The tool writes only a structured JSON comparison to standard output. It does
not modify either snapshot, invoke Unity, access the network, or modify your
project. It returns zero only when profile identity, inheritance source, profile asset path,
declared entry sequence and comparison findings match, with no empty enabled
list, comparison warnings, or reversed capture timestamps. Exit one requests
review of a difference or diagnostic warning. Exit two means invalid input
or failure to read the snapshots. An older baseline can contain existing
warnings; these intentionally still request review. Capture-time differences
alone do not indicate configuration drift. The report locates the first
different declared entry even when only disabled-scene positions change.
Use the current security-patched .NET 10 LTS runtime; .NET 8 and 9 are out
of upstream support.

The JSON contains the paths and identifiers of your selected scenes; inspect
before sharing logs. The command cannot establish that the two snapshots
belong to the same project, prove how recently the project was scanned, or
detect custom build scripts, pipeline overrides, generated content or the
actual built Player's scene contents. A successful result is limited to the
two supplied snapshots.

This private companion is intended for the supported .NET 10 LTS runtime.
Refer to the exact accompanying acceptance receipt for verified versions
and platforms; Windows and macOS are not yet verified. It shares the original C# comparison
and bounded snapshot parser with Build Scene Matrix. The included private
prerelease license is not an approved customer license. No publication or
third-party support commitment is implied.

## Capture directly from a saved project (no Unity process)

Use a closed, stable project checkout. This option reads the saved text
configuration, not the Editor's live state:

```text
dotnet HprSceneGate.dll capture /path/to/project global approved.hpr-scenes
dotnet HprSceneGate.dll capture /path/to/project Assets/BuildProfiles/Release.asset current.hpr-scenes
```

Choose the same global list or explicit profile for baseline and current capture.
Output must be a new file outside the project directory. The bounded reader
understands the observed Unity 2022.3.22f1 and 6000.6.8f1 global text layout,
and the observed 6000.6.8f1 custom Build Profile layout (version two).
Independent real saved-file tests covered nonempty 6.6 lists and an empty
2022 list; a nonempty native 2022 configuration was not available in the
inspected fixtures. The historical 2022 file-format test is not a recommendation
to install or use that unpatched Editor.
It distinguishes inherited and overridden lists and checks listed scene paths
and their adjacent metadata identifiers. It does not interpret arbitrary YAML,
binary serialization, linked paths, package scenes, or unverified Unity versions.
Unsupported formats return exit two rather than guessing. It does not search
for moved files or validate the internal contents of scene assets; stale or
missing path metadata is reported. It cannot determine the active profile,
unsaved changes, or actual build results. Capture exit zero means a snapshot
was created, not that all its scenes are healthy; run the comparison gate to
review findings. Inputs must be ordinary local saved files, not live streams.

The included `examples/` files are synthetic demonstration snapshots, not
customer data or actual Unity scans. In the extracted package, compare
`examples/approved.hpr-scenes` with `examples/same.hpr-scenes` for exit zero,
or with `examples/renamed.hpr-scenes` for exit one and a renamed scene finding.
The command line JSON uses zero-based list positions; the editor and CSV
describe positions starting at one.
