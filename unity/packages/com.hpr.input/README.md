# HPR Input

Input abstraction, action binding, and player option storage for HPR gameplay packages.

Included:
- `GameAction`
- `GameOptionsData`
- `GameOptionsStore`
- `IInputSource`
- `IInputBindingsSource`
- `IOptionsController`
- `UnityInputSource`

Typical usage:
- poll input through `IInputSource` instead of raw `Input.*`
- expose current bindings and options through `IInputBindingsSource`
- mutate rebinds and settings through `IOptionsController`

Current scope:
- Unity legacy input adapter
- option persistence via `PlayerPrefs`
- no package-standalone demo scene yet
