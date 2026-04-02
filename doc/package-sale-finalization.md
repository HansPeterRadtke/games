# Package Sale Finalization

This report covers the frozen sellable package set from the current repo state.

## Launch recommendation by package
- `com.hpr.eventbus` — `launch_now` — Clear standalone value, isolated API surface, strong reusable fit across gameplay and tool layers, and easy screenshotable story once event flow is visualized.
- `com.hpr.composition` — `launch_now` — Architecturally clean, independently useful, validated headless, and strong companion product for teams building modular Unity runtime composition.
- `com.hpr.save` — `launch_now` — Narrow, understandable product scope: snapshot contracts and restore flow that buyers can integrate into their own persistence layer without framework lock-in.
- `com.hpr.stats` — `launch_now` — Clear gameplay-system value, real runtime behavior, validated bugs already fixed, and an easy buyer story around health, stamina, damage, and healing.
- `com.hpr.inventory` — `launch_now` — Clear reusable runtime value with actual quantity tracking, sample items, and straightforward integration into pickups, save systems, and gameplay logic.
- `com.hpr.interaction` — `launch_now` — Buyer-facing value is easy to understand from demos and screenshots: sensors, pickups, keys, and doors with explicit bindings and package-safe runtime boundaries.
- `com.hpr.abilities` — `launch_now` — The package already reads like a real product: ability assets, effect assets, cooldowns, unlock tracking, and visible runtime behavior backed by clean validations.
- `com.hpr.weapons` — `second_wave` — Technically clean, but the current value proposition is data-definition heavy and weaker than the first-wave systems unless paired with a stronger runtime controller or bundle story.
- `com.hpr.ai` — `second_wave` — The package is technically solid, but buyer-facing value is narrower because it defines AI archetype data without a stronger runtime behavior/controller story.
- `com.hpr.world` — `bundle_only` — Useful supporting code, but too thin to lead as a standalone paid Asset Store listing today; best packaged inside a broader world-authoring or gameplay-data bundle.

## Screenshot regeneration
- Every package now carries three tracked screenshots in `dist/package_sale_artifacts/<package>/screenshots/`.
- The screenshot generator is package-specific and reproducible from `unity/tools/release/HprPackageScreenshotRunner.cs`.
- Exact duplicate screenshot hashes are rejected during draft generation.

## Screenshot files
### `com.hpr.eventbus`
- `dist/package_sale_artifacts/com.hpr.eventbus/screenshots/01_overview.png` — sha256 `6fdb597b5f367bef3a2c2dd9e38636e5409ffe42ae253c7284498630768003de`
- `dist/package_sale_artifacts/com.hpr.eventbus/screenshots/02_workflow.png` — sha256 `17c1a4acb50ba326354c65233185327e7e0aec54e9657911c667306b40f312ba`
- `dist/package_sale_artifacts/com.hpr.eventbus/screenshots/03_details.png` — sha256 `e9b3d0ea0f066910a31079ffe5770e9e0884db5ed002542dc47994f2c6eeb803`

### `com.hpr.composition`
- `dist/package_sale_artifacts/com.hpr.composition/screenshots/01_overview.png` — sha256 `3ae9a1be33b09806a53ce0fdb741c0e3707e57a1cdd2e4214e6db022af50c901`
- `dist/package_sale_artifacts/com.hpr.composition/screenshots/02_workflow.png` — sha256 `f53f36256385bfc791cbafb6215b5f68eb41f3851168643dccee83041a4c11a1`
- `dist/package_sale_artifacts/com.hpr.composition/screenshots/03_details.png` — sha256 `c5745806f0df6069ea91d1fb0894caa84e54ac2e6f943f3abc067999811f2ed2`

### `com.hpr.save`
- `dist/package_sale_artifacts/com.hpr.save/screenshots/01_overview.png` — sha256 `fcdeb7cbf53b97699c8b7780521de1485d1099080bc3d765220be476b2209770`
- `dist/package_sale_artifacts/com.hpr.save/screenshots/02_workflow.png` — sha256 `e137e8fea716adc76825944cae3a8220966fc3f1eba61c84721e6ab79c76f410`
- `dist/package_sale_artifacts/com.hpr.save/screenshots/03_details.png` — sha256 `790f43e33bd01b6f6bb45f4ad811d6451bb747248e690d47a1193b8568de2404`

### `com.hpr.stats`
- `dist/package_sale_artifacts/com.hpr.stats/screenshots/01_overview.png` — sha256 `7a19856f084063a52d421dbfa82a29ba754772438c1dffa54be958f877f41d23`
- `dist/package_sale_artifacts/com.hpr.stats/screenshots/02_workflow.png` — sha256 `a63ad5c5b14d32005de93a213417e92e2282a73b97453f2553e389c3f48f1670`
- `dist/package_sale_artifacts/com.hpr.stats/screenshots/03_details.png` — sha256 `1177dd8d2036ddbf82c0339fd0ce166f18abe85ffda32a721185ef6f9dd3e1c8`

### `com.hpr.inventory`
- `dist/package_sale_artifacts/com.hpr.inventory/screenshots/01_overview.png` — sha256 `3b375ec53ac5a344eeddfb5983b4e94c37fec9ff4b0e6413b995d92370ec1df5`
- `dist/package_sale_artifacts/com.hpr.inventory/screenshots/02_workflow.png` — sha256 `b5d65051461731469e041b2dd0da1377718512446a0fa945bec57bb155071ea8`
- `dist/package_sale_artifacts/com.hpr.inventory/screenshots/03_details.png` — sha256 `643d8f5ecf2d5eef09ee53001f79640ec4cd35191a91ce016358f55e2b000848`

### `com.hpr.interaction`
- `dist/package_sale_artifacts/com.hpr.interaction/screenshots/01_overview.png` — sha256 `2a4d0e93ca6fd232d308958ac8fbeab249820958954ce6dc7f1fda6e1779c4aa`
- `dist/package_sale_artifacts/com.hpr.interaction/screenshots/02_workflow.png` — sha256 `47668ff722b0eb4902b349fd717b1ef05d35249e7294812a17f2063076a909e5`
- `dist/package_sale_artifacts/com.hpr.interaction/screenshots/03_details.png` — sha256 `250fdf3c6377ea9cc19c6fa4766674ce02db8df960fc80ec1ee2b345614ed6bc`

### `com.hpr.abilities`
- `dist/package_sale_artifacts/com.hpr.abilities/screenshots/01_overview.png` — sha256 `a929f1612fa7941be27662fe2fdecbd17b41552c3ec0eba6b2e758422a9a0314`
- `dist/package_sale_artifacts/com.hpr.abilities/screenshots/02_workflow.png` — sha256 `429869fde45652242ac5c3f89a9354aeece540f3d00f5a2f56fc64fd5b1fce33`
- `dist/package_sale_artifacts/com.hpr.abilities/screenshots/03_details.png` — sha256 `31433eedb9a297705615195d0b88c49266f3e85d47ff02b4bd8ecd38cdff0603`

### `com.hpr.weapons`
- `dist/package_sale_artifacts/com.hpr.weapons/screenshots/01_overview.png` — sha256 `f3e27e6a9958b6e927f20a7e94602b3114a28ecad657e9daa2c1ff3f99d81771`
- `dist/package_sale_artifacts/com.hpr.weapons/screenshots/02_workflow.png` — sha256 `c171c3cff05fe1b09dd40d42eaed3573b857c0d93d528a5268e9e22a2f8df040`
- `dist/package_sale_artifacts/com.hpr.weapons/screenshots/03_details.png` — sha256 `8b58fa8535344e365877b41341923a87926ef308d425e79cccadbbc7b9f75be6`

### `com.hpr.ai`
- `dist/package_sale_artifacts/com.hpr.ai/screenshots/01_overview.png` — sha256 `1c5e1e62ed68cfeb039cc06d0f1f3cc807a358965e555352f262ec187cd56008`
- `dist/package_sale_artifacts/com.hpr.ai/screenshots/02_workflow.png` — sha256 `1821ea3fc997493597034ff76bdceff21786f170e1adbbf67fe26b263137ba96`
- `dist/package_sale_artifacts/com.hpr.ai/screenshots/03_details.png` — sha256 `f40489b3de23ee8672c536da3862fbe2392ecc88e194df57aba3db95cf12694d`

### `com.hpr.world`
- `dist/package_sale_artifacts/com.hpr.world/screenshots/01_overview.png` — sha256 `30caae8c2ccd60b25f7134ce9b1a0bfda43c967624bf167959340437c5bb88b7`
- `dist/package_sale_artifacts/com.hpr.world/screenshots/02_workflow.png` — sha256 `5c07bb9f2a34252d2361cefaa3e7cc93d17dac60b70c71a8772057438cd677b4`
- `dist/package_sale_artifacts/com.hpr.world/screenshots/03_details.png` — sha256 `0fdbe0251c9c2fbec5a34df96637a576facc5d501c7ad1dffb04b9f0310c207e`

## Current tracked artifact root
- `dist/package_sale_artifacts`

## Proof roots
- `doc/logs/package_validation/`
- `doc/logs/package_sale_prep/`
- `doc/logs/asset_store_tools_validation/`
- `doc/logs/` for release audit, dependency audit, build, and smoke logs

## Human-only boundary
See `doc/human-only-final-steps.md` for the remaining steps that cannot be completed by repository automation.
