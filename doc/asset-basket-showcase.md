# Asset Basket Showcase

This repo now contains a dedicated local Unity project for rebuilding a full showcase scene from the Unity Asset Store basket owned by the local user account.

## Project

- Project path: `unity/projects/asset_basket_showcase`
- Unity version: `6000.4.0f1`
- Generated scene path: `Assets/Scenes/AssetBasketShowcase.unity`

## What is tracked

Tracked files cover only reproducible project scaffolding and automation:

- batch import/build scripts in `unity/assetstore/`
- editor tooling in `unity/projects/asset_basket_showcase/Assets/Editor/`
- project config in `unity/projects/asset_basket_showcase/Packages/` and `unity/projects/asset_basket_showcase/ProjectSettings/`

Imported third-party Asset Store content, generated preview assets, local download state, and Unity cache/log folders stay untracked.

## Rebuild flow

Run:

```bash
unity/assetstore/build_asset_basket_showcase.sh
```

That script:

1. verifies all purchased basket packages are downloaded locally
2. imports them into `unity/projects/asset_basket_showcase`
3. strips imported code and editor/test assemblies that block compilation
4. repairs unsupported materials
5. inventories all imported content
6. builds the generated showcase scene

## Latest validated result

Validated on `2026-04-04` from the current repo state.

Inventory/build outputs were generated under ignored local logs:

- `unity/assetstore/logs/asset_basket_showcase_inventory.txt`
- `unity/assetstore/logs/asset_basket_showcase_build_report.txt`
- `unity/assetstore/logs/asset_basket_showcase_scene_validation.txt`

Latest measured content totals:

- structures: `1931`
- nature: `1024`
- props: `2714`
- weapons: `185`
- characters: `884`
- effects: `81`
- materials: `4067`
- textures: `4608`
- animations: `1516`

Latest scene validation totals:

- renderers: `85782`
- animators: `2723`
- particle systems: `262`
- terrains: `32`
- labels: `17020`

## Notes

- The generated scene is intentionally not tracked. It is too large for normal Git hosting and depends on local third-party purchased content.
- The generated preview materials/controllers under `Assets/Generated/Showcase/` are also intentionally untracked and are recreated by the builder.
