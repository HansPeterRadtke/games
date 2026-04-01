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
