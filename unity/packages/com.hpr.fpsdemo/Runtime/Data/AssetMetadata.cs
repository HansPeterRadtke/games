using UnityEngine;

[CreateAssetMenu(menuName = "FPS Demo/Data/Asset Metadata", fileName = "AssetMetadata")]
public class AssetMetadata : ScriptableObject
{
    public string AssetId;
    public string DisplayName;
    public string PrefabAssetPath;
    public AssetType AssetType = AssetType.Prop;
    public Vector3 DefaultScale = Vector3.one;
    public MaterialType MaterialType = MaterialType.Unknown;
}
