using System.Linq;
using UnityEngine;

[DisallowMultipleComponent]
public class InteractionTargetProxy : MonoBehaviour
{
    [SerializeField] private MonoBehaviour interactableBehaviour;

    public IInteractable Resolve()
    {
        if (interactableBehaviour is IInteractable explicitTarget)
        {
            return explicitTarget;
        }

        return GetComponents<MonoBehaviour>().OfType<IInteractable>().FirstOrDefault();
    }

    public void Bind(MonoBehaviour source)
    {
        interactableBehaviour = source;
    }
}
