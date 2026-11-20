using System;
using System.Collections.Generic;
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

        private sealed class CleanupService : IDisposable, IService
        {
            private readonly Action cleanup;

            public CleanupService(Action cleanup) { this.cleanup = cleanup; }
            public void Dispose() { cleanup(); }
        }

        [TestCase(false)]
        [TestCase(true)]
        public void Dispose_ContinuesInReverseOrderAndReportsOriginalFailures(bool failTwice)
        {
            var root = new CompositionRoot();
            var released = new List<string>();
            var saveFailure = new InvalidOperationException("Save failed");
            var controllerFailure = new InvalidOperationException("Controller failed");
            root.Services.Register<IService>(new CleanupService(() =>
            {
                released.Add("controller");
                if (failTwice) throw controllerFailure;
            }));
            root.Services.Register<CleanupService>(new CleanupService(() => released.Add("input")));
            root.Services.Register<IDisposable>(new CleanupService(() =>
            {
                released.Add("save");
                throw saveFailure;
            }));

            if (failTwice)
            {
                var error = Assert.Throws<AggregateException>(() => root.Dispose());
                Assert.That(error.InnerExceptions, Is.EqualTo(new[] { saveFailure, controllerFailure }));
            }
            else
            {
                var error = Assert.Throws<InvalidOperationException>(() => root.Dispose());
                Assert.That(error, Is.SameAs(saveFailure));
            }

            root.Dispose();
            Assert.That(released, Is.EqualTo(new[] { "save", "input", "controller" }));
        }

        [Test]
        public void ResolveOptional_ReturnsNullForMissingService()
        {
            var services = new ServiceRegistry();
            Assert.That(services.ResolveOptional<CounterService>(), Is.Null);
        }
    }
}
