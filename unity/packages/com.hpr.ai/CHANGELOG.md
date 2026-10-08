# Changelog

## 0.2.0 - 2026-10-08
- added `EnemyRuntimeState` with health, damage, healing, death, and attack-cooldown state
- added deterministic patrol/chase/hold/attack/dead decisions based on authored archetype and target distance
- added `EnemyAttackResult` handoff for melee/ranged combat execution
- expanded demo validation to execute runtime decisions and attacks for included enemy assets
- expanded EditMode coverage to five runtime/data tests

## 0.1.0 - 2026-03-28
- productized `EnemyData` as a standalone enemy-archetype package
- added package demo scene, demo assets, and batch validator
- added external-user documentation and release metadata
