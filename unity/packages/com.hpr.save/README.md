# HPR Save

Minimal save-state primitives for Unity projects that want serializable transform/entity data
without taking a dependency on a concrete game, scene, or save-slot implementation.

## Audience
Use this package when you want:
- package-safe save data wrappers for `Vector3` and `Quaternion`
- a reusable `ISaveableEntity` contract for runtime components
- generic entity state payloads that a higher-level save system can persist

## Included
- `SerializableVector3`
- `SerializableQuaternion`
- `SaveEntityData`
- `ISaveableEntity`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- no local package dependencies

## Installation
1. Add `com.hpr.save` to your Unity project.
2. Reference `HPR.Save.Runtime` from dependent asmdefs.
3. Implement `ISaveableEntity` on any component that should capture and restore its own state.

## Quick start
```csharp
public sealed class DoorSaveState : UnityEngine.MonoBehaviour, ISaveableEntity
{
    public string SaveId => "door_main";

    public SaveEntityData CaptureState()
    {
        return new SaveEntityData
        {
            id = SaveId,
            active = gameObject.activeSelf,
            position = new SerializableVector3(transform.position),
            rotation = new SerializableQuaternion(transform.rotation)
        };
    }

    public void RestoreState(SaveEntityData data)
    {
        transform.position = data.position.ToVector3();
        transform.rotation = data.rotation.ToQuaternion();
        gameObject.SetActive(data.active);
    }
}
```

## API overview
- `SerializableVector3` and `SerializableQuaternion` convert Unity structs into JSON-friendly values
- `SaveEntityData` stores generic entity state fields without assuming a specific game model
- `ISaveableEntity` lets each runtime component own its own capture and restore logic

## Demo
- Scene: `Packages/com.hpr.save/Demo/SaveDemo.unity`
- Builder: `SaveDemoSceneBuilder.BuildDemoScene`
- Batch validator: `SavePackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod SavePackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=SavePackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.save`

## Extension points
- compose multiple `ISaveableEntity` implementations into your own save coordinator
- extend save payloads in your own game code instead of modifying this package
- serialize `SaveEntityData` with any persistence backend you prefer

## Limitations
- this package does not provide save-slot UI, disk IO, or profile management
- it intentionally does not define player-, quest-, or weapon-specific save models
