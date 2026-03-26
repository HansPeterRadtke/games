using System;
using System.Collections.Generic;
using UnityEngine;

public class EventManager : MonoBehaviour, IGameEventBus
{
    private readonly Dictionary<Type, Delegate> subscribers = new Dictionary<Type, Delegate>();

    public void Publish<TEvent>(TEvent gameEvent) where TEvent : GameEvent
    {
        if (gameEvent == null)
        {
            return;
        }

        Type currentType = typeof(TEvent);
        while (currentType != null && typeof(GameEvent).IsAssignableFrom(currentType))
        {
            if (subscribers.TryGetValue(currentType, out Delegate handlers) && handlers is Action<TEvent> typedHandlers)
            {
                typedHandlers.Invoke(gameEvent);
            }

            currentType = currentType.BaseType;
        }
    }

    public void Subscribe<TEvent>(Action<TEvent> handler) where TEvent : GameEvent
    {
        if (handler == null)
        {
            return;
        }

        Type eventType = typeof(TEvent);
        if (subscribers.TryGetValue(eventType, out Delegate existing))
        {
            subscribers[eventType] = Delegate.Combine(existing, handler);
            return;
        }

        subscribers[eventType] = handler;
    }

    public void Unsubscribe<TEvent>(Action<TEvent> handler) where TEvent : GameEvent
    {
        if (handler == null)
        {
            return;
        }

        Type eventType = typeof(TEvent);
        if (!subscribers.TryGetValue(eventType, out Delegate existing))
        {
            return;
        }

        Delegate updated = Delegate.Remove(existing, handler);
        if (updated == null)
        {
            subscribers.Remove(eventType);
            return;
        }

        subscribers[eventType] = updated;
    }
}
