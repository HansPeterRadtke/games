#nullable enable
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace HPR
{
    public sealed class ServiceRegistry : IServiceRegistry
    {
        private readonly Dictionary<Type, object> services = new();
        private readonly List<object> serviceOrder = new();

        public void Register<TService>(TService service) where TService : class
        {
            Register(typeof(TService), service);
        }

        public void Register(Type serviceType, object service)
        {
            if (serviceType == null)
            {
                throw new ArgumentNullException(nameof(serviceType));
            }

            if (service == null)
            {
                throw new ArgumentNullException(nameof(service));
            }

            if (!serviceType.IsInstanceOfType(service))
            {
                throw new ArgumentException($"Service does not implement '{serviceType.FullName}'.", nameof(service));
            }

            services.TryGetValue(serviceType, out object? previous);
            services[serviceType] = service;

            // The old instance can still be registered under another interface.
            // Do not orphan it in ResolveAll/initialize/tick/dispose ordering after
            // its final registration is replaced, and never dispose caller-owned
            // services as a side effect of changing the registry.
            if (previous != null && !ReferenceEquals(previous, service) &&
                !services.Values.Any(value => ReferenceEquals(value, previous)))
            {
                serviceOrder.RemoveAll(value => ReferenceEquals(value, previous));
            }
            if (!serviceOrder.Any(value => ReferenceEquals(value, service)))
                serviceOrder.Add(service);
        }

        public TService Resolve<TService>() where TService : class
        {
            if (TryResolve(out TService? service))
            {
                return service;
            }

            throw new InvalidOperationException($"Service '{typeof(TService).FullName}' is not registered.");
        }

        public bool TryResolve<TService>([NotNullWhen(true)] out TService? service) where TService : class
        {
            if (services.TryGetValue(typeof(TService), out object? instance) && instance is TService typed)
            {
                service = typed;
                return true;
            }

            service = serviceOrder.OfType<TService>().FirstOrDefault();
            return service != null;
        }

        public IReadOnlyList<TService> ResolveAll<TService>() where TService : class
        {
            return serviceOrder.OfType<TService>().ToList();
        }

        public bool IsRegistered<TService>() where TService : class
        {
            return services.ContainsKey(typeof(TService)) || serviceOrder.OfType<TService>().Any();
        }

        internal IReadOnlyList<object> GetOrderedServices()
        {
            return serviceOrder;
        }
    }
}
