# Workflows

## 1. Build the Linux player
Run as `hans`:

```bash
cd /data/src/github/games
unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux
```

What it does:
- cleans stale Unity lock files in the project
- runs Unity batch mode against `unity/projects/fps_demo`
- writes a timestamped log to `doc/logs/`

Default Unity editor path:
- `/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity`

Override if needed:

```bash
UNITY_BIN=/path/to/Unity unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux
```

## 2. Run a smoke test
Run as `hans`:

```bash
cd /data/src/github/games
unity/tools/fps_demo/smoke_test.sh
```

Notes:
- it uses the built player at `unity/projects/fps_demo/Build/Linux/FPSDemo.x86_64`
- it shows the standard focus notice before the visible run
- if no notice appears, there is no focus requirement

Useful environment overrides:

```bash
SMOKE_TIMEOUT=30 NOTICE_SECONDS=2 unity/tools/fps_demo/smoke_test.sh
NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh
```

## 3. Focus-sensitive visible tests
Use:

```bash
unity/tools/common/focus_notice.sh 2 "Leave FPSDemo alone for 8 seconds."
```

This is the repo copy of the helper that was also exposed through `/data/bin/focus_notice.sh`.

## 4. Zip only tracked repo files
Use:

```bash
unity/tools/common/zip_tracked_repo.sh /data/src/github/games
```

Optional output path:

```bash
unity/tools/common/zip_tracked_repo.sh /data/src/github/games /tmp/games_tracked.zip
```

## 5. Temp-project workflow for Unity lock issues
If the main project gets stuck in a bad batch/lock state, the fallback workflow is:

```bash
cd /data/src/github/games
unity/tools/fps_demo/sync_temp_project.sh
unity/tools/fps_demo/temp_apply_and_build.sh
```

What these do:
- create/sync a temp Unity project under `/data/tmp/games_unity_temp/fps_demo`
- symlink local-only asset roots into that temp project
- run selected local art integration in the temp project
- build there, then copy tracked scene/build outputs back if required

This exists because Unity can occasionally leave stale lock state even when no live editor is present.

## 6. Local Asset Store workflow
Tooling lives in:
- `unity/tools/assetstore/`
- `unity/assetstore/`

Important scripts already in the repo:
- `unity/tools/assetstore/queue_native_downloads.py`
- `unity/tools/assetstore/unity_native_asset.py`
- `unity/assetstore/run_native_queue.sh`
- `unity/assetstore/continue_native_downloads.sh`
- `unity/assetstore/asset_pipeline.sh`

Policy:
- downloads keep running locally
- imported art stays ignored
- only scripts/automation/docs are committed

## 7. Ownership / permissions
Everything should be runnable as `hans`.

If ownership drifts again, the safe correction is:

```bash
sudo chown -R hans:hans /data/src/github/games
```

The current repo state should already be corrected for this.
