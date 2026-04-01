using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class WorldEditModeTests
    {
        [Test]
        public void AssetRegistry_ResolvesEntriesById()
        {
            var registry = ScriptableObject.CreateInstance<AssetRegistry>();
            var metadata = ScriptableObject.CreateInstance<AssetMetadata>();
            try
            {
                metadata.AssetId = "crate";
                metadata.DisplayName = "Crate";
                registry.SetEntries(new[] { metadata });

                Assert.That(registry.Get("crate"), Is.SameAs(metadata));
                Assert.That(registry.TryGet("missing", out _), Is.False);
            }
            finally
            {
                Object.DestroyImmediate(metadata);
                Object.DestroyImmediate(registry);
            }
        }
    }
}
