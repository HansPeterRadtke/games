using UnityEngine;

namespace HPR
{
    public abstract class FpsDemoEvent
    {
        public float Timestamp { get; } = Time.time;
    }

    public sealed class WeaponFiredEvent : FpsDemoEvent
    {
        public GameObject SourceRoot;
        public string WeaponId;
        public int CurrentMagazineAmmo;
        public int CurrentReserveAmmo;
        public int ProjectileCount;
        public string FireModeId;
    }

    public sealed class ImpactEvent : FpsDemoEvent
    {
        public GameObject SourceRoot;
        public GameObject TargetRoot;
        public Vector3 Impulse;
        public Vector3 HitPoint;
    }

    public sealed class EnemyKilledEvent : FpsDemoEvent
    {
        public GameObject SourceRoot;
        public GameObject EnemyRoot;
        public string EnemyId;
        public string EnemyDisplayName;
    }

    public sealed class DialogueStartedEvent : FpsDemoEvent
    {
        public string NpcId;
        public string DialogueId;
        public string SpeakerName;
    }

    public sealed class DialogueCompletedEvent : FpsDemoEvent
    {
        public string NpcId;
        public string DialogueId;
        public string FinalNodeId;
    }

    public sealed class QuestCompletedEvent : FpsDemoEvent
    {
        public string QuestId;
        public string QuestTitle;
        public int RewardSkillPoints;
    }
}
