using UnityEngine;

[RequireComponent(typeof(EventManager))]
public class EventBusSourceAdapter : MonoBehaviour, IEventBusSource
{
    private EventManager eventManager;

    public IEventBus EventBus
    {
        get
        {
            if (eventManager == null)
            {
                eventManager = GetComponent<EventManager>();
            }

            return eventManager != null ? eventManager.EventBus : null;
        }
    }
}
