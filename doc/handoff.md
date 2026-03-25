# Handoff Guide

## Start here
The project is in a usable engineering state for takeover if you follow this order:

1. read `doc/current-state.md`
2. read `doc/local-assets.md`
3. use `unity/tools/fps_demo/run_unity_batch.sh` for batch work
4. use `unity/tools/fps_demo/smoke_test.sh` for player verification
5. do not commit imported art data

## Current code changes included in this handoff
The repo currently includes tracked changes for:
- third-party asset integration helpers
- scene/material diagnostics (`ThirdPartySceneReporter`)
- menu-state fixes in `GameUiController`
- smoke/runtime path fixes in `GameManager`
- temp-project sync/build helpers
- repo-local copies of helper scripts used during work
- expanded repo documentation

## What is local-only and not reproducible from git alone
Not committed:
- downloaded Unity Asset Store packages
- imported vendor asset folders in `Assets/`
- local-only art scene dressing based on those imports
- generated logs/builds/temp state

If the next developer wants the same art state, they must recreate it locally with the asset pipeline.

## Verified commands
Build:

```bash
cd /data/src/github/games
unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux
```

Smoke:

```bash
cd /data/src/github/games
unity/tools/fps_demo/smoke_test.sh
```

Temp workflow:

```bash
cd /data/src/github/games
unity/tools/fps_demo/sync_temp_project.sh
unity/tools/fps_demo/temp_apply_and_build.sh
```

## Known realities / caveats
- Unity batch mode can still be sensitive to stale lock files. The repo now has scripts to standardize cleanup.
- Local third-party art integration is scriptable, but the art itself is intentionally excluded from version control.
- The gameplay codebase is the committed source of truth; local scene dressing based on untracked asset packs is not.
- If the desktop must remain untouched during a visible run, the workflow uses a 2-second popup notice first.

## Recommended immediate next steps for a new developer
1. verify the workspace as `hans`
2. rebuild the player with `run_unity_batch.sh`
3. run the smoke test
4. inspect `doc/logs/` and the Unity player log if anything fails
5. only then continue gameplay or art integration work

## Current open follow-up areas
- local-only art integration still needs polish for orientation/scale/material consistency
- smoke preview capture should be rechecked after the latest hierarchy-path fix
- the menu system should get another visible QA pass after recent layout/state changes
- if local asset imports continue, keep them script-driven and out of git
