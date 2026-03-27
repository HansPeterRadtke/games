using UnityEngine;

public sealed class AbilityUsedEvent : GameEvent
{
    public GameObject SourceRoot;
    public string AbilityId;
    public string AbilityDisplayName;
}

public sealed class AbilityEffectAppliedEvent : GameEvent
{
    public GameObject SourceRoot;
    public string AbilityId;
    public string EffectId;
    public AbilityEffectType EffectType;
    public float Value;
    public Vector3 Origin;
}
