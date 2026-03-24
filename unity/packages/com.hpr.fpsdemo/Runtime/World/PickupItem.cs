using UnityEngine;

public class PickupItem : MonoBehaviour, IInteractable, ISaveableEntity
{
    private const string AutoVisualName = "__AutoVisual";

    [SerializeField] private string saveId;
    [SerializeField] private ItemData itemData;
    [SerializeField] private int amount = 1;

    public string SaveId => saveId;
    public ItemData ItemData => itemData;
    public int Amount => amount;

    private void Awake()
    {
        RefreshPresentation();
    }

#if UNITY_EDITOR
    private void OnValidate()
    {
        RefreshPresentation();
    }
#endif

    public void Configure(string id, ItemData data, int pickupAmount)
    {
        saveId = id;
        itemData = data;
        amount = pickupAmount;
        RefreshPresentation();
    }

    public string GetPrompt(IPlayerActor player)
    {
        return itemData != null && !string.IsNullOrWhiteSpace(itemData.PickupPrompt)
            ? itemData.PickupPrompt
            : "Collect item [E]";
    }

    public void Interact(IPlayerActor player)
    {
        if (itemData == null)
        {
            return;
        }

        if (!player.InventoryService.AddItem(itemData, amount))
        {
            return;
        }

        GameManager.Instance?.EventBus?.Publish(new ItemPickedEvent
        {
            PickerRoot = player.ActorTransform.gameObject,
            ItemData = itemData,
            Amount = amount
        });
        GameManager.Instance?.NotifyStatus(string.IsNullOrWhiteSpace(itemData.PickupStatus) ? $"Collected {itemData.DisplayName}" : itemData.PickupStatus);
        gameObject.SetActive(false);
    }

    public SaveEntityData CaptureState()
    {
        return new SaveEntityData
        {
            id = saveId,
            active = gameObject.activeSelf,
            position = new SerializableVector3(transform.position),
            rotation = new SerializableQuaternion(transform.rotation)
        };
    }

    public void RestoreState(SaveEntityData data)
    {
        gameObject.SetActive(data.active);
    }

    private void RefreshPresentation()
    {
        var autoVisual = transform.Find(AutoVisualName);
        if (autoVisual != null)
        {
            DestroyObject(autoVisual.gameObject);
        }

        var rootRenderer = GetComponent<Renderer>();
        if (rootRenderer != null)
        {
            rootRenderer.enabled = itemData == null || itemData.PickupPrefab == null;
        }

        if (itemData == null || itemData.PickupPrefab == null)
        {
            return;
        }

        var visual = Instantiate(itemData.PickupPrefab, transform);
        visual.name = AutoVisualName;
        visual.transform.localPosition = itemData.PickupVisualLocalPosition;
        visual.transform.localEulerAngles = itemData.PickupVisualLocalEuler;
        visual.transform.localScale = itemData.PickupVisualLocalScale;

        foreach (var behaviour in visual.GetComponentsInChildren<MonoBehaviour>(true))
        {
            DestroyObject(behaviour);
        }

        foreach (var rigidbody in visual.GetComponentsInChildren<Rigidbody>(true))
        {
            DestroyObject(rigidbody);
        }
    }

    private static void DestroyObject(Object target)
    {
        if (target == null)
        {
            return;
        }

        if (Application.isPlaying)
        {
            Destroy(target);
        }
        else
        {
            DestroyImmediate(target);
        }
    }
}
