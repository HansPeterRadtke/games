# HPR Build Scene Matrix
Original Unity Editor diagnostic. Open Tools > HPR > Build Scene Matrix and click Scan project.
Choose the shared/global list or a custom Build Profile as your reference, then choose another list.
The tool reads the effective declared scene list using Unity's public API without activating any profile. It shows inheritance, enabled indices, first scene, missing/renamed assets, repeated entries and ambiguous enabled scene names. Differences can be intentional. Expand All profiles for the project-wide overview, then select a profile for detailed comparison. Filter paths and use Find to ping the scene asset. Export creates a NEW local CSV, never replaces a file. The CSV contains project paths: inspect it before sharing.

Unity 6.1+ API is required; earlier editors display an unsupported-version message. Actual compatibility must be stated from tested versions, not inferred from compilation. Only asset-backed Build Profiles under Assets and any currently active persistent profile are enumerated. No scenes opened, profiles changed, Player Settings read or written, builds launched, packages added, networking, telemetry or runtime code. Disabled rows have no build index. Absent is distinct from disabled. An empty enabled list is a configuration warning, not a prediction of actual build behavior. Custom build scripts, generated scenes, Addressables, platform failures and engine defects are outside this diagnostic. Explicitly rescan after editing settings. Not a build correctness guarantee.
The accompanying license is the private prerelease placeholder, not an approved buyer agreement.

## Compare a saved reference with a later scan

Select the desired live reference, scan the project, then use **Save live reference**.
Choose a new local file outside Assets if you do not want Unity to import the
file. The snapshot stores the declared scene entries, profile identity, source
and capture time. It is bounded to twenty thousand rows and four MiB.
After editing your project or switching revisions, use **Load saved reference**.
The tool selects a matching readable current profile when one is available.
Check that the loaded reference belongs to the intended project. A global list
or matching asset identifier alone does not prove project identity. Select
**Return to live reference** to compare two current lists again.

A moved scene is matched by its original identifier and displays its prior path.
A reference becoming stale or becoming valid is a difference, even if its
build index is unchanged. Historical entries never activate a build profile.
Exporting a historical comparison includes its capture time and profile
identities. Snapshot and CSV exports never overwrite existing files; they
may contain private project paths. Inspect before sharing. This checks declared
configuration, not what a custom build script actually included.

The declared-list sequence check also identifies changes in disabled scene
positions that leave every enabled build index unchanged. Historical exports
include the first differing declared list position and changes in profile asset
path. The separately distributed offline companion shares this comparison core;
its private package is not part of the Unity asset archive.
