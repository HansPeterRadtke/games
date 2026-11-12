using HPR;
using UnityEngine;

namespace HPR.Qa.RunnerDependency
{
    [RequireComponent(typeof(BoxCollider), typeof(Rigidbody), typeof(AbilityRunnerComponent))]
    public abstract class BuyerCastingBase : MonoBehaviour { }

    public sealed class BuyerCastingController : BuyerCastingBase { }
}
