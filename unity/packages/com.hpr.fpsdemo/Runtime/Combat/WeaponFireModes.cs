using System;
using UnityEngine;

public interface IFireMode
{
    bool Execute(WeaponFireContext context);
}

public sealed class WeaponFireContext
{
    public WeaponFireContext(WeaponSystem weaponSystem, IPlayerActor owner, WeaponRuntimeState runtimeState)
    {
        WeaponSystem = weaponSystem;
        Owner = owner;
        RuntimeState = runtimeState;
    }

    public WeaponSystem WeaponSystem { get; }
    public IPlayerActor Owner { get; }
    public WeaponRuntimeState RuntimeState { get; }
    public WeaponData Data => RuntimeState.Data;
    public Camera PlayerCamera => WeaponSystem.PlayerCamera;
    public Transform MuzzleTransform => WeaponSystem.ResolveCurrentMuzzle();
    public IInventoryService Inventory => WeaponSystem.InventoryService;
    public IPlayerStats OwnerStats => WeaponSystem.OwnerStats;
    public IEventBus EventBus => WeaponSystem.EventBus;

    public bool TryConsumeAmmo()
    {
        return WeaponSystem.TryConsumeAmmo(RuntimeState);
    }

    public void ApplyFireAnimation(float multiplier)
    {
        WeaponSystem.ApplyFireAnimation(RuntimeState, multiplier);
    }

    public Vector3 ResolveDirection(float spread)
    {
        Vector3 direction = PlayerCamera.transform.forward;
        if (spread <= 0f)
        {
            return direction;
        }

        return Quaternion.Euler(
            UnityEngine.Random.Range(-spread, spread),
            UnityEngine.Random.Range(-spread, spread),
            0f) * direction;
    }

    public void CreateProjectile(Vector3 direction, float explosiveRadius, float projectileScale, float lifetime)
    {
        WeaponSystem.CreateProjectile(Owner.ActorTransform, MuzzleTransform.position, direction, Data, ScaleDamage(Data.Damage), explosiveRadius, projectileScale, lifetime);
    }

    public void PublishWeaponFired(int projectileCount)
    {
        EventBus?.Publish(new WeaponFiredEvent
        {
            SourceRoot = Owner.ActorTransform.gameObject,
            WeaponId = Data != null ? Data.Id : string.Empty,
            CurrentMagazineAmmo = RuntimeState.MagazineAmmo,
            CurrentReserveAmmo = RuntimeState.ReserveAmmo,
            ProjectileCount = projectileCount,
            FireModeId = Data != null ? Data.FireModeType.ToString() : string.Empty
        });
    }

    public void PublishDamage(GameObject targetRoot, float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        if (targetRoot == null)
        {
            return;
        }

        EventBus?.Publish(new DamageEvent
        {
            SourceRoot = Owner.ActorTransform.gameObject,
            TargetRoot = targetRoot,
            Amount = ScaleDamage(amount),
            HitPoint = hitPoint,
            HitDirection = hitDirection
        });
    }

    public void PublishImpact(GameObject targetRoot, Vector3 impulse, Vector3 hitPoint)
    {
        if (targetRoot == null)
        {
            return;
        }

        EventBus?.Publish(new ImpactEvent
        {
            SourceRoot = Owner.ActorTransform.gameObject,
            TargetRoot = targetRoot,
            Impulse = impulse,
            HitPoint = hitPoint
        });
    }

    public void Notify(string message)
    {
        WeaponSystem.StatusSink?.NotifyStatus(message);
    }

    private float ScaleDamage(float amount)
    {
        if (Owner?.ActorTransform == null)
        {
            return amount;
        }

        foreach (var behaviour in Owner.ActorTransform.GetComponents<MonoBehaviour>())
        {
            if (behaviour is ICombatModifierSource modifiers)
            {
                return amount * Mathf.Max(0.1f, modifiers.DamageMultiplier);
            }
        }

        return amount;
    }
}

public static class FireModeFactory
{
    public static IFireMode Create(FireModeType fireModeType)
    {
        switch (fireModeType)
        {
            case FireModeType.Projectile:
                return new ProjectileFireMode();
            case FireModeType.Shotgun:
                return new ShotgunFireMode();
            case FireModeType.Melee:
                return new MeleeFireMode();
            case FireModeType.Utility:
                return new UtilityFireMode();
            default:
                return new HitscanFireMode();
        }
    }
}

internal static class FireModeTargetResolver
{
    public static GameObject ResolveDamageTarget(Collider collider)
    {
        return collider != null ? (collider.GetComponentInParent<IDamageable>() as Component)?.gameObject : null;
    }

    public static GameObject ResolveImpactTarget(Collider collider)
    {
        return collider != null ? (collider.GetComponentInParent<IImpactReceiver>() as Component)?.gameObject : null;
    }
}

public sealed class HitscanFireMode : IFireMode
{
    public bool Execute(WeaponFireContext context)
    {
        if (!context.TryConsumeAmmo())
        {
            return false;
        }

        context.ApplyFireAnimation(1f);
        Vector3 direction = context.ResolveDirection(context.Data.Spread);
        if (Physics.Raycast(context.PlayerCamera.transform.position, direction, out RaycastHit hit, context.Data.Range, ~0, QueryTriggerInteraction.Ignore))
        {
            GameObject targetRoot = FireModeTargetResolver.ResolveDamageTarget(hit.collider);
            GameObject impactTarget = FireModeTargetResolver.ResolveImpactTarget(hit.collider);
            if (targetRoot != null && targetRoot != context.Owner.ActorTransform.gameObject)
            {
                context.PublishDamage(targetRoot, context.Data.Damage, hit.point, direction);
            }

            if (impactTarget != null && impactTarget != context.Owner.ActorTransform.gameObject)
            {
                context.PublishImpact(impactTarget, direction * context.Data.ImpactForce, hit.point);
            }

            if (hit.rigidbody != null && !hit.rigidbody.isKinematic)
            {
                hit.rigidbody.AddForceAtPosition(direction * context.Data.ImpactForce, hit.point, ForceMode.Impulse);
            }
        }

        context.PublishWeaponFired(1);
        context.Notify(context.Data.DisplayName + " fired");
        return true;
    }
}

public sealed class ProjectileFireMode : IFireMode
{
    public bool Execute(WeaponFireContext context)
    {
        if (!context.TryConsumeAmmo())
        {
            return false;
        }

        context.ApplyFireAnimation(context.Data.ExplosiveRadius > 0f ? 1.3f : 1f);
        Vector3 direction = context.ResolveDirection(context.Data.Spread);
        float lifetime = Mathf.Clamp(context.Data.Range / Mathf.Max(8f, context.Data.ProjectileSpeed), 1.2f, 4f);
        context.CreateProjectile(direction, context.Data.ExplosiveRadius, context.Data.ProjectileScale, lifetime);
        context.PublishWeaponFired(1);
        context.Notify(context.Data.DisplayName + " fired");
        return true;
    }
}

public sealed class ShotgunFireMode : IFireMode
{
    public bool Execute(WeaponFireContext context)
    {
        if (!context.TryConsumeAmmo())
        {
            return false;
        }

        context.ApplyFireAnimation(1.15f);
        int pellets = Mathf.Max(1, context.Data.Pellets);
        int landedHits = 0;
        for (int index = 0; index < pellets; index++)
        {
            Vector3 direction = context.ResolveDirection(context.Data.Spread);
            if (!Physics.Raycast(context.PlayerCamera.transform.position, direction, out RaycastHit hit, context.Data.Range, ~0, QueryTriggerInteraction.Ignore))
            {
                continue;
            }

            GameObject targetRoot = FireModeTargetResolver.ResolveDamageTarget(hit.collider);
            GameObject impactTarget = FireModeTargetResolver.ResolveImpactTarget(hit.collider);
            if (targetRoot != null && targetRoot != context.Owner.ActorTransform.gameObject)
            {
                context.PublishDamage(targetRoot, context.Data.Damage, hit.point, direction);
                landedHits++;
            }

            if (impactTarget != null && impactTarget != context.Owner.ActorTransform.gameObject)
            {
                context.PublishImpact(impactTarget, direction * context.Data.ImpactForce, hit.point);
            }

            if (hit.rigidbody != null && !hit.rigidbody.isKinematic)
            {
                hit.rigidbody.AddForceAtPosition(direction * context.Data.ImpactForce, hit.point, ForceMode.Impulse);
            }
        }

        context.PublishWeaponFired(pellets);
        context.Notify(landedHits > 0 ? context.Data.DisplayName + " fired" : context.Data.DisplayName + " blasted");
        return true;
    }
}

public sealed class MeleeFireMode : IFireMode
{
    private const float MeleeHitRadius = 1.15f;
    private const float MeleeRangeFactor = 0.65f;

    public bool Execute(WeaponFireContext context)
    {
        context.ApplyFireAnimation(1.5f);

        Vector3 center = context.PlayerCamera.transform.position + context.PlayerCamera.transform.forward * Mathf.Clamp(context.Data.Range * MeleeRangeFactor, 1f, 1.8f);
        Collider[] hits = Physics.OverlapSphere(center, MeleeHitRadius, ~0, QueryTriggerInteraction.Ignore);
        Collider bestCollider = null;
        Vector3 bestPoint = center;
        float bestDistance = float.MaxValue;

        foreach (Collider collider in hits)
        {
            if (collider.transform.root == context.Owner.ActorTransform)
            {
                continue;
            }

            IDamageable damageable = collider.GetComponentInParent<IDamageable>();
            if (damageable == null || !damageable.IsAlive)
            {
                continue;
            }

            Vector3 point = collider.ClosestPoint(center);
            float distance = (point - center).sqrMagnitude;
            if (distance >= bestDistance)
            {
                continue;
            }

            bestDistance = distance;
            bestCollider = collider;
            bestPoint = point;
        }

        if (bestCollider == null)
        {
            context.Notify(context.Data.DisplayName + " missed");
            return false;
        }

        Vector3 hitDirection = (bestPoint - context.PlayerCamera.transform.position).normalized;
        GameObject targetRoot = FireModeTargetResolver.ResolveDamageTarget(bestCollider);
        GameObject impactTarget = FireModeTargetResolver.ResolveImpactTarget(bestCollider);
        if (targetRoot == null && impactTarget == null)
        {
            context.Notify(context.Data.DisplayName + " missed");
            return false;
        }

        context.PublishDamage(targetRoot, context.Data.Damage, bestPoint, hitDirection);
        context.PublishImpact(impactTarget ?? targetRoot, hitDirection * context.Data.ImpactForce, bestPoint);
        if (bestCollider.attachedRigidbody != null && !bestCollider.attachedRigidbody.isKinematic)
        {
            bestCollider.attachedRigidbody.AddForceAtPosition(hitDirection * context.Data.ImpactForce, bestPoint, ForceMode.Impulse);
        }

        context.PublishWeaponFired(1);
        context.Notify(context.Data.DisplayName + " connected");
        return true;
    }
}

public sealed class UtilityFireMode : IFireMode
{
    public bool Execute(WeaponFireContext context)
    {
        WeaponData data = context.Data;
        if (data == null)
        {
            return false;
        }

        switch (data.UtilityAction)
        {
            case WeaponUtilityAction.ConsumeItem:
                return ConsumeLinkedItem(context);
            case WeaponUtilityAction.ThreatScan:
                context.Notify(context.WeaponSystem.ThreatScanner != null ? context.WeaponSystem.ThreatScanner.DescribeNearbyThreats(context.Owner.ActorTransform.position) : data.UtilityMessage);
                return true;
            case WeaponUtilityAction.KeyringStatus:
                context.Notify(context.Inventory != null && context.Inventory.HasAnyItemOfType(ItemType.Key) ? data.UtilityMessage : "Keyring is empty");
                return true;
            case WeaponUtilityAction.RepairTool:
                context.Notify(data.UtilityMessage);
                return true;
            default:
                context.Notify(data.UtilityMessage);
                return true;
        }
    }

    private static bool ConsumeLinkedItem(WeaponFireContext context)
    {
        if (context.Inventory == null || context.OwnerStats == null)
        {
            return false;
        }

        ItemData item = context.Inventory.GetItemData(context.Data.LinkedItemId);
        if (item == null)
        {
            context.Notify(context.Data.UtilityMessage);
            return false;
        }

        if (!context.Inventory.HasItem(item.Id))
        {
            context.Notify("No " + item.DisplayName + " available");
            return false;
        }

        if (item.Value > 0 && context.OwnerStats.Health >= context.OwnerStats.MaxHealth - 1f)
        {
            context.Notify("Health already full");
            return false;
        }

        if (!context.Inventory.RemoveItem(item.Id, 1))
        {
            context.Notify("No " + item.DisplayName + " available");
            return false;
        }

        if (item.Value > 0)
        {
            context.OwnerStats.Heal(item.Value);
        }

        context.PublishWeaponFired(1);
        context.Notify(string.IsNullOrWhiteSpace(context.Data.UtilityMessage) ? "Used " + item.DisplayName : context.Data.UtilityMessage);
        return true;
    }
}
