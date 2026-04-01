using System.Linq;
using UnityEngine;

namespace HPR
{
    public class DoorController : MonoBehaviour, IInteractable, ISaveableEntity
    {
        [SerializeField] private string saveId;
        [SerializeField] private ItemData requiredKeyItem;
        [SerializeField] private float openAngle = 92f;
        [SerializeField] private float openSpeed = 140f;
        [SerializeField] private Transform doorLeaf;
        [SerializeField] private bool isOpen;
        [SerializeField] private MonoBehaviour servicesBehaviour;

        private Quaternion closedRotation;
        private Quaternion openedRotation;
        private IStatusMessageSink statusSink;

        public string SaveId => saveId;
        public InteractionType InteractionType => InteractionType.Open;

        private void Awake()
        {
            if (doorLeaf == null)
            {
                doorLeaf = transform.GetChild(0);
            }
            servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IStatusMessageSink);
            statusSink = servicesBehaviour as IStatusMessageSink;
            closedRotation = doorLeaf.localRotation;
            openedRotation = closedRotation * Quaternion.Euler(0f, openAngle, 0f);
        }

        private void Update()
        {
            if (doorLeaf == null)
            {
                return;
            }

            Quaternion target = isOpen ? openedRotation : closedRotation;
            doorLeaf.localRotation = Quaternion.RotateTowards(doorLeaf.localRotation, target, openSpeed * Time.deltaTime);
        }

        public void Configure(string id, Transform leaf, ItemData keyItem)
        {
            saveId = id;
            doorLeaf = leaf;
            requiredKeyItem = keyItem;
            closedRotation = doorLeaf.localRotation;
            openedRotation = closedRotation * Quaternion.Euler(0f, openAngle, 0f);
        }

        public void BindRuntimeServices(MonoBehaviour services)
        {
            servicesBehaviour = services;
            statusSink = servicesBehaviour as IStatusMessageSink;
        }

        public string GetPrompt(IInteractionActor player)
        {
            if (requiredKeyItem != null && (player?.InventoryService == null || !player.InventoryService.HasItem(requiredKeyItem.Id)))
            {
                return $"{requiredKeyItem.DisplayName} required";
            }

            return isOpen ? "Close door [E]" : "Open door [E]";
        }

        public void Interact(IInteractionActor player)
        {
            if (requiredKeyItem != null && (player?.InventoryService == null || !player.InventoryService.HasItem(requiredKeyItem.Id)))
            {
                statusSink?.NotifyStatus($"{requiredKeyItem.DisplayName} required");
                return;
            }

            isOpen = !isOpen;
            statusSink?.NotifyStatus(isOpen ? "Door opening" : "Door closing");
        }

        public SaveEntityData CaptureState()
        {
            return new SaveEntityData
            {
                id = saveId,
                active = gameObject.activeSelf,
                boolValue = isOpen,
                position = new SerializableVector3(transform.position),
                rotation = new SerializableQuaternion(transform.rotation)
            };
        }

        public void RestoreState(SaveEntityData data)
        {
            gameObject.SetActive(data.active);
            isOpen = data.boolValue;
            if (doorLeaf != null)
            {
                doorLeaf.localRotation = isOpen ? openedRotation : closedRotation;
            }
        }
    }
}
