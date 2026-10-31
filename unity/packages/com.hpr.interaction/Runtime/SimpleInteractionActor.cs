using UnityEngine;

namespace HPR
{
    [DisallowMultipleComponent]
    public class SimpleInteractionActor : MonoBehaviour, IInteractionActor
    {
        [SerializeField] private InventoryComponent inventory;

        public Transform ActorTransform => transform;
        public IInventoryService InventoryService => inventory;

        public void BindInventory(InventoryComponent source)
        {
            inventory = source;
        }

        private void Awake()
        {
            if (inventory == null)
            {
                inventory = GetComponent<InventoryComponent>();
            }
        }
    }
}
