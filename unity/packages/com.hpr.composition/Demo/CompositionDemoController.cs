using UnityEngine;

namespace HPR
{
    public class CompositionDemoController : MonoBehaviour
    {
        private CompositionRoot compositionRoot;
        private CounterService counterService;
        private SummaryService summaryService;

        public bool IsInitialized => compositionRoot != null;
        public int TickCount => counterService != null ? counterService.TickCount : 0;
        public string Summary => summaryService != null ? summaryService.Message : "Not initialized";

        private void Start()
        {
            InitializeDemo();
        }

        private void OnDestroy()
        {
            compositionRoot?.Dispose();
            compositionRoot = null;
            counterService = null;
            summaryService = null;
        }

        public void InitializeDemo()
        {
            compositionRoot?.Dispose();

            compositionRoot = new CompositionRoot();
            counterService = new CounterService();
            summaryService = new SummaryService();

            compositionRoot.Services.Register(counterService);
            compositionRoot.Services.Register(summaryService);
            compositionRoot.Initialize();
        }

        public void RunStep()
        {
            if (compositionRoot == null)
            {
                InitializeDemo();
            }

            compositionRoot.Tick(1f);
        }

        public void ValidateDemo()
        {
            InitializeDemo();
            RunStep();
            RunStep();

            if (TickCount != 2)
            {
                throw new System.InvalidOperationException($"Expected two ticks, got {TickCount}.");
            }

            if (!Summary.Contains("initialized"))
            {
                throw new System.InvalidOperationException("Summary service did not resolve dependencies during initialization.");
            }
        }

        private void OnGUI()
        {
            GUILayout.BeginArea(new Rect(16f, 16f, 520f, 260f), GUI.skin.box);
            GUILayout.Label("HPR Composition Demo");
            GUILayout.Label("This sample shows explicit registration, initialization, and update ticks.");
            GUILayout.Space(8f);

            if (GUILayout.Button("Initialize Composition", GUILayout.Height(32f)))
            {
                InitializeDemo();
            }

            if (GUILayout.Button("Run Tick", GUILayout.Height(32f)))
            {
                RunStep();
            }

            GUILayout.Space(8f);
            GUILayout.Label($"Initialized: {IsInitialized}");
            GUILayout.Label($"Tick count: {TickCount}");
            GUILayout.Label($"Summary: {Summary}");
            GUILayout.EndArea();
        }

        private sealed class CounterService : IInitializable, IUpdatableService
        {
            public int TickCount { get; private set; }
            public bool Initialized { get; private set; }

            public void Initialize(IServiceResolver services)
            {
                Initialized = true;
                TickCount = 0;
            }

            public void Tick(float deltaTime)
            {
                TickCount++;
            }
        }

        private sealed class SummaryService : IInitializable
        {
            public string Message { get; private set; } = "Not initialized";

            public void Initialize(IServiceResolver services)
            {
                CounterService counter = services.Resolve<CounterService>();
                Message = counter.Initialized ? "Counter service initialized and resolved." : "Counter service missing.";
            }
        }
    }
}
