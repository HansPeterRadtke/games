# HPR Scene Gate — offline Build Scene Matrix companion

Compare a chosen reference scene list with a freshly read saved Unity project,
without opening Unity or creating a second snapshot. See which scene is first,
whether a profile inherits or overrides the global list, and what changed.

This private prerelease is a companion to Build Scene Matrix, not a separate
published store product. It checks declared configuration, not the contents
or success of a built game. The included licence is for private evaluation;
it is not an approved customer licence.

## Requirements

- Linux x86-64 with the `statx` file metadata API. Windows, macOS and other
  architectures are currently rejected for input operations.
- A current .NET 10 LTS runtime, at least 10.0.15. The runtime is not included.
- A closed, stable local Unity project with ordinary saved text files.
- The observed Unity 6000.6.8f1 global scene list or version-two Build Profile
  layout, or the observed 2022.3.22f1 global layout. Other versions and layouts
  are rejected rather than guessed.

Independent saved-file acceptance covers nonempty Unity 6.6 lists and an empty
2022 list. A nonempty native 2022 configuration was not available. This historical
file-format coverage is not a recommendation to install an old Editor. See the
exact package acceptance receipt for tested runtime and platform details.

## First use

Extract the archive, then check the installed runtime and the command help:

```text
dotnet --list-runtimes
dotnet HprSceneGate.dll --version
dotnet HprSceneGate.dll --help
```

Choose the project and explicit global list or profile you intend to check.
First review the scene configuration yourself, then capture a reference in a
new file **outside** the project:

```text
dotnet HprSceneGate.dll capture "/path/to/project" global approved.hpr-scenes
```

After changes, check the saved project against that reference in one step:

```text
dotnet HprSceneGate.dll check approved.hpr-scenes "/path/to/project" global
```

The default text result names the selected list, its source, the current and
reference launch scenes, enabled and declared scene counts, and the first
differing entry. A launch scene means the first **enabled** scene in the selected
saved list, not the scene currently open in the Editor. Up to ten per-scene
findings appear in text; JSON includes all findings.

For an explicit Build Profile, use the same project-relative asset path when
capturing and checking:

```text
dotnet HprSceneGate.dll capture "/path/to/project" Assets/BuildProfiles/Release.asset release.hpr-scenes
dotnet HprSceneGate.dll check release.hpr-scenes "/path/to/project" Assets/BuildProfiles/Release.asset
```

The program does not choose or activate a profile for you. It follows the
explicit saved profile's inheritance setting. Unused custom rows in an
inherited profile do not replace the global list.

For automation, request exactly one JSON result:

```text
dotnet HprSceneGate.dll check approved.hpr-scenes "/path/to/project" global --format json
```

Check creates no snapshot, temporary comparison file, or project output.
It reads the saved files during this invocation and rechecks those inputs for
changes. JSON marks `current_saved_configuration_read_this_run` as true and
records the read start and finish times. This is not a filesystem transaction;
keep the project closed and stable while checking.

## Exit results

| Exit | Check or compare | Capture |
|---|---|---|
| 0 | Declared configuration matches without warnings. | A new snapshot was created; its scenes may still need review. |
| 1 | A configuration difference or warning needs review. | Not used. |
| 2 | Invalid input, unsupported format/platform, or a read error. | No successful snapshot capture. |

Differences include profile identity, profile asset path, inheritance source,
full declared entry order (including disabled scenes), enabled build indices,
renamed paths and missing/stale references. Empty enabled lists, duplicate
entries, ambiguous enabled scene names and a reference timestamp later than
the current read also request review. Warnings already present in both lists
still request review. An old reference is allowed; age alone does not fail.

A successful check does not prove that the reference was approved or belongs
to this project. Review its launch scene and selected profile. Saved files
cannot reveal unsaved Editor changes, whether the chosen profile is active,
custom build scripts, cloud scene overrides, generated content or actual Player
contents. JSON retains `project_identity_verified=false`; snapshot comparison
does not verify freshness. No command starts Unity or accesses the network.
The results contain project and scene paths, so inspect logs before sharing.

## Comparing two saved snapshots

The existing snapshot workflow remains available:

```text
dotnet HprSceneGate.dll compare approved.hpr-scenes current.hpr-scenes
```

Compare always emits JSON and reads only the two supplied snapshots. Unlike
check, it cannot establish that either snapshot reflects the saved project now.
The synthetic examples in this package can demonstrate the exits:

```text
dotnet HprSceneGate.dll compare examples/approved.hpr-scenes examples/same.hpr-scenes
dotnet HprSceneGate.dll compare examples/approved.hpr-scenes examples/renamed.hpr-scenes
```

The first returns zero. The second returns one with a renamed-scene finding.
These examples are not customer data or actual Unity scans. JSON list positions
start at zero; text positions start at one.

## Input boundaries and recovery

Use ordinary local files. Special files such as pipes, sockets and devices are
rejected before opening, and linked project paths are unsupported. Metadata is
checked before reads; this does not protect against another process maliciously
replacing a path between that check and the read. Do not use a changing checkout,
network stream or hostile filesystem as input.

The saved reader is deliberately limited. It does not interpret arbitrary YAML,
binary serialization, quoted or complex scalars, package scenes, linked assets
or unverified Unity versions. It checks listed scene existence and adjacent
metadata identifiers, without searching for moved files or examining scene
contents. If input is unsupported, restore a stable supported saved layout or
use another verified workflow; do not edit the reference merely to hide a warning.

Capture requires a new `.hpr-scenes` file outside the project and refuses to
overwrite an existing file. Keep the approved reference separate from disposable
captures. None of these commands repairs or modifies Unity project settings.

The Build Scene Matrix Editor's Save live reference integration is a separate
source-level increment still awaiting native Unity acceptance. Earlier native
Unity packages do not include it. This independently usable saved-file companion
does not remove that release hold.
