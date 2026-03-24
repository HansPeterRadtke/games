using System;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(menuName = "FPS Demo/Data/Asset Registry", fileName = "AssetRegistry")]
public class AssetRegistry : ScriptableObject
{
    [SerializeField] private List<AssetMetadata> entries = new List<AssetMetadata>();

    private readonly Dictionary<string, AssetMetadata> lookup = new Dictionary<string, AssetMetadata>(StringComparer.Ordinal);
    private bool isBuilt;

    public IReadOnlyList<AssetMetadata> Entries => entries;

    public void SetEntries(IEnumerable<AssetMetadata> metadata)
    {
        entries = metadata != null ? new List<AssetMetadata>(metadata) : new List<AssetMetadata>();
        isBuilt = false;
    }

    public bool TryGet(string assetId, out AssetMetadata metadata)
    {
        metadata = null;
        EnsureLookup();
        return !string.IsNullOrWhiteSpace(assetId) && lookup.TryGetValue(assetId, out metadata);
    }

    public AssetMetadata Get(string assetId)
    {
        TryGet(assetId, out AssetMetadata metadata);
        return metadata;
    }

    public void EnsureLookup()
    {
        if (isBuilt)
        {
            return;
        }

        lookup.Clear();
        foreach (AssetMetadata metadata in entries)
        {
            if (metadata == null || string.IsNullOrWhiteSpace(metadata.AssetId))
            {
                continue;
            }

            lookup[metadata.AssetId] = metadata;
        }

        isBuilt = true;
    }

#if UNITY_EDITOR
    private void OnValidate()
    {
        isBuilt = false;
        EnsureLookup();
    }
#endif
}
