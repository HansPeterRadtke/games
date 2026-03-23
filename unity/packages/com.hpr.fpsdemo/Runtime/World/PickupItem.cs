using UnityEngine;

public class PickupItem : MonoBehaviour, IInteractable, ISaveableEntity
{
    [SerializeField] private string saveId;
    [SerializeField] private ItemData itemData;
    [SerializeField] private int amount = 1;

    public string SaveId => saveId;

    public void Configure(string id, ItemData data, int pickupAmount)
    {
        saveId = id;
        itemData = data;
        amount = pickupAmount;
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
}
