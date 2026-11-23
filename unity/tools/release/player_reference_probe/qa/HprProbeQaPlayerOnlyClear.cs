using UnityEngine;

// PRIVATE intentional negative control only. Simulates one runtime-only field loss;
// it is NOT evidence of a Unity serialization bug or shipped with buyer code.
public sealed class HprProbeQaPlayerOnlyClear : MonoBehaviour
{
    public HprProbeQaItem source;
    private void Awake()
    {
        if(Application.isEditor || source==null)return;
        source.itemPrefab=null;
        Debug.Log("HPR_PRIVATE_INTENTIONAL_PLAYER_FIELD_CLEAR_DONE");
    }
}
