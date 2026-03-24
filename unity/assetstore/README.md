# Unity Asset Store workflow

This folder contains the local tooling for authenticated Unity Asset Store downloads,
native Unity-cache downloads, and automated project import/integration.

## Main paths

- Purchase catalog: `metadata/my_assets.json`
- Raw API download cache: `downloads/`
- Native Unity cache: `/home/hans/.local/share/unity3d/Asset Store-5.x/`
- Logs: `logs/`

## Tools

- `unity/tools/assetstore/unity_assetstore.py`
  - Queries purchased assets through the authenticated Unity API
  - Auto-refreshes expired Unity Hub access tokens via the Hub refresh token
  - Can list purchases and fetch raw package payloads
- `unity/tools/assetstore/unity_native_asset.py`
  - Uses the Unity Editor's internal Asset Store download path
  - Downloads real importable `.unitypackage` files into the native Asset Store cache
  - Imports those packages into the main project
  - Cleans up stale native cache temp files before retrying a stalled download
  - Falls back to cached package metadata if the Unity web API is temporarily unreachable
- `unity/tools/assetstore/queue_native_downloads.py`
  - Sequential native download queue
  - Validates existing downloaded packages before skipping
- `unity/assetstore/asset_pipeline.sh`
  - Waits for the current active download to finish
  - Imports each finished package once
  - Rebuilds and smoke-tests after every integration step
  - Continues through the selected asset list with only one active download at a time

## Import/integration automation

Editor methods in `Packages/com.hpr.fpsdemo/Editor/ThirdPartyAssetIntegrator.cs`:

- `ThirdPartyAssetIntegrator.ApplyDoorPackFromBatch`
- `ThirdPartyAssetIntegrator.ApplyFurniturePackFromBatch`
- `ThirdPartyAssetIntegrator.ApplyWeaponPackFromBatch`
- `ThirdPartyAssetIntegrator.ApplyHousePackFromBatch`
- `ThirdPartyAssetIntegrator.ApplyCharacterPacksFromBatch`

These keep gameplay intact and only replace visuals or set dressing.

## Cataloging

Use `PrefabCatalogReporter.ReportPrefabCatalogFromArgs` to dump imported prefab/model bounds.
This is used to fit third-party content to the existing FPS scene with correct scale.

## Pipeline flow

The current preferred flow is:

1. keep a single native download active
2. wait for the finished gzip `.unitypackage`
3. import it into the main project
4. catalog prefab/model bounds
5. apply the relevant scene/data integration
6. rebuild the game
7. run the smoke test

This is automated by `asset_pipeline.sh`.

## Notes

- The helper Unity project under `/home/hans/.local/share/hpr_unity_asset_helper` is used for native downloads so the main game project stays free for integration/build work.
- Do not trust manually renamed `.tmp` files from the Unity cache. Only import final gzip `.unitypackage` files that Unity completed itself.
- Large native downloads can leave stale `.tmp` files behind when Unity stalls. The downloader now removes stale cache temp files before retrying so the next attempt starts cleanly.
