# HPR Weapons Demo

This demo scene shows authored `WeaponData` assets driving a simple static preview setup.

- Scene: `WeaponsDemo.unity`
- Builder: `HPR.WeaponsDemoSceneBuilder.BuildDemoScene`
- Validator: `HPR.WeaponsPackageValidator.ValidateInBatch`

## Runtime
The package also includes `WeaponRuntimeState` for magazine/reserve ammo, cooldown, firing, ammo pickups, and reload behavior. The demo package validator exercises this runtime against the included rifle and scattergun data.
