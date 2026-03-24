using System;
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
    public ItemData ItemData;
    public int Amount;
}

public sealed class WeaponFiredEvent : GameEvent
{
    public GameObject SourceRoot;
    public string WeaponId;
    public int CurrentMagazineAmmo;
    public int CurrentReserveAmmo;
    public int ProjectileCount;
    public FireModeType FireModeType;
}

public sealed class EnemyKilledEvent : GameEvent
{
    public GameObject SourceRoot;
    public GameObject EnemyRoot;
    public string EnemyId;
    public EnemyData EnemyData;
}

public interface IGameEventBus
{
    void Publish<TEvent>(TEvent gameEvent) where TEvent : GameEvent;
    void Subscribe<TEvent>(Action<TEvent> handler) where TEvent : GameEvent;
    void Unsubscribe<TEvent>(Action<TEvent> handler) where TEvent : GameEvent;
}
