using System.Linq;
using UnityEngine;

namespace HPR
{
    public class PickupItem : MonoBehaviour, IInteractable, ISaveableEntity
    {
        private const string AutoVisualName = "__AutoVisual";

        [SerializeField] private string saveId;
        [SerializeField] private ItemData itemData;
        [SerializeField] private int amount = 1;
        [SerializeField] private MonoBehaviour servicesBehaviour;

        private IEventBusSource eventBusSource;
        private IStatusMessageSink statusSink;

        public string SaveId => saveId;
        public ItemData ItemData => itemData;
        public int Amount => amount;
        public InteractionType InteractionType => InteractionType.Loot;

        private void Awake()
        {
            servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IEventBusSource || component is IStatusMessageSink);
            eventBusSource = servicesBehaviour as IEventBusSource;
            statusSink = servicesBehaviour as IStatusMessageSink;
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

        public void BindRuntimeServices(MonoBehaviour services)
        {
            servicesBehaviour = services;
            eventBusSource = servicesBehaviour as IEventBusSource;
            statusSink = servicesBehaviour as IStatusMessageSink;
        }

        public string GetPrompt(IInteractionActor player)
        {
            return itemData != null && !string.IsNullOrWhiteSpace(itemData.PickupPrompt)
                ? itemData.PickupPrompt
                : "Collect item [E]";
        }

        public void Interact(IInteractionActor player)
        {
            if (itemData == null || player?.InventoryService == null)
            {
                return;
            }

            if (!player.InventoryService.AddItem(itemData, amount))
            {
                return;
            }

            eventBusSource?.EventBus?.Publish(new ItemPickedEvent
            {
                PickerRoot = player.ActorTransform.gameObject,
                ItemId = itemData.Id,
                ItemDisplayName = itemData.DisplayName,
                LinkedWeaponId = itemData.LinkedWeaponId,
                PickupStatus = itemData.PickupStatus,
                ItemType = (int)itemData.ItemType,
                Amount = amount
            });
            statusSink?.NotifyStatus(string.IsNullOrWhiteSpace(itemData.PickupStatus) ? $"Collected {itemData.DisplayName}" : itemData.PickupStatus);
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
                DestroyUnityObject(autoVisual.gameObject);
            }

            var rootRenderer = GetComponent<Renderer>();
            bool shouldSpawnRuntimeVisual = Application.isPlaying && itemData != null && itemData.PickupPrefab != null;
            if (rootRenderer != null)
            {
                rootRenderer.enabled = !shouldSpawnRuntimeVisual;
            }

            if (!shouldSpawnRuntimeVisual)
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
                DestroyUnityObject(behaviour);
            }

            foreach (var rigidbody in visual.GetComponentsInChildren<Rigidbody>(true))
            {
                DestroyUnityObject(rigidbody);
            }
        }

        private static void DestroyUnityObject(Object target)
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
}
