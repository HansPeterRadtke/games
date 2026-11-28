// PRIVATE native buyer fixture only. DO NOT include in buyer archive.
using UnityEngine;
public sealed class HprEventAuditFixtureReceiver : MonoBehaviour
{
    public void OnStep() { }
    private void OnHiddenValid() { }
    public void TakesFloat(float value) { }
    public void TakesEvent(AnimationEvent value) { }
#if UNITY_6000_6_OR_NEWER
    public void TakesEventInfo(AnimationEventInfo value) { }
#endif
    public void TwoArguments(int value, int another) { }
    public int ReturnsAValue() { return 42; }
}
