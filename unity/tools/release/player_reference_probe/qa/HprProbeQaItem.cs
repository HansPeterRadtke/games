using UnityEngine;

// PRIVATE author-owned sample content, never bundled with the buyer tool.
public sealed class HprProbeQaItem : ScriptableObject
{
    public GameObject itemPrefab;
    [SerializeField] private GameObject privatePrefab;
    public void SetPrivate(GameObject value){privatePrefab=value;}
    public GameObject PrivatePrefab=>privatePrefab;
}
