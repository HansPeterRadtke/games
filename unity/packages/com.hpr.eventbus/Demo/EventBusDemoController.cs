using System.Collections.Generic;
using UnityEngine;

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

    private void OnEnable()
    {
        if (eventManager == null)
        {
            return;
        }

        eventManager.Subscribe<DemoPingEvent>(HandlePing);
        eventManager.Subscribe<DemoStatusEvent>(HandleStatus);
    }

    private void OnDisable()
    {
        if (eventManager == null)
        {
            return;
        }

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
            eventManager?.Publish(new DemoPingEvent { Message = "Demo ping published" });
        }

        if (GUILayout.Button("Publish Status", GUILayout.Height(32f)))
        {
            eventManager?.Publish(new DemoStatusEvent { Message = "Status event published" });
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
}
