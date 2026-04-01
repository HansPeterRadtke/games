#nullable enable
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace HPR
{
    public interface IService
    {
    }

    public interface IServiceResolver
    {
        TService Resolve<TService>() where TService : class;
        bool TryResolve<TService>([NotNullWhen(true)] out TService? service) where TService : class;
        IReadOnlyList<TService> ResolveAll<TService>() where TService : class;
    }

    public interface IServiceRegistry : IServiceResolver
    {
        void Register<TService>(TService service) where TService : class;
        void Register(Type serviceType, object service);
        bool IsRegistered<TService>() where TService : class;
    }

    public interface IInitializable : IService
    {
        void Initialize(IServiceResolver services);
    }

    public interface IUpdatableService : IService
    {
        void Tick(float deltaTime);
    }

    public static class ServiceResolverExtensions
    {
        public static T? ResolveOptional<T>(this IServiceResolver services) where T : class
        {
            if (services == null)
            {
                return null;
            }

            services.TryResolve(out T? service);
            return service;
        }
    }
}
