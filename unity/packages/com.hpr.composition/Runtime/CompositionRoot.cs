using System;
using System.Linq;

public sealed class CompositionRoot : IDisposable
{
    private bool initialized;

    public CompositionRoot()
    {
        Services = new ServiceRegistry();
    }

    public ServiceRegistry Services { get; }

    public void Initialize()
    {
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
        foreach (IUpdatableService service in Services.GetOrderedServices().OfType<IUpdatableService>())
        {
            service.Tick(deltaTime);
        }
    }

    public void Dispose()
    {
        foreach (object service in Services.GetOrderedServices().Reverse())
        {
            if (service is IDisposable disposable)
            {
                disposable.Dispose();
            }
        }
    }
}
