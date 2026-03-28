# HPR AI

Reusable enemy-definition assets for Unity projects that want authored AI archetypes
without hardcoding enemy tuning directly into runtime scripts.

## Audience
Use this package when you want:
- enemy archetypes authored as `ScriptableObject` assets
- stable ids and behavior categories for AI-driven runtime systems
- a reusable data schema for health, speed, range, and attack tuning

## Included
- `EnemyData`
- `EnemyAIType`
- `EnemyAttackStyle`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- no local package dependencies
- Unity `UnityEngine` only

## Installation
1. Add `com.hpr.ai` to your Unity project.
2. Reference `HPR.Ai.Runtime` from dependent asmdefs.
3. Create enemy assets via `Assets > Create > HPR > AI > Enemy`.
4. Feed those assets into your own runtime enemy/agent system.

## Quick start
```csharp
[SerializeField] private EnemyData raider;

private void Start()
{
    UnityEngine.Debug.Log($"Loaded enemy {raider.DisplayName} with speed {raider.MoveSpeed}");
}
```

## API overview
- `EnemyData` stores ids, display names, behavior categories, combat tuning, and visual offsets
- `EnemyAIType` selects a high-level behavior family for the consuming runtime
- `EnemyAttackStyle` distinguishes melee and ranged archetypes

## Demo
- Scene: `Packages/com.hpr.ai/Demo/AiDemo.unity`
- Builder: `AiDemoSceneBuilder.BuildDemoScene`
- Batch validator: `AiPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod AiPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=AiPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.ai`

## Extension points
- add custom editor tooling that consumes `EnemyData`
- build your own runtime behavior layer keyed by `EnemyData.Id`
- use the visual offset fields to position art or rigs in your own AI presentation pipeline

## Limitations
- this package defines AI data only; it does not include a full runtime behavior tree or navigation system
- combat execution and target selection remain the responsibility of the consuming project
