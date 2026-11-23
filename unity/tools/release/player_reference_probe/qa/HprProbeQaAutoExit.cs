using System.Collections;
using UnityEngine;

// PRIVATE disposable Player smoke test: never included in the retail candidate.
public sealed class HprProbeQaAutoExit : MonoBehaviour
{
    private IEnumerator Start()
    {
        for(var i=0;i<40;i++)yield return null;
        Debug.Log("HPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS");
        Application.Quit(0);
    }
}
