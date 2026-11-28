# HPR Assembly Preflight — private local Unity assembly health report

**New private source-level product candidate; NOT an approved Unity Asset Store editor extension, NOT PUBLISHED, and NOT for resale.** Original stand-alone Python source checks a saved Unity project's local assembly definitions, `.asmdef` and `.asmref` files, for some important structural problems before a Unity package is shipped. It
also identifies embedded UPM `.cs` files with no ancestor `.asmdef` or `.asmref`
(such as runtime scripts hidden by an Editor-only definition). It excludes
`Samples~` and `Documentation~` from embedded-package assembly and C# scans;
those directories are not compiled by Unity until explicitly imported. It never starts the Unity Editor, makes a build, downloads dependencies, modifies files, or contacts anyone. It is deliberately separate from the existing HPR Package Boundary Inspector (which inspects asset references and GUID inventory, not assembly-name collisions or assembly reference declarations).

## Typical buyer problem

A package can look complete but its scripts may fail to become available to the buyer when an assembly definition is missing, when two local packages use the same assembly name, or when a test-only constraint hides a runtime assembly. Unity forum posts describe missing scripts after local package import and a real 2025 case where removing an unintended `UNITY_INCLUDE_TESTS` constraint restored a Player build. Official Unity documentation establishes that `.asmdef` files are necessary for compiled UPM scripts and that define constraints, versions and platforms decide compilation. **This tool does not solve or diagnose every such failure.**

## Run a private scan

Use Python 3.10 or later (standard library only). The project must have saved `Assets/` and `ProjectSettings/ProjectVersion.txt`. Close the Unity Editor or ensure all data has been saved before comparing versions:

    python3 -B hpr_asmdef_preflight.py /path/to/your/UnityProject

The default JSON prints to stdout with `schema`, `status`, finding paths/severities and explicit coverage limits. To save a report outside your Unity project, use exactly one of these commands with a **new** output path:

    python3 -B hpr_asmdef_preflight.py /path/to/UnityProject --json-out /private/report.json
    python3 -B hpr_asmdef_preflight.py /path/to/UnityProject --html-out /private/report.html

The HTML has no JavaScript, remote fonts, telemetry or network calls; its content-security policy disables remote resources. Reports may contain names and paths from your project, so inspect privately before sharing. Existing files cannot be overwritten. Outputs within the scanned Unity project are rejected.

## Exact result meanings

- `CLEAR_WITH_LIMITS`, exit zero: no structural problems found **within local saved assembly definitions actually inspected**. It is not proof of a clean Unity compile or Player.
- `REVIEW` or `FAIL`, exit one: a review is needed. `FAIL` means a definite local duplicate assembly name, duplicate saved GUID,
or an embedded UPM script with no assembly definition/reference in its folder ancestry. Unresolved references are `REVIEW`, **not declared broken**: they may legitimately point to installed external Registry packages or precompiled libraries. Multiple platform filters, repeated references and an unexpected `UNITY_INCLUDE_TESTS` constraint in a non-test location also request review.
- `INCOMPLETE`, exit three: a required saved file cannot be inspected or has unsupported/unsafe contents, such as malformed JSON, missing `Assets/*.asmdef.meta`, nonregular files, symbolic links, changed files or exceeded safety limits. This must never be advertised as a successful scan.

The scanner reads `Assets` plus explicitly embedded local package folders in `Packages` with an on-disk `package.json`. Registry `PackageCache`, remotely installed or embedded external packages without readable saved definitions, C# source-level reflection, actual compiler symbols, `csc.rsp`, version expressions, inactive/unsaved Editor state and final Player contents are **not covered**. An embedded asmdef without a `.meta` file is classified as having an unknown GUID. Potentially false-positive constraints require user review, not automatic deletion. Limits: three thousand assembly assets, one MiB per file, thirty-two MiB aggregate assembly JSON and three thousand findings. Source input reads use regular-file/no-symlink checks and stable metadata; this is not a guarantee against hostile concurrent filesystem modification.

## Current acceptance and rights

The QA suite uses isolated real-layout saved Unity directories, duplicate names, local GUID references, unresolved external names, malformed JSON, FIFOs, oversized files, symlinks, output overwrite attempts, Unicode/HTML escaping and input preservation. Run `python3 -m unittest discover -s qa -p 'test_*.py' -v`. The packaged product, when approved, should include only this Python code, README, LICENSE.md and ThirdPartyNotices.md; not the QA fixture. Independent clean Unity Editor import, supported platform matrices, interactive buyer workflow and professional images are still required for a Unity Asset Store extension. This CLI is useful privately now but **has not passed any Unity-native installation**.

AI-assisted first-party coding and docs must be disclosed to the shared seller, and any future listing must accurately describe which tools, testing, and limitations apply. Commercial viability and direct paid adoption have not been verified. See the private-only licence below.

### Saved first-party Unity source acceptance

The private author QA command `qa/run_saved_unity_acceptance.py` accepts a
previously saved first-party Unity project with real `.asmdef` assets. It scans
the original project read-only, copies **only** the saved assembly JSON,
metadata and project-version file to a disposable private local project, then
independently triggers three negative cases in the copy: duplicate assembly
name, unintended test-only compile constraint, and embedded UPM runtime script
without an owning assembly definition. The script rehashes every original
source file, proves preservation, removes its own temporary project, and writes
create-only private JSON evidence. It never runs Unity or asserts native
buyer-import acceptance. Actual independent first-party Unity six saved-source
acceptance is recorded in the seller's private QA handoff for this revision.
