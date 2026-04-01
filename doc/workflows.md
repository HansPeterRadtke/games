# Workflows

## 1. Run the authoritative release-candidate validation
Run as `hans`:

```bash
cd /data/src/github/games
unity/tools/release/validate_release_candidate.sh
```

What it does:
- runs release audit for the sellable package set
- runs dependency audit
- runs headless validation
- validates clean-project import + demo execution for each sale-ready package
- validates clean-project import for the sale-ready package combinations
- rebuilds the main game
- runs the main-game smoke test

Current sale-ready package set:
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`

## 2. Build the Linux player directly
Run as `hans`:

```bash
cd /data/src/github/games
unity/tools/fps_demo/run_unity_batch.sh HPR.SceneBootstrap.BuildLinux
```

What it does:
- cleans stale Unity lock files in the project
- runs Unity batch mode against `unity/projects/fps_demo`
- writes a timestamped log to `doc/logs/`

Default Unity editor path:
- `/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity`

Override if needed:

```bash
UNITY_BIN=/path/to/Unity unity/tools/fps_demo/run_unity_batch.sh HPR.SceneBootstrap.BuildLinux
```

## 3. Run the full-game smoke test
Run as `hans`:

```bash
cd /data/src/github/games
unity/tools/fps_demo/smoke_test.sh
```

Notes:
- it uses the built player at `unity/projects/fps_demo/Build/Linux/FPSDemo.x86_64`
- it shows the standard focus notice before the visible run unless `NO_NOTICE=1`
- the player proof log is written to `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

Useful environment overrides:

```bash
SMOKE_TIMEOUT=30 NOTICE_SECONDS=2 unity/tools/fps_demo/smoke_test.sh
NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh
```

## 4. Validate selected packages in fresh Unity projects
Use:

```bash
cd /data/src/github/games
unity/tools/packages/validate_local_packages.sh com.hpr.eventbus
unity/tools/packages/validate_local_packages.sh com.hpr.composition
unity/tools/packages/validate_local_packages.sh com.hpr.save
unity/tools/packages/validate_local_packages.sh com.hpr.stats
unity/tools/packages/validate_local_packages.sh com.hpr.inventory
unity/tools/packages/validate_local_packages.sh com.hpr.interaction
unity/tools/packages/validate_local_packages.sh com.hpr.abilities
```

To execute a package-owned validator inside the clean temp project:

```bash
cd /data/src/github/games
EXECUTE_METHOD=HPR.EventBusPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.eventbus
EXECUTE_METHOD=HPR.CompositionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.composition
EXECUTE_METHOD=HPR.SavePackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.save
EXECUTE_METHOD=HPR.StatsPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.stats
EXECUTE_METHOD=HPR.InventoryPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.inventory
EXECUTE_METHOD=HPR.InteractionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.interaction
EXECUTE_METHOD=HPR.AbilitiesPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.abilities
```

Representative package combination validations:

```bash
cd /data/src/github/games
unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus
unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats
unity/tools/packages/validate_local_packages.sh com.hpr.inventory com.hpr.interaction
unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats com.hpr.abilities
unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.composition com.hpr.save com.hpr.stats com.hpr.inventory com.hpr.interaction com.hpr.abilities
```

## 5. Headless non-Unity validation
Use:

```bash
cd /data/src/github/games
unity/tools/architecture/run_phase1_headless_validation.sh
```

This proves the standalone composition + eventbus core still works outside Unity scene bootstrapping.

## 6. Focus-sensitive visible tests
Use:

```bash
unity/tools/common/focus_notice.sh 2 "Leave FPSDemo alone for 8 seconds."
```

This is the repo copy of the helper that is also exposed through `/data/bin/focus_notice.sh`.

## 7. Zip only tracked repo files
Use:

```bash
unity/tools/common/zip_tracked_repo.sh /data/src/github/games
```

Optional output path:

```bash
unity/tools/common/zip_tracked_repo.sh /data/src/github/games /tmp/games_tracked.zip
```

You can also pass a tracked subfolder instead of the repo root.

## 8. Temp-project workflow for Unity lock issues
If the main project gets stuck in a bad batch/lock state, the fallback workflow is:

```bash
cd /data/src/github/games
unity/tools/fps_demo/sync_temp_project.sh
unity/tools/fps_demo/temp_apply_and_build.sh
```

This exists because Unity can occasionally leave stale lock state even when no live editor is present.

## 9. Local Asset Store workflow
Tooling lives in:
- `unity/tools/assetstore/`
- `unity/assetstore/`

Real local asset inventory:
- `doc/local-assets.md`

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

## 10. Ownership / permissions
Everything should be runnable as `hans`.

If ownership drifts again, the safe correction is:

```bash
sudo chown -R hans:hans /data/src/github/games
```

## Publisher validation
- official Asset Store Tools validation: `unity/tools/release/run_official_asset_store_validator.sh`
