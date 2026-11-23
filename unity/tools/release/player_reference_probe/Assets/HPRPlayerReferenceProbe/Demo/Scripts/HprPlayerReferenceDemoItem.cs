using UnityEngine;

// Original first-party sample data: no game mechanics and no runtime auto-loader.
namespace HPR.PlayerReferenceProbe.Demo
{
    [CreateAssetMenu(fileName="New HPR Demo Item",menuName="HPR/Player Reference Probe/Sample Item")]
    public sealed class HprPlayerReferenceDemoItem : ScriptableObject
    {
        public GameObject itemPrefab;
        [Tooltip("Demonstration information; deliberately not inspected by the probe.")]
        public string label;
    }
}
