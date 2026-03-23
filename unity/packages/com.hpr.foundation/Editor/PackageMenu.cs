using UnityEditor;
using UnityEngine;

namespace HPR.Foundation.Editor
{
    public static class PackageMenu
    {
        [MenuItem("HPR/Foundation/Ping")]
        public static void Ping()
        {
            Debug.Log("HPR Foundation package loaded");
        }
    }
}
