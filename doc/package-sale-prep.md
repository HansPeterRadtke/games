# Package Sale Preparation

Generated on 2026-04-01T11:03:17+02:00

## Prepared sellable packages
- `com.hpr.eventbus`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_eventbus`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.eventbus/com.hpr.eventbus.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.eventbus/com.hpr.eventbus_upm.zip`, dependencies `com.hpr.eventbus`
- `com.hpr.composition`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_composition`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.composition/com.hpr.composition.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.composition/com.hpr.composition_upm.zip`, dependencies `com.hpr.composition`
- `com.hpr.save`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_save`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.save/com.hpr.save.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.save/com.hpr.save_upm.zip`, dependencies `com.hpr.save`
- `com.hpr.stats`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_stats`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.stats/com.hpr.stats.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.stats/com.hpr.stats_upm.zip`, dependencies `com.hpr.eventbus com.hpr.stats`
- `com.hpr.inventory`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_inventory`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.inventory/com.hpr.inventory.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.inventory/com.hpr.inventory_upm.zip`, dependencies `com.hpr.inventory`
- `com.hpr.interaction`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_interaction`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.interaction/com.hpr.interaction.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.interaction/com.hpr.interaction_upm.zip`, dependencies `com.hpr.eventbus com.hpr.inventory com.hpr.interaction`
- `com.hpr.abilities`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_abilities`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.abilities/com.hpr.abilities.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.abilities/com.hpr.abilities_upm.zip`, dependencies `com.hpr.eventbus com.hpr.stats com.hpr.abilities`
- `com.hpr.weapons`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_weapons`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.weapons/com.hpr.weapons.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.weapons/com.hpr.weapons_upm.zip`, dependencies `com.hpr.weapons`
- `com.hpr.ai`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_ai`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.ai/com.hpr.ai.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.ai/com.hpr.ai_upm.zip`, dependencies `com.hpr.ai`
- `com.hpr.world`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_world`, unitypackage `/data/src/github/games/dist/package_sale_artifacts/com.hpr.world/com.hpr.world.unitypackage`, zip `/data/src/github/games/dist/package_sale_artifacts/com.hpr.world/com.hpr.world_upm.zip`, dependencies `com.hpr.world`

## Artifact root
- `/data/tmp/hpr_assetstore_sale/artifacts`

## Tracked artifact root
- `/data/src/github/games/dist/package_sale_artifacts`
- each package directory now contains the exported `.unitypackage`, UPM zip, screenshot PNG, info file, and listing draft markdown

## Project root
- `/data/tmp/hpr_assetstore_sale/projects`

## Official Asset Store Tools validation
- Command: `unity/tools/release/run_official_asset_store_validator.sh`
- Logs: `/data/src/github/games/doc/logs/asset_store_tools_validation`

## Human-only steps left
- Finalize Unity Asset Store publisher listings, pricing, categories, and support/contact identity.
- Review the generated screenshot and listing draft for each package and replace them only if you want a more polished marketing presentation.
- Perform a final human review in each clean sale project before upload.
- Upload the generated `.unitypackage` files or package source zips through the publisher portal.
- Handle publisher-account, payout, tax, and legal acceptance steps outside the repo.

## Not prepared for sale
- Packages outside the frozen sellable set in `unity/tools/release/release_packages.json` remain excluded for engineering reasons and are not included in these artifacts.
