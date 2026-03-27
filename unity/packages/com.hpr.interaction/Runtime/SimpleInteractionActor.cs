using UnityEngine;

[DisallowMultipleComponent]
public class SimpleInteractionActor : MonoBehaviour, IInteractionActor
{
    [SerializeField] private InventoryComponent inventory;

    public Transform ActorTransform => transform;
    public IInventoryService InventoryService => inventory;

    private void Awake()
    {
        if (inventory == null)
        {
            inventory = GetComponent<InventoryComponent>();
        }
    }
}
