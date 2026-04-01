using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    public sealed class DemoPingEvent
    {
        public string Message;
    }

    public sealed class DemoStatusEvent
    {
        public string Message;
    }

    public class EventBusDemoController : MonoBehaviour
    {
        [SerializeField] private EventManager eventManager;

        private readonly List<string> entries = new();
        private int pingCount;
        private int statusCount;
        private bool subscriptionsActive;

        public int PingCount => pingCount;
        public int StatusCount => statusCount;
        public IReadOnlyList<string> Entries => entries;

        private void OnEnable()
        {
            EnsureSubscriptions();
        }

        private void OnDisable()
        {
            RemoveSubscriptions();
        }

        public void EnsureSubscriptions()
        {
            if (eventManager == null || subscriptionsActive)
            {
                return;
            }

            subscriptionsActive = true;
            eventManager.Subscribe<DemoPingEvent>(HandlePing);
            eventManager.Subscribe<DemoStatusEvent>(HandleStatus);
        }

        public void RemoveSubscriptions()
        {
            if (eventManager == null || !subscriptionsActive)
            {
                return;
            }

            subscriptionsActive = false;
            eventManager.Unsubscribe<DemoPingEvent>(HandlePing);
            eventManager.Unsubscribe<DemoStatusEvent>(HandleStatus);
        }

        private void HandlePing(DemoPingEvent demoEvent)
        {
            pingCount++;
            entries.Insert(0, $"Ping {pingCount}: {demoEvent.Message}");
            TrimEntries();
        }

        private void HandleStatus(DemoStatusEvent demoEvent)
        {
            statusCount++;
            entries.Insert(0, $"Status {statusCount}: {demoEvent.Message}");
            TrimEntries();
        }

        private void OnGUI()
        {
            GUILayout.BeginArea(new Rect(16f, 16f, 460f, 320f), GUI.skin.box);
            GUILayout.Label("HPR Event Bus Demo");
            GUILayout.Label("This scene is standalone. It publishes two event types and renders the subscription results.");
            GUILayout.Space(8f);

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Publish Ping", GUILayout.Height(32f)))
            {
                PublishPing();
            }

            if (GUILayout.Button("Publish Status", GUILayout.Height(32f)))
            {
                PublishStatus();
            }
            GUILayout.EndHorizontal();

            GUILayout.Space(10f);
            GUILayout.Label($"Observed ping events: {pingCount}");
            GUILayout.Label($"Observed status events: {statusCount}");
            GUILayout.Space(8f);
            GUILayout.Label("Latest events:");
            foreach (var entry in entries)
            {
                GUILayout.Label($"- {entry}");
            }

            GUILayout.EndArea();
        }

        private void TrimEntries()
        {
            while (entries.Count > 8)
            {
                entries.RemoveAt(entries.Count - 1);
            }
        }

        public void PublishPing()
        {
            eventManager?.Publish(new DemoPingEvent { Message = "Demo ping published" });
        }

        public void PublishStatus()
        {
            eventManager?.Publish(new DemoStatusEvent { Message = "Status event published" });
        }
    }
}
