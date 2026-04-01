using UnityEngine;

namespace HPR
{
    [DisallowMultipleComponent]
    public class InventoryPickupInteractable : MonoBehaviour, IInteractable
    {
        [SerializeField] private ItemData itemData;
        [SerializeField] private int amount = 1;
        [SerializeField] private MonoBehaviour eventBusSourceBehaviour;

        private IEventBusSource eventBusSource;

        public InteractionType InteractionType => InteractionType.Loot;

        private void Awake()
        {
            eventBusSource = eventBusSourceBehaviour as IEventBusSource;
        }

        public void BindRuntimeEventBusSource(MonoBehaviour source)
        {
            eventBusSourceBehaviour = source;
            eventBusSource = source as IEventBusSource;
        }

        public string GetPrompt(IInteractionActor actor)
        {
            if (itemData == null)
            {
                return string.Empty;
            }

            return string.IsNullOrWhiteSpace(itemData.PickupPrompt)
                ? $"Pick up {itemData.DisplayName}"
                : itemData.PickupPrompt;
        }

        public void Interact(IInteractionActor actor)
        {
            if (actor?.InventoryService == null || itemData == null)
            {
                return;
            }

            if (!actor.InventoryService.AddItem(itemData, Mathf.Max(1, amount)))
            {
                return;
            }

            eventBusSource?.EventBus?.Publish(new ItemPickedEvent
            {
                PickerRoot = actor.ActorTransform != null ? actor.ActorTransform.gameObject : null,
                ItemId = itemData.Id,
                ItemDisplayName = itemData.DisplayName,
                LinkedWeaponId = itemData.LinkedWeaponId,
                PickupStatus = itemData.PickupStatus,
                ItemType = (int)itemData.ItemType,
                Amount = Mathf.Max(1, amount)
            });

            gameObject.SetActive(false);
        }
    }
}
