using System;

sealed class PingEvent
{
    public int Value { get; init; }
}

class BaseEvent
{
    public string Message { get; init; } = string.Empty;
}

sealed class DerivedEvent : BaseEvent
{
}

sealed class PingRecorder : IInitializable, IDisposable
{
    private IDisposable? subscription;

    public int Total { get; private set; }

    public void Initialize(IServiceResolver services)
    {
        subscription = services.Resolve<IEventBus>().Subscribe<PingEvent>(OnPing);
    }

    public void Dispose()
    {
        subscription?.Dispose();
        subscription = null;
    }

    private void OnPing(PingEvent payload)
    {
        Total += payload.Value;
    }
}

sealed class BaseEventRecorder : IInitializable, IDisposable
{
    private IDisposable? subscription;

    public int Count { get; private set; }

    public void Initialize(IServiceResolver services)
    {
        subscription = services.Resolve<IEventBus>().Subscribe<BaseEvent>(OnEvent);
    }

    public void Dispose()
    {
        subscription?.Dispose();
        subscription = null;
    }

    private void OnEvent(BaseEvent payload)
    {
        Count++;
    }
}

static class Program
{
    public static int Main()
    {
        var root = new CompositionRoot();
        var bus = new EventBus();
        var pingRecorder = new PingRecorder();
        var baseRecorder = new BaseEventRecorder();

        root.Services.Register<IEventBus>(bus);
        root.Services.Register(pingRecorder);
        root.Services.Register(baseRecorder);
        root.Initialize();

        bus.Publish(new PingEvent { Value = 7 });
        bus.Publish(new DerivedEvent { Message = "derived" });

        Expect(pingRecorder.Total == 7, "PingRecorder did not observe published event.");
        Expect(baseRecorder.Count == 1, "Base event subscriber did not observe derived event.");

        int transientCount = 0;
        IDisposable transient = bus.Subscribe<PingEvent>(_ => transientCount++);
        transient.Dispose();
        bus.Publish(new PingEvent { Value = 3 });
        Expect(transientCount == 0, "Disposed subscription still received events.");
        Expect(pingRecorder.Total == 10, "Persistent ping subscription broke after transient unsubscribe.");

        root.Dispose();
        bus.Publish(new PingEvent { Value = 5 });
        Expect(pingRecorder.Total == 10, "Composition disposal did not tear down subscriptions.");

        Console.WriteLine("phase1-headless-validation: OK");
        return 0;
    }

    private static void Expect(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
