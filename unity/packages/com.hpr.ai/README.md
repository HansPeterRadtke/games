# HPR AI

Reusable enemy and agent data definitions for Unity gameplay packages.

## Included
- `EnemyData` ScriptableObject
- `EnemyAIType` and `EnemyAttackStyle` enums

## Current scope
This package currently provides the data layer for AI-driven gameplay. Runtime enemy behavior remains in the game composition package while the split continues.

## Setup
1. Add the package to your Unity project.
2. Reference `HPR.Ai.Runtime` from dependent asmdefs.
3. Create enemy assets via `Assets > Create > HPR > AI > Enemy`.

## Validation
- Clean-project import validation is automated through `unity/tools/packages/validate_local_packages.sh com.hpr.ai`.
