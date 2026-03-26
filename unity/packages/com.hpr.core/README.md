# HPR Core

Shared runtime contracts for composing HPR gameplay modules without concrete cross-package references.

Included:
- gameplay state and flow interfaces
- status/prompt/HUD sink interfaces
- player death and menu command contracts

Intended use:
- reference this package from other HPR packages that need shared service contracts
- keep this package generic and free of project-specific orchestration code

Current public API:
- `IGameplayStateSource`
- `IStatusMessageSink`
- `IInteractionPromptSink`
- `IHudRefreshSink`
- `IThreatScanner`
- `IGameplayFlowCommands`
- `IGameMenuCommands`
- `IPlayerDeathHandler`

This package should remain small and stable. Higher-level game logic does not belong here.
