using UnityEngine;

namespace HPR.Foundation.Utils
{
    public static class TransformResetExtensions
    {
        public static void ResetLocalPose(this Transform transform)
        {
            transform.localPosition = Vector3.zero;
            transform.localRotation = Quaternion.identity;
            transform.localScale = Vector3.one;
        }
    }
}
