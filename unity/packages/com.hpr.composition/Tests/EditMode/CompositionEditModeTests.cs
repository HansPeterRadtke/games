using NUnit.Framework;

namespace HPR
{
    public class CompositionEditModeTests
    {
        private sealed class CounterService : IInitializable, IUpdatableService
        {
            public bool Initialized { get; private set; }
            public float LastDeltaTime { get; private set; }

            public void Initialize(IServiceResolver services)
            {
                Initialized = services.Resolve<CounterService>() == this;
            }

            public void Tick(float deltaTime)
            {
                LastDeltaTime = deltaTime;
            }
        }

        [Test]
        public void CompositionRoot_InitializesAndTicksRegisteredServices()
        {
            var root = new CompositionRoot();
            var service = new CounterService();
            root.Services.Register(service);

            root.Initialize();
            root.Tick(0.5f);

            Assert.That(service.Initialized, Is.True);
            Assert.That(service.LastDeltaTime, Is.EqualTo(0.5f));
        }

        [Test]
        public void ResolveOptional_ReturnsNullForMissingService()
        {
            var services = new ServiceRegistry();
            Assert.That(services.ResolveOptional<CounterService>(), Is.Null);
        }
    }
}
