using System.Collections;
using UnityEngine;

// PRIVATE original QA fixture; deliberately changes one field after multiple Player frames.
// Never bundle in the customer package or claim a Unity engine bug from this mutation.
public sealed class HprProbeQaManualTrigger : MonoBehaviour
{
    public HPR.PlayerReferenceProbe.HprPlayerReferenceProbe probe;
    public HprProbeQaItem source;
    private IEnumerator Start()
    {
        if(Application.isEditor)yield break;
        for(var frame=0;frame<6;frame++)yield return null;
        if(probe==null || source==null || source.itemPrefab==null || !probe.manualOnly)
        {
            Debug.LogError("HPR_PRIVATE_MANUAL_LATE_QA_FIXTURE_INVALID");
            yield break;
        }
        source.itemPrefab=null;
        Debug.Log("HPR_PRIVATE_INTENTIONAL_LATE_PLAYER_FIELD_CLEAR_DONE");
        bool first=probe.CaptureNow();
        if(!first)Debug.LogError("HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_FAILED");
        else Debug.Log("HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_SUCCESS");
        bool second=probe.CaptureNow();
        if(second)Debug.LogError("HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_FAILURE");
        else Debug.Log("HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_ENFORCED");
    }
}
