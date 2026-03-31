# Package Sale Preparation

Generated on 2026-03-31T12:28:01+02:00

## Prepared sellable packages
- `com.hpr.eventbus`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_eventbus`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.eventbus/com.hpr.eventbus.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.eventbus/com.hpr.eventbus_upm.zip`, dependencies `com.hpr.eventbus`
- `com.hpr.composition`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_composition`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.composition/com.hpr.composition.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.composition/com.hpr.composition_upm.zip`, dependencies `com.hpr.composition`
- `com.hpr.save`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_save`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.save/com.hpr.save.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.save/com.hpr.save_upm.zip`, dependencies `com.hpr.save`
- `com.hpr.stats`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_stats`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.stats/com.hpr.stats.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.stats/com.hpr.stats_upm.zip`, dependencies `com.hpr.eventbus com.hpr.stats`
- `com.hpr.inventory`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_inventory`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.inventory/com.hpr.inventory.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.inventory/com.hpr.inventory_upm.zip`, dependencies `com.hpr.inventory`
- `com.hpr.interaction`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_interaction`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.interaction/com.hpr.interaction.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.interaction/com.hpr.interaction_upm.zip`, dependencies `com.hpr.eventbus com.hpr.inventory com.hpr.interaction`
- `com.hpr.abilities`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_abilities`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.abilities/com.hpr.abilities.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.abilities/com.hpr.abilities_upm.zip`, dependencies `com.hpr.eventbus com.hpr.stats com.hpr.abilities`
- `com.hpr.weapons`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_weapons`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.weapons/com.hpr.weapons.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.weapons/com.hpr.weapons_upm.zip`, dependencies `com.hpr.weapons`
- `com.hpr.ai`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_ai`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.ai/com.hpr.ai.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.ai/com.hpr.ai_upm.zip`, dependencies `com.hpr.ai`
- `com.hpr.world`: project `/data/tmp/hpr_assetstore_sale/projects/sale_com_hpr_world`, unitypackage `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.world/com.hpr.world.unitypackage`, zip `/data/tmp/hpr_assetstore_sale/artifacts/com.hpr.world/com.hpr.world_upm.zip`, dependencies `com.hpr.world`

## Artifact root
- `/data/tmp/hpr_assetstore_sale/artifacts`

## Project root
- `/data/tmp/hpr_assetstore_sale/projects`

## Preparation command
- `unity/tools/release/prepare_sale_packages.sh`

## Proof logs
- `doc/logs/package_sale_prep/`
- Each package run records:
  - wrapper validation log
  - clean-project import log
  - package validator execute log
  - export refresh log
  - export log

## Human-only steps left
- Create/update Unity Asset Store publisher listings, pricing, categories, screenshots, promo copy, icons, and support links.
- Perform a final human review in each clean sale project before upload.
- Upload the generated `.unitypackage` files or package source zips through the publisher portal.
- Handle publisher-account, payout, tax, and legal acceptance steps outside the repo.

## Not prepared for sale
- Packages outside the frozen sellable set in `unity/tools/release/release_packages.json` remain excluded for engineering reasons and are not included in these artifacts.
