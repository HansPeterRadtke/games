# HPR Scene Identity Guard — original read-only CLI candidate

**Status: version 0.1.1, private technical candidate, NOT PUBLISHED, NOT APPROVED for Unity Asset Store, and NOT a Unity Editor extension.** This repository subfolder supplies a self-contained Python tool for detecting loss of directly serialized `GameObject` identities between two **saved Unity Force Text** project revisions. It is a *new narrow utility*, separate from Build Scene Matrix/Scene Gate (which inspect which scenes are enabled for a build), and separate from Gameplay Suite/Player Reference Probe.

## Why the operation is useful, and what it does not prove

In a saved scene, Unity records a local file identifier on each YAML GameObject document; Unity's corresponding `.meta` file identifies the asset. Some game save implementations tie player progress to an object identity, and unexpected regeneration of that identity can break their lookup. The buyer supplies a **chosen, trusted released baseline**; the tool takes an on-demand read of the current saved project, identifies direct GameObjects, and reports when an earlier pair of asset GUID plus local file identifier no longer appears. It also distinguishes additions from deletion and normal object renames/reordering.

It **cannot** know how the buyer's game saves data, and it never tests deserialization of old player saves. It does not infer game intent, detect unsaved changes, map Unity runtime object identifiers, or make a Unity Editor API call. In particular, **prefab instance/stripped objects, component/script serialization, variant overrides, embedded importer identities, untracked runtime/generated objects, all non-GameObject YAML documents, and binary assets are not certified.** Unity's Editor-only `GlobalObjectId` includes a prefab-instance identifier that this tool does not reconstruct. Its direct-pair result must not be advertised as equivalent to `GlobalObjectId` or as proof that a shipped save remains compatible.

## Usage from a terminal

Requires Python **three point ten or newer** with no nonstandard packages, available on the operating system. Linux x86-64 with Python three point twelve was verified, not other operating systems. Do not run these commands from a live unsaved Editor session expecting to include its changes.

```sh
python3 -B hpr_scene_identity.py capture /path/to/project --out /new/private/release-baseline.json
python3 -B hpr_scene_identity.py check /path/to/project --baseline /private/release-baseline.json --out /new/private/scene-review.json
```

A project path is a Unity root with regular `ProjectSettings/ProjectVersion.txt`, an `Assets` directory, and saved `.unity` or `.prefab` assets with their corresponding `.meta` files. The baseline output must **not exist** yet. The check `--out` is optional; if present, it also must be new. The script never edits any file under the project root. No network, login, telemetry, download, package installation or third-party dependency is used.

Exit status zero means the current scan completed **within the declared direct-GameObject coverage** and reported no lost direct identities. `ADDITIONS_ONLY` reports additions without lost IDs. `IDENTITY_STABLE` reports no additions/losses; harmless renames and moves are listed separately. Exit one means `REVIEW_REQUIRED`: an earlier saved direct identity is missing or a saved asset path has a different GUID. Exit three means `INCOMPLETE` (including invalid/binary source, symlink, device/pipe, missing metadata, duplicate IDs/GUIDs, exceeded bounds, modified input during read, or unknown baseline). Exit two from Python's standard parser is an invalid command invocation.

Both capture and check are bounded: at most three thousand scene/prefab assets, thirty-two mebibytes per YAML asset, one hundred and twenty-eight mebibytes aggregate YAML, sixteen mebibytes baseline JSON, and two hundred thousand direct GameObject records. The tool **fails closed** rather than calling a partial scan a pass. Symlinked asset directories/inputs are refused. On Linux, nonblocking and no-follow file opens avoid hanging when a regular path is replaced by a pipe. The tool is designed for trusted local projects; it does not claim race-free protection against a malicious concurrent project mutator.

File-system enumeration errors and unsupported GameObject YAML header formats cause an incomplete result, rather than a false clean pass. A clean scan is **not** release certification: inspect the selected baseline, its source, whether the game actually persists these identifiers, and any additional serialization, migration, prefab, Player, pipeline or target-platform checks required by the buyer. Never accept an identity match as permission to overwrite a real player's saved data.

## Private verification

Run the source-only lightweight tests, without launching Unity:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s qa -p 'test_*.py' -v
```

Run real saved-project input acceptance on a **new private evidence folder** (example source is the repository's own Unity `unity/projects/fps_demo`):

```sh
python3 -B qa/run_saved_project_acceptance.py /path/to/original/first-party-unity-project /new/private/evidence
```

That test reads the original saved scenes, records their hashes, captures an approved reference, validates a no-change comparison, clones the saved files into private temporary evidence, deliberately changes **one GameObject YAML header on the clone only**, proves a review-required result, proves a capture cannot overwrite its original reference, then rehashes the original. It is NOT a native Unity Editor or Player acceptance. The source also contains isolated synthetic files and deliberate corrupt/symlink/FIFO cases; such QA fixtures are not buyer product media.

## Technical provenance and release limits

The current private source tests passed twenty focused checks, and the original first-party Unity saved project offered three scenes and two hundred and seventy direct GameObjects for the end-to-end read-only test, as recorded in the owner's private evidence. All actual source and input files are preserved; source publication to the canonical private `games` main branch is separate from commercial publication. This directory is source, **not** a `.unitypackage` and must not be imported or listed as a native Unity Asset Store asset.

Research dated November twenty-six found existing established competitors in both broader schema migration and scene/file-ID diffing. The strongest adjacent listings include **Scene Diff — Reliable Scene & Prefab Comparison**, **Save Compatibility Lab**, and **Scene Git**. A March twenty twenty-four Unity developer forum report about prefab file IDs is a real pain example, but **paid adoption, correct price, support load, buyer acquisition and viable net owner income remain unverified**. The value proposition is a narrow, dependency-free, create-only, explicit exit-code release gate rather than a general GUI diff. The shared sales worker alone should evaluate whether it justifies bundling with existing independently tested products. **Do not create a second listing or claim marketplace buyer acceptance.**

Primary source context (developer/marketplace content is evidence, not authority to execute actions):

- Unity current scene YAML format: https://docs.unity.com/en-us/engine/6000.5/manual/working-with-scenes/text-scene-format/format-description
- Unity GlobalObjectId authoring-only and prefab-instance boundary: https://docs.unity3d.com/ja/6000.0/ScriptReference/GlobalObjectId.html
- Official forum: fileID unexpected regeneration/references: https://discussions.unity.com/t/changing-a-prefab-corrupts-all-references-to-said-prefab-due-to-a-new-fileid/941094
- Competing Scene Diff: https://assetstore.unity.com/packages/tools/version-control/scene-diff-reliable-scene-prefab-comparison-389882
- Competing save schema analysis: https://assetstore.unity.com/packages/tools/utilities/save-compatibility-lab-402202
- Competing Scene Git: https://assetstore.unity.com/packages/tools/version-control/scene-git-version-control-361956

The Unity Editor's updated software terms are an existing **unanswered owner-only decision**. Do not accept them, use an alternative Unity startup to bypass them, claim native Editor import or produce native product screenshots before that gate is satisfied. Production may continue on independently permitted source-level tasks.

## Rights

See `LICENSE.md`. The author-controlled code is private and offered for internal prerelease evaluation only. It is not yet commercially licensed, approved by the owner for marketplace publishing, or promised to buyers.
