# HPR Enemy Runtime

Data-driven enemy archetypes plus a deterministic, navigation-independent runtime for health, death, attack cooldowns, distance-based behavior decisions, and attack results.

## Audience
Use this package when you want:
- enemy archetypes authored as `ScriptableObject` assets
- stable ids and behavior categories for AI-driven runtime systems
- package-owned runtime decisions for patrol, chase, hold, attack, and dead states
- health/damage/healing and attack cooldown state that works without scene objects
- a clean handoff to your own navigation, movement, animation, projectile, and perception layers

## Included
- `EnemyData`
- `EnemyRuntimeState`
- `EnemyRuntimeDecision`
- `EnemyAttackResult`
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
4. Create one `EnemyRuntimeState` per live enemy instance.
5. Feed `Decide(targetDistance)` and successful `TryAttack(...)` results into your own movement/combat/presentation layer.

## Quick start
```csharp
[SerializeField] private EnemyData raider;
private EnemyRuntimeState state;

private void Start()
{
    state = new EnemyRuntimeState(raider);
}

private void Update()
{
    state.Tick(Time.deltaTime);
    float distance = Vector3.Distance(transform.position, target.position);

    switch (state.Decide(distance))
    {
        case EnemyRuntimeDecision.Chase:
            // Drive your NavMesh/custom movement toward the target.
            break;
        case EnemyRuntimeDecision.Attack:
            if (state.TryAttack(distance, out EnemyAttackResult attack))
            {
                // Apply melee/projectile execution in your own combat layer.
            }
            break;
    }
}
```

## Runtime behavior
- `EnemyRuntimeState` starts from `EnemyData.MaxHealth` and tracks live health/death state.
- `Decide(targetDistance)` maps authored archetypes and distance to `Patrol`, `Hold`, `Chase`, `Attack`, or `Dead`.
- `TryAttack(...)` enforces attack range and cooldown, then returns authored damage, attack style, projectile speed, and projectile impact.
- `Tick(deltaTime)` advances cooldowns without requiring a `MonoBehaviour`.
- `ApplyDamage(...)` clamps at zero and stops behavior when dead.
- `Heal(...)` clamps at `MaxHealth` and deliberately does not resurrect a dead state.

## Decision model
- `PatrolChase`: patrol outside chase range, chase inside chase range, attack inside attack range when cooldown is ready.
- `AggressiveChase`: chase whenever not attacking/dead.
- `StationaryAttack`: hold position whenever not attacking/dead.
- while an attack is cooling down, mobile archetypes return to their movement decision and stationary archetypes hold.

## API overview
- `EnemyData` stores ids, behavior family, combat tuning, ranges, projectile metadata, and visual offsets.
- `EnemyRuntimeState` owns transient health and attack-cooldown state.
- `EnemyRuntimeDecision` is the navigation/presentation-agnostic behavior handoff.
- `EnemyAttackResult` is the combat handoff for melee or ranged execution.

## Demo
- Scene: `Packages/com.hpr.ai/Demo/AiDemo.unity`
- Builder: `HPR.AiDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.AiPackageValidator.ValidateInBatch`
- the validator creates runtime state for both included enemy archetypes, verifies close-range attack decisions, and executes their authored attacks.

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.AiPackageValidator.ValidateInBatch -quit`
- repository helper:
  - `EXECUTE_METHOD=HPR.AiPackageValidator.ValidateInBatch RUN_TESTS=1 unity/tools/packages/validate_local_packages.sh com.hpr.ai`
- current EditMode coverage includes distance decisions, stationary hold behavior, attack cooldown/results, health/healing/death, and stable defaults.

## Extension points
- map `EnemyRuntimeDecision.Chase` to NavMesh, steering, character-controller, or custom movement.
- map `EnemyAttackResult` to melee damage, projectiles, animation, audio, and VFX.
- feed target distance from your own perception/sensing system.
- add higher-level target selection, patrol routes, threat tables, squads, or behavior trees around the deterministic package state.

## Limitations
- no pathfinding, steering, NavMesh integration, or movement controller
- no perception/target selection or line-of-sight system
- no spawner, behavior tree, animation, audio, or VFX layer
- the package intentionally provides deterministic combat/decision state rather than a monolithic AI framework

## Samples
- Import the package sample from Package Manager > Samples > AI Demo.
- The imported sample contains the demo scene and helper assets from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.
