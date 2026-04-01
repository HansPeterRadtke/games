using UnityEngine;

namespace HPR
{
    public sealed class DamageEvent
    {
        public GameObject SourceRoot;
        public GameObject TargetRoot;
        public float Amount;
        public Vector3 HitPoint;
        public Vector3 HitDirection;
    }
}
