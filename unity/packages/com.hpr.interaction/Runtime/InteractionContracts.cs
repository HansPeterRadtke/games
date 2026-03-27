using UnityEngine;

public enum InteractionType
{
    Activate,
    Open,
    Loot,
    Talk
}

public interface IInteractionActor
{
    Transform ActorTransform { get; }
    IInventoryService InventoryService { get; }
}

public interface IInteractable
{
    InteractionType InteractionType { get; }
    string GetPrompt(IInteractionActor actor);
    void Interact(IInteractionActor actor);
}
