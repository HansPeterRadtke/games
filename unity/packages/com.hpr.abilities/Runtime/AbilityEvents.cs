using UnityEngine;

public sealed class AbilityUsedEvent
{
    public GameObject SourceRoot;
    public string AbilityId;
    public string AbilityDisplayName;
}

public sealed class AbilityEffectAppliedEvent
{
    public GameObject SourceRoot;
    public string AbilityId;
    public string EffectId;
    public AbilityEffectType EffectType;
    public float Value;
    public Vector3 Origin;
}

public sealed class AbilityStatusEvent
{
    public string Message;
}

public sealed class AbilityStateChangedEvent
{
    public GameObject SourceRoot;
}
