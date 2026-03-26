# HPR Event Bus

Runtime event bus infrastructure and gameplay event payloads used to decouple HPR modules.

Included:
- `IGameEventBus`
- `EventManager`
- gameplay event payloads for damage, weapon fire, pickup, kills, impact, and HUD-related notifications
- `IEventBusSource`
- `EventBusSourceAdapter`

Typical usage:
- add `EventManager` to a composition root object
- add `EventBusSourceAdapter` when you need a ready-made `IEventBusSource` component
- expose the bus through `IEventBusSource`
- publish and subscribe to events instead of calling other systems directly

Current limitation:
- the payload set still includes FPS-domain events and may later split into generic bus infrastructure plus separate domain-event packages
