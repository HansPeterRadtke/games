using UnityEngine;

namespace HPR.Foundation.Utils
{
    public static class GameObjectUtils
    {
        public static T GetOrAddComponent<T>(GameObject gameObject) where T : Component
        {
            if (gameObject.TryGetComponent<T>(out var component))
            {
                return component;
            }
            return gameObject.AddComponent<T>();
        }
    }
}
