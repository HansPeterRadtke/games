# HPR Event Bus

Runtime event bus infrastructure and gameplay event payloads used to decouple HPR modules.

Included:
- `IGameEventBus`
- `EventManager`
- gameplay event payloads for damage, weapon fire, pickup, kills, impact, and HUD-related notifications
- `IEventBusSource`

Typical usage:
- add `EventManager` to a composition root object
- expose it through `IEventBusSource`
- publish and subscribe to events instead of calling other systems directly

Current limitation:
- the payload set still includes FPS-domain events and may later split into generic bus infrastructure plus separate domain-event packages
