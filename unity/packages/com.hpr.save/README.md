# HPR Save

Reusable save contracts and serializable save payload types for gameplay packages.

What is included:
- serializable vector and quaternion wrappers
- generic entity and player save payload models
- saveable entity contract for runtime components

Setup:
- add `com.hpr.save` as a local Unity package
- reference `HPR.Save.Runtime` from dependent asmdefs

Typical usage:
- implement `ISaveableEntity` on runtime components that expose persistent state
- use `SaveGameData` as the top-level payload when composing a game-specific save system
- keep scene/game-specific save orchestration outside this package

Current scope:
- generic save models only
- no project-specific save paths, slot UI, or scene restoration logic
