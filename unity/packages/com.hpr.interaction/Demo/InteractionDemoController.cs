using System.Collections.Generic;
using UnityEngine;

public class InteractionDemoController : MonoBehaviour
{
    [SerializeField] private SimpleInteractionActor actor;
    [SerializeField] private InteractionSensor sensor;
    [SerializeField] private Camera actorCamera;
    [SerializeField] private InventoryPickupInteractable medkitPickup;
    [SerializeField] private InventoryPickupInteractable keyPickup;
    [SerializeField] private KeyDoorInteractable door;
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private List<ItemData> demoItems = new();

    private readonly List<string> logEntries = new();

    private void Awake()
    {
        if (actorCamera == null)
        {
            actorCamera = Camera.main;
        }

        sensor?.BindCamera(actorCamera);
    }

    private void Start()
    {
        if (actor?.InventoryService is InventoryComponent inventory)
        {
            inventory.ConfigureKnownItems(demoItems);
            inventory.ItemAdded += HandleItemAdded;
        }

        logEntries.Clear();
        logEntries.Add("Move with WASD. Press E to interact.");
    }

    public void ValidateDemo()
    {
        if (actor?.InventoryService is not InventoryComponent inventory || medkitPickup == null || keyPickup == null || door == null || demoItems.Count < 2)
        {
            throw new System.InvalidOperationException("Interaction demo is missing serialized references.");
        }

        inventory.ConfigureKnownItems(demoItems);
        ItemData keyItem = demoItems[0];
        ItemData medkitItem = demoItems[1];

        medkitPickup.Interact(actor);
        if (!inventory.HasItem(medkitItem.Id))
        {
            throw new System.InvalidOperationException("Interaction demo medkit pickup did not reach the inventory.");
        }

        bool openedWithoutKey = door.IsOpen;
        door.Interact(actor);
        if (door.IsOpen != openedWithoutKey)
        {
            throw new System.InvalidOperationException("Interaction demo door opened without the required key.");
        }

        keyPickup.Interact(actor);
        if (!inventory.HasItem(keyItem.Id))
        {
            throw new System.InvalidOperationException("Interaction demo key pickup did not reach the inventory.");
        }

        door.Interact(actor);
        if (!door.IsOpen)
        {
            throw new System.InvalidOperationException("Interaction demo door did not open after the key was collected.");
        }
    }

    private void OnDestroy()
    {
        if (actor?.InventoryService is InventoryComponent inventory)
        {
            inventory.ItemAdded -= HandleItemAdded;
        }
    }

    private void Update()
    {
        if (actor == null || sensor == null)
        {
            return;
        }

        Vector3 move = Vector3.zero;
        if (Input.GetKey(KeyCode.W)) move += Vector3.forward;
        if (Input.GetKey(KeyCode.S)) move += Vector3.back;
        if (Input.GetKey(KeyCode.A)) move += Vector3.left;
        if (Input.GetKey(KeyCode.D)) move += Vector3.right;
        actor.transform.position += move.normalized * (moveSpeed * Time.deltaTime);

        sensor.Probe(actor);
        if (Input.GetKeyDown(KeyCode.E) && sensor.TryInteract(actor))
        {
            logEntries.Insert(0, $"Interacted: {sensor.CurrentPrompt}");
            TrimLog();
        }
    }

    private void OnGUI()
    {
        GUILayout.BeginArea(new Rect(16f, 16f, 560f, 420f), GUI.skin.box);
        GUILayout.Label("HPR Interaction Demo");
        GUILayout.Label("Standalone demo for generic interaction contracts, pickups, and key doors.");
        GUILayout.Space(8f);
        GUILayout.Label($"Prompt: {(string.IsNullOrWhiteSpace(sensor?.CurrentPrompt) ? "<none>" : sensor.CurrentPrompt)}");

        if (actor?.InventoryService != null)
        {
            GUILayout.Space(8f);
            GUILayout.Label("Inventory:");
            foreach (ItemData item in demoItems)
            {
                if (item == null)
                {
                    continue;
                }

                GUILayout.Label($"- {item.DisplayName}: {actor.InventoryService.GetQuantity(item.Id)}");
            }
        }

        GUILayout.Space(12f);
        GUILayout.Label("Log:");
        foreach (string entry in logEntries)
        {
            GUILayout.Label($"- {entry}");
        }
        GUILayout.EndArea();
    }

    private void HandleItemAdded(ItemData itemData, int amount)
    {
        logEntries.Insert(0, $"Picked up {amount} x {itemData.DisplayName}");
        TrimLog();
    }

    private void TrimLog()
    {
        while (logEntries.Count > 10)
        {
            logEntries.RemoveAt(logEntries.Count - 1);
        }
    }
}
