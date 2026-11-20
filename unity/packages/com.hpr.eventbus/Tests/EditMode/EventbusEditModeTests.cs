using NUnit.Framework;

namespace HPR
{
    public class EventBusEditModeTests
    {
        private class BaseEvent { }
        private sealed class DerivedEvent : BaseEvent { }

        [Test]
        public void Publish_ReachesBaseTypeSubscribers()
        {
            var bus = new EventBus();
            bool invoked = false;

            bus.Subscribe<BaseEvent>(_ => invoked = true);
            bus.Publish(new DerivedEvent());

            Assert.That(invoked, Is.True);
        }

        [Test]
        public void DuplicateHandlerSubscriptions_KeepIndependentLifetime()
        {
            using var bus = new EventBus();
            int calls = 0;
            System.Action<BaseEvent> callback = _ => calls++;
            using var first = bus.Subscribe(callback);
            using var second = bus.Subscribe(callback);

            bus.Publish(new BaseEvent());
            Assert.That(calls, Is.EqualTo(2), "Each subscription token represents one registration.");
            first.Dispose();
            first.Dispose();
            bus.Publish(new BaseEvent());
            Assert.That(calls, Is.EqualTo(3), "Disposing first token must not cancel the other.");
            second.Dispose();
            bus.Publish(new BaseEvent());
            Assert.That(calls, Is.EqualTo(3));
        }

        [Test]
        public void DelegateUnsubscribe_RemovesAllMatchingSubscriptions()
        {
            using var bus = new EventBus();
            int calls = 0;
            System.Action<BaseEvent> callback = _ => calls++;
            using var first = bus.Subscribe(callback);
            using var second = bus.Subscribe(callback);
            bus.Unsubscribe(callback);
            bus.Publish(new BaseEvent());
            Assert.That(calls, Is.EqualTo(0));
        }

        [Test]
        public void SubscriptionDispose_RemovesHandler()
        {
            var bus = new EventBus();
            int callCount = 0;
            var subscription = bus.Subscribe<BaseEvent>(_ => callCount++);

            subscription.Dispose();
            bus.Publish(new BaseEvent());

            Assert.That(callCount, Is.EqualTo(0));
        }
    }
}
