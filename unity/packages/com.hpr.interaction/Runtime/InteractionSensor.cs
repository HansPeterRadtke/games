using System.Linq;
using UnityEngine;

[DisallowMultipleComponent]
public class InteractionSensor : MonoBehaviour
{
    [SerializeField] private Camera sourceCamera;
    [SerializeField] private float interactRange = 3.5f;
    [SerializeField] private LayerMask interactionMask = ~0;

    public IInteractable CurrentInteractable { get; private set; }
    public string CurrentPrompt { get; private set; }

    public void BindCamera(Camera camera)
    {
        sourceCamera = camera;
    }

    public void Probe(IInteractionActor actor)
    {
        CurrentInteractable = null;
        CurrentPrompt = string.Empty;

        if (sourceCamera == null || actor == null)
        {
            return;
        }

        if (!Physics.Raycast(sourceCamera.transform.position, sourceCamera.transform.forward, out RaycastHit hit, interactRange, interactionMask, QueryTriggerInteraction.Collide))
        {
            return;
        }

        CurrentInteractable = ResolveInteractable(hit.collider);
        CurrentPrompt = CurrentInteractable != null ? CurrentInteractable.GetPrompt(actor) : string.Empty;
    }

    public bool TryInteract(IInteractionActor actor)
    {
        Probe(actor);
        if (CurrentInteractable == null || actor == null)
        {
            return false;
        }

        CurrentInteractable.Interact(actor);
        Probe(actor);
        return true;
    }

    private static IInteractable ResolveInteractable(Collider collider)
    {
        if (collider == null)
        {
            return null;
        }

        IInteractable directTarget = collider.GetComponents<MonoBehaviour>().OfType<IInteractable>().FirstOrDefault();
        if (directTarget != null)
        {
            return directTarget;
        }

        InteractionTargetProxy proxy = collider.GetComponent<InteractionTargetProxy>();
        return proxy != null ? proxy.Resolve() : null;
    }
}
