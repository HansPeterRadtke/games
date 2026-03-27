using UnityEngine;

public abstract class GameEvent
{
    public float Timestamp { get; } = Time.time;
}

public sealed class DamageEvent : GameEvent
{
    public GameObject SourceRoot;
    public GameObject TargetRoot;
    public float Amount;
    public Vector3 HitPoint;
    public Vector3 HitDirection;
}

public sealed class ImpactEvent : GameEvent
{
    public GameObject SourceRoot;
    public GameObject TargetRoot;
    public Vector3 Impulse;
    public Vector3 HitPoint;
}

public sealed class ItemPickedEvent : GameEvent
{
    public GameObject PickerRoot;
    public string ItemId;
    public string ItemDisplayName;
    public string LinkedWeaponId;
    public string PickupStatus;
    public int ItemType;
    public int Amount;
}

public sealed class WeaponFiredEvent : GameEvent
{
    public GameObject SourceRoot;
    public string WeaponId;
    public int CurrentMagazineAmmo;
    public int CurrentReserveAmmo;
    public int ProjectileCount;
    public string FireModeId;
}

public sealed class EnemyKilledEvent : GameEvent
{
    public GameObject SourceRoot;
    public GameObject EnemyRoot;
    public string EnemyId;
    public string EnemyDisplayName;
}

public sealed class DialogueStartedEvent : GameEvent
{
    public string NpcId;
    public string DialogueId;
    public string SpeakerName;
}

public sealed class DialogueCompletedEvent : GameEvent
{
    public string NpcId;
    public string DialogueId;
    public string FinalNodeId;
}

public sealed class QuestCompletedEvent : GameEvent
{
    public string QuestId;
    public string QuestTitle;
    public int RewardSkillPoints;
}

public sealed class StatusMessageEvent : GameEvent
{
    public string Message;
}

public sealed class InteractionPromptEvent : GameEvent
{
    public string Prompt;
}

public sealed class HudInvalidatedEvent : GameEvent
{
}
