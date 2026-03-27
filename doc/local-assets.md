# Local Asset Inventory

This file documents the real local-only Unity asset state on this machine.
It exists because the imported art is intentionally not tracked in git.

## Policy
- none of the imported asset folders listed here are committed
- none of the `.unitypackage` downloads are committed
- this file is the takeover map for recreating or auditing the art state

## Imported local asset roots currently present in the Unity project
Project path:
- `unity/projects/fps_demo/Assets`

Current local-only imported roots:
- `ALP_Assets`
- `Brick Project Studio`
- `Flooded_Grounds`
- `TerrainDemoScene_URP`
- `Free Wood Door Pack`
- `FurnishedCabin`
- `Furniture Mega Pack`
- `Low Poly Weapons VOL.1`
- `NatureStarterKit2`
- `POLYGON city pack`
- `Survivalist`
- `DoubleL`
- `Kevin Iglesias`
- `_TerrainAutoUpgrade`
- `nappin`
- `npc_casual_set_00`

Tracked/project roots that are not third-party imports:
- `Data`
- `Scenes`

## Selected Asset Store packages for this project
The active selection file is:
- `unity/assetstore/selected_assets.json`

Selected packages and intended roots/integration labels:
- `280509` - `Free Wood Door Pack` - doors
- `151980` - `Low Poly Weapons VOL.1` - weapons
- `258782` - `House Interior - Free` -> `Assets/nappin/HouseInteriorPack` - house
- `330002` - `Furniture Mega Pack - Free` -> `Assets/Furniture Mega Pack` - furniture
- `71426` - `Furnished Cabin` - environment
- `124055` - `Apartment Kit` / `Brick Project Studio` - environment
- `107224` - `CITY package` / `POLYGON city pack` - environment
- `326131` - `npc_casual_set_00` - characters
- `181470` - `Survivalist character` -> `Assets/Survivalist` - characters
- `157920` - `Human Crafting Animations FREE` -> `Assets/Kevin Iglesias/Human Animations` - animations
- `288783` - `RPG Animations Pack FREE` -> `Assets/DoubleL` - animations
- `52977` - `Nature Starter Kit 2` - environment
- `138810` - `Grass Flowers Pack Free` -> `Assets/ALP_Assets` - environment
- `279940` - `Realistic Terrain Textures FREE` -> `Assets/ALP_Assets` - environment
- `48529` - `Flooded Grounds` -> `Assets/Flooded_Grounds` - environment
- `213197` - `Unity Terrain - URP Demo Scene` -> `Assets/TerrainDemoScene_URP` - environment
- `267961` - `Starter Assets: Character Controllers | URP` - starter assets

## Local Unity Asset Store cache
Authoritative local cache path:
- `/home/hans/.local/share/unity3d/Asset Store-5.x`

Verified cached `.unitypackage` files currently present there:
- `Nature Starter Kit 2.unitypackage`
- `Free Wood Door Pack.unitypackage`
- `Furnished Cabin.unitypackage`
- `Human Crafting Animations FREE.unitypackage`
- `Flooded Grounds.unitypackage`
- `Low Poly Weapons VOL1.unitypackage`
- `Furniture Mega Pack - Free.unitypackage`
- `CITY package.unitypackage`
- `RPGAnimationsPackFREE.unitypackage`
- `Starter Assets Character Controllers URP.unitypackage`
- `Unity Terrain - URP Demo Scene.unitypackage`
- `Survivalist character.unitypackage`
- `Grass Flowers Pack Free.unitypackage`
- `Realistic Terrain Textures FREE.unitypackage`
- `Apartment Kit.unitypackage`
- `npccasualset00.unitypackage`
- `House Interior - Free.unitypackage`

## Repo-local download workspace
Repo-local download area:
- `unity/assetstore/downloads`

Current state there:
- `151980_Low_Poly_Weapons_VOL.1.unitypackage`
- `151980_Low_Poly_Weapons_VOL_1.unitypackage`
- `258782_House_Interior_-_Free.unitypackage`
- `330002_Furniture_Mega_Pack_-_Free.unitypackage.part`

Important:
- the repo-local downloads folder is not the source of truth
- the Unity Asset Store cache under `/home/hans/.local/share/unity3d/Asset Store-5.x` is the real completed cache
- the `.part` furniture file is stale and not meaningful by itself

## Integration state by category
### Confirmed integrated into gameplay/tooling path
- Free Wood Door Pack
- Low Poly Weapons VOL.1
- House Interior - Free / nappin
- Furniture Mega Pack
- character packs (`npc_casual_set_00`, `Survivalist`)
- animation packs (`Kevin Iglesias/Human Animations`, `DoubleL`)
- several environment packs via local scene integration tooling

### Known integration/use notes
- weapon prefabs from `Low Poly Weapons VOL.1` required per-weapon rotation handling; the pack is not orientation-standardized
- animation integration now uses a generated local humanoid combat controller under `Assets/DoubleL/HPRGenerated` plus ambient NPC placements driven from Kevin Iglesias controllers
- furniture from mixed packs caused unrealistic scale/material issues; current integration was narrowed toward `Furniture Mega Pack` exact prefabs for furniture placement
- `Nature Starter Kit 2` needed compatibility fixup for older scripts/editor pieces after import
- local imported art still needs another visual polish pass; this is not considered final content quality

## Logs and diagnostics
Useful local log folders:
- `unity/assetstore/logs`
- `doc/logs`

Examples of meaningful logs already present:
- native download logs for each package
- native import logs for each imported package
- smoke test logs after specific integration passes
- build logs from scripted Unity batch runs

## Rebuild / re-audit guidance
If a new developer needs to audit the local art state:
1. inspect `unity/assetstore/selected_assets.json`
2. inspect the imported roots listed above under `unity/projects/fps_demo/Assets`
3. inspect `unity/assetstore/logs`
4. rebuild with `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
5. smoke test with `unity/tools/fps_demo/smoke_test.sh`

## Current bottom line
- the real local asset data exists on this machine
- it is partially integrated
- it is intentionally not tracked by git
- this file is the inventory bridge between the tracked repo and that local-only art state
