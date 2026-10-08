# HPR AI Demo

This demo scene shows authored `EnemyData` assets driving simple preview archetypes.

- Scene: `AiDemo.unity`
- Builder: `HPR.AiDemoSceneBuilder.BuildDemoScene`
- Validator: `HPR.AiPackageValidator.ValidateInBatch`

## Runtime
The package includes `EnemyRuntimeState` for health/death, attack cooldowns, and patrol/chase/hold/attack decisions. The package validator exercises this runtime against the included raider and sentry data.
