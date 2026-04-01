using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    public class WorldDemoController : MonoBehaviour
    {
        [SerializeField] private AssetRegistry registry;
        [SerializeField] private List<AssetMetadata> expectedEntries = new();
        [SerializeField] private List<Transform> previews = new();

        public void ValidateDemo()
        {
            if (registry == null)
            {
                throw new System.InvalidOperationException("World demo registry is missing.");
            }

            if (expectedEntries.Count < 2)
            {
                throw new System.InvalidOperationException("World demo requires at least two metadata assets.");
            }

            if (expectedEntries.Count != previews.Count)
            {
                throw new System.InvalidOperationException("World demo preview count does not match metadata count.");
            }

            foreach (AssetMetadata entry in expectedEntries)
            {
                if (entry == null || string.IsNullOrWhiteSpace(entry.AssetId))
                {
                    throw new System.InvalidOperationException("World demo contains a missing metadata asset or asset id.");
                }

                AssetMetadata resolved = registry.Get(entry.AssetId);
                if (resolved != entry)
                {
                    throw new System.InvalidOperationException($"World registry failed to resolve '{entry.AssetId}'.");
                }

                if (entry.DefaultScale == Vector3.zero)
                {
                    throw new System.InvalidOperationException($"Metadata '{entry.DisplayName}' has an invalid zero scale.");
                }
            }

            Debug.Log($"WorldPackageValidator: validated {expectedEntries.Count} asset metadata entries.");
        }
    }
}
