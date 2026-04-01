using UnityEngine;

namespace HPR
{
    [DisallowMultipleComponent]
    public class KeyDoorInteractable : MonoBehaviour, IInteractable
    {
        [SerializeField] private ItemData requiredKeyItem;
        [SerializeField] private Transform doorLeaf;
        [SerializeField] private float openAngle = 90f;
        [SerializeField] private float openSpeed = 120f;
        [SerializeField] private bool isOpen;
        [SerializeField] private string lockedPromptSuffix = " required";

        private Quaternion closedRotation;
        private Quaternion openedRotation;

        public InteractionType InteractionType => InteractionType.Open;
        public bool IsOpen => isOpen;

        private void Awake()
        {
            if (doorLeaf == null && transform.childCount > 0)
            {
                doorLeaf = transform.GetChild(0);
            }

            CacheRotations();
        }

        private void OnValidate()
        {
            CacheRotations();
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

        public string GetPrompt(IInteractionActor actor)
        {
            if (requiredKeyItem != null && (actor?.InventoryService == null || !actor.InventoryService.HasItem(requiredKeyItem.Id)))
            {
                return requiredKeyItem.DisplayName + lockedPromptSuffix;
            }

            return isOpen ? "Close door" : "Open door";
        }

        public void Interact(IInteractionActor actor)
        {
            if (requiredKeyItem != null && (actor?.InventoryService == null || !actor.InventoryService.HasItem(requiredKeyItem.Id)))
            {
                return;
            }

            isOpen = !isOpen;
        }

        private void CacheRotations()
        {
            if (doorLeaf == null)
            {
                return;
            }

            closedRotation = doorLeaf.localRotation;
            openedRotation = closedRotation * Quaternion.Euler(0f, openAngle, 0f);
        }
    }
}
