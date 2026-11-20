using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.ExceptionServices;

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

        /// <summary>Disposes each service once in reverse registration order. A single
        /// failure is rethrown after cleanup. Multiple failures are reported together.</summary>
        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            List<Exception> failures = null;
            foreach (object service in Services.GetOrderedServices().Reverse())
            {
                if (!(service is IDisposable disposable)) continue;
                try
                {
                    disposable.Dispose();
                }
                catch (Exception error)
                {
                    (failures ??= new List<Exception>()).Add(error);
                }
            }

            if (failures == null) return;
            if (failures.Count == 1)
                ExceptionDispatchInfo.Capture(failures[0]).Throw();
            throw new AggregateException("Multiple services failed during disposal.", failures);
        }
    }
}
