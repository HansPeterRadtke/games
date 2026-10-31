#nullable enable
using System;
using System.Collections.Generic;

namespace HPR
{
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
                if (!subscribers.TryGetValue(entry.EventType, out List<SubscriptionEntry>? handlers))
                {
                    handlers = new List<SubscriptionEntry>();
                    subscribers[entry.EventType] = handlers;
                }

                handlers.Add(entry);
            }

            return new EventSubscription(this, entry);
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
                if (!subscribers.TryGetValue(eventType, out List<SubscriptionEntry>? handlers))
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

        private void RemoveEntry(SubscriptionEntry registration)
        {
            lock (gate)
            {
                if (!subscribers.TryGetValue(registration.EventType, out List<SubscriptionEntry>? entries))
                    return;
                entries.Remove(registration); // Identity, never the shared callback delegate.
                if (entries.Count == 0)
                    subscribers.Remove(registration.EventType);
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

        /// <summary>
        /// One lifetime token for one registration. Dispose is idempotent, even
        /// when called by multiple threads or after the parent EventBus is cleared.
        /// A Publish already in progress may still invoke its captured callbacks.
        /// </summary>
        private sealed class EventSubscription : IDisposable
        {
            private EventBus? bus;
            private readonly SubscriptionEntry registration;

            public EventSubscription(EventBus bus, SubscriptionEntry registration)
            {
                this.bus = bus;
                this.registration = registration;
            }

            public void Dispose()
            {
                EventBus? owner = System.Threading.Interlocked.Exchange(ref bus, null);
                owner?.RemoveEntry(registration);
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
}
