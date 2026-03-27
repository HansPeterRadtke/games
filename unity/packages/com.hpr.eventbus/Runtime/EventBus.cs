using System;
using System.Collections.Generic;

public sealed class EventBus : IEventBus, IDisposable
{
    private readonly Dictionary<Type, List<SubscriptionEntry>> subscribers = new();
    private readonly object gate = new();

    public IDisposable Subscribe<TEvent>(Action<TEvent> handler) where TEvent : class
    {
        if (handler == null)
        {
            return EmptySubscription.Instance;
        }

        var entry = new SubscriptionEntry(typeof(TEvent), handler, payload => handler((TEvent)payload));
        lock (gate)
        {
            if (!subscribers.TryGetValue(entry.EventType, out List<SubscriptionEntry> handlers))
            {
                handlers = new List<SubscriptionEntry>();
                subscribers[entry.EventType] = handlers;
            }

            handlers.Add(entry);
        }

        return new EventSubscription(this, entry.EventType, handler);
    }

    public void Unsubscribe<TEvent>(Action<TEvent> handler) where TEvent : class
    {
        Remove(typeof(TEvent), handler);
    }

    public void Publish<TEvent>(TEvent eventData) where TEvent : class
    {
        if (eventData == null)
        {
            return;
        }

        Type concreteType = eventData.GetType();
        SubscriptionEntry[] snapshot;
        lock (gate)
        {
            var collected = new List<SubscriptionEntry>();
            foreach ((Type subscriptionType, List<SubscriptionEntry> handlers) in subscribers)
            {
                if (!subscriptionType.IsAssignableFrom(concreteType))
                {
                    continue;
                }

                collected.AddRange(handlers);
            }

            snapshot = collected.ToArray();
        }

        foreach (SubscriptionEntry entry in snapshot)
        {
            entry.Invoke(eventData);
        }
    }

    public void Clear()
    {
        lock (gate)
        {
            subscribers.Clear();
        }
    }

    public void Dispose()
    {
        Clear();
    }

    internal void Remove(Type eventType, Delegate handler)
    {
        if (eventType == null || handler == null)
        {
            return;
        }

        lock (gate)
        {
            if (!subscribers.TryGetValue(eventType, out List<SubscriptionEntry> handlers))
            {
                return;
            }

            handlers.RemoveAll(entry => entry.Handler == handler);
            if (handlers.Count == 0)
            {
                subscribers.Remove(eventType);
            }
        }
    }

    private sealed class SubscriptionEntry
    {
        public SubscriptionEntry(Type eventType, Delegate handler, Action<object> invoker)
        {
            EventType = eventType;
            Handler = handler;
            Invoke = invoker;
        }

        public Type EventType { get; }
        public Delegate Handler { get; }
        public Action<object> Invoke { get; }
    }

    private sealed class EventSubscription : IDisposable
    {
        private readonly EventBus bus;
        private readonly Type eventType;
        private Delegate handler;

        public EventSubscription(EventBus bus, Type eventType, Delegate handler)
        {
            this.bus = bus;
            this.eventType = eventType;
            this.handler = handler;
        }

        public void Dispose()
        {
            if (handler == null)
            {
                return;
            }

            bus.Remove(eventType, handler);
            handler = null;
        }
    }

    private sealed class EmptySubscription : IDisposable
    {
        public static readonly EmptySubscription Instance = new();

        public void Dispose()
        {
        }
    }
}
