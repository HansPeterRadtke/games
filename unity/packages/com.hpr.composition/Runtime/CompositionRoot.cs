using System;
using System.Linq;

namespace HPR
{
    public sealed class CompositionRoot : IDisposable
    {
        private bool initialized;
        private bool disposed;

        public CompositionRoot()
        {
            Services = new ServiceRegistry();
        }

        public ServiceRegistry Services { get; }

        public void Initialize()
        {
            ThrowIfDisposed();
            if (initialized)
            {
                return;
            }

            foreach (IInitializable service in Services.GetOrderedServices().OfType<IInitializable>())
            {
                service.Initialize(Services);
            }

            initialized = true;
        }

        public void Tick(float deltaTime)
        {
            ThrowIfDisposed();
            if (float.IsNaN(deltaTime) || float.IsInfinity(deltaTime) || deltaTime < 0f)
                throw new ArgumentOutOfRangeException(nameof(deltaTime));
            foreach (IUpdatableService service in Services.GetOrderedServices().OfType<IUpdatableService>())
            {
                service.Tick(deltaTime);
            }
        }

        private void ThrowIfDisposed()
        {
            if (disposed)
                throw new ObjectDisposedException(nameof(CompositionRoot));
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            foreach (object service in Services.GetOrderedServices().Reverse())
            {
                if (service is IDisposable disposable)
                {
                    disposable.Dispose();
                }
            }
        }
    }
}
