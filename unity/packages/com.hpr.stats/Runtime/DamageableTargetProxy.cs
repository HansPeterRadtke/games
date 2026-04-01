using System.Linq;
using UnityEngine;

namespace HPR
{
    [DisallowMultipleComponent]
    public class DamageableTargetProxy : MonoBehaviour
    {
        [SerializeField] private MonoBehaviour damageableBehaviour;

        public IDamageable Resolve()
        {
            if (damageableBehaviour is IDamageable explicitTarget)
            {
                return explicitTarget;
            }

            return GetComponents<MonoBehaviour>().OfType<IDamageable>().FirstOrDefault();
        }

        public void Bind(MonoBehaviour source)
        {
            damageableBehaviour = source;
        }
    }
}
