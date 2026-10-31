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

        private interface IReplaceableService { }
        private sealed class ReplacementService : IReplaceableService { }

        [Test]
        public void RegisterReplacement_DoesNotRetainStaleServiceInResolutionOrder()
        {
            var services = new ServiceRegistry();
            var previous = new ReplacementService();
            var replacement = new ReplacementService();
            services.Register<IReplaceableService>(previous);
            services.Register<IReplaceableService>(replacement);
            Assert.That(services.Resolve<IReplaceableService>(), Is.SameAs(replacement));
            Assert.That(services.ResolveAll<IReplaceableService>(), Is.EquivalentTo(new[] { replacement }));
        }

        [Test]
        public void CompositionRoot_Dispose_IsIdempotent()
        {
            var root = new CompositionRoot();
            var service = new DisposableService();
            root.Services.Register(service);
            root.Dispose();
            root.Dispose();
            Assert.That(service.DisposeCount, Is.EqualTo(1));
        }

        private sealed class DisposableService : System.IDisposable
        {
            public int DisposeCount;
            public void Dispose() { DisposeCount++; }
        }

        [Test]
        public void ResolveOptional_ReturnsNullForMissingService()
        {
            var services = new ServiceRegistry();
            Assert.That(services.ResolveOptional<CounterService>(), Is.Null);
        }
    }
}
