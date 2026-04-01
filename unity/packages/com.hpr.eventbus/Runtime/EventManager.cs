using System;
using UnityEngine;

namespace HPR
{
    public class EventManager : MonoBehaviour, IEventBusSource
    {
        private readonly EventBus eventBus = new();

        public IEventBus EventBus => eventBus;

        public IDisposable Subscribe<TEvent>(Action<TEvent> handler) where TEvent : class
        {
            return eventBus.Subscribe(handler);
        }

        public void Unsubscribe<TEvent>(Action<TEvent> handler) where TEvent : class
        {
            eventBus.Unsubscribe(handler);
        }

        public void Publish<TEvent>(TEvent eventData) where TEvent : class
        {
            eventBus.Publish(eventData);
        }

        private void OnDestroy()
        {
            eventBus.Dispose();
        }
    }
}
