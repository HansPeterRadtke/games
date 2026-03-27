using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class AbilityRunnerComponent : MonoBehaviour, IAbilityLoadout
{
    [SerializeField] private List<AbilityData> configuredAbilities = new();
    [SerializeField] private bool unlockAllConfiguredAbilities;
    [SerializeField] private Transform effectOrigin;
    [SerializeField] private LayerMask damageLayers = ~0;
    [SerializeField] private MonoBehaviour eventBusSourceBehaviour;
    [SerializeField] private MonoBehaviour resourcePoolBehaviour;

    private readonly Dictionary<string, AbilityData> abilityLookup = new(StringComparer.Ordinal);
    private readonly Dictionary<string, float> nextReadyTimes = new(StringComparer.Ordinal);
    private readonly HashSet<string> unlockedAbilityIds = new(StringComparer.Ordinal);
    private readonly HashSet<string> requestedUnlockedAbilityIds = new(StringComparer.Ordinal);

    private IGameEventBus eventBus;
    private IEventBusSource eventBusSource;
    private IAbilityResourcePool resourcePool;

    public Transform EffectOrigin => effectOrigin != null ? effectOrigin : transform;

    private void Awake()
    {
        effectOrigin = effectOrigin != null ? effectOrigin : transform;
        eventBusSource = eventBusSourceBehaviour as IEventBusSource;
        resourcePool = resourcePoolBehaviour as IAbilityResourcePool ?? GetComponent<IAbilityResourcePool>();
        RebuildLookup();
        if (unlockAllConfiguredAbilities)
        {
            SetUnlockedAbilityIds(configuredAbilities.Where(ability => ability != null).Select(ability => ability.Id));
        }
    }

    private void Start()
    {
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    private void OnDestroy()
    {
        BindEventBus(null);
    }

    public void BindRuntimeServices(MonoBehaviour eventBusSourceMono, MonoBehaviour resourcePoolMono)
    {
        eventBusSourceBehaviour = eventBusSourceMono;
        resourcePoolBehaviour = resourcePoolMono;
        eventBusSource = eventBusSourceBehaviour as IEventBusSource;
        resourcePool = resourcePoolBehaviour as IAbilityResourcePool ?? GetComponent<IAbilityResourcePool>();
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    public void ConfigureAbilities(IEnumerable<AbilityData> abilities)
    {
        configuredAbilities = abilities?.Where(ability => ability != null).Distinct().ToList() ?? new List<AbilityData>();
        RebuildLookup();
        if (unlockAllConfiguredAbilities)
        {
            SetUnlockedAbilityIds(configuredAbilities.Select(ability => ability.Id));
        }
    }

    public void SetUnlockedAbilityIds(IEnumerable<string> abilityIds)
    {
        requestedUnlockedAbilityIds.Clear();
        if (abilityIds != null)
        {
            foreach (string abilityId in abilityIds)
            {
                if (!string.IsNullOrWhiteSpace(abilityId))
                {
                    requestedUnlockedAbilityIds.Add(abilityId);
                }
            }
        }

        RefreshUnlockedAbilityIds();
    }

    public List<AbilityEntryViewData> BuildEntries()
    {
        return configuredAbilities
            .Where(ability => ability != null && !string.IsNullOrWhiteSpace(ability.Id))
            .Select(ability => new AbilityEntryViewData
            {
                Id = ability.Id,
                DisplayName = ability.DisplayName,
                Description = ability.Description,
                Cooldown = Mathf.Max(0f, ability.Cooldown),
                CooldownRemaining = GetCooldownRemaining(ability.Id),
                Cost = Mathf.Max(0f, ability.Cost),
                Unlocked = unlockedAbilityIds.Contains(ability.Id),
                Ready = unlockedAbilityIds.Contains(ability.Id) && GetCooldownRemaining(ability.Id) <= 0f,
                ThemeColor = ability.ThemeColor
            })
            .ToList();
    }

    public bool TryActivateBySlot(int slotIndex)
    {
        var unlocked = configuredAbilities
            .Where(ability => ability != null && !string.IsNullOrWhiteSpace(ability.Id) && unlockedAbilityIds.Contains(ability.Id))
            .ToList();
        if (slotIndex < 0 || slotIndex >= unlocked.Count)
        {
            PublishStatus("Ability slot unavailable.");
            return false;
        }

        return TryActivate(unlocked[slotIndex].Id);
    }

    public bool TryActivate(string abilityId)
    {
        if (string.IsNullOrWhiteSpace(abilityId) || !abilityLookup.TryGetValue(abilityId, out AbilityData ability) || ability == null)
        {
            PublishStatus("Ability unavailable.");
            return false;
        }

        if (!unlockedAbilityIds.Contains(abilityId))
        {
            PublishStatus(ability.FailureStatus);
            return false;
        }

        float cooldownRemaining = GetCooldownRemaining(abilityId);
        if (cooldownRemaining > 0f)
        {
            PublishStatus($"{ability.DisplayName} cooling down {cooldownRemaining:0.0}s");
            return false;
        }

        if (resourcePool == null || !resourcePool.SpendAbilityCost(Mathf.Max(0f, ability.Cost)))
        {
            PublishStatus($"{ability.DisplayName} requires {ability.Cost:0} stamina.");
            return false;
        }

        foreach (AbilityEffectData effect in ability.Effects.Where(effect => effect != null))
        {
            ApplyEffect(ability, effect);
        }

        nextReadyTimes[ability.Id] = Time.time + Mathf.Max(0f, ability.Cooldown);
        eventBus?.Publish(new AbilityUsedEvent
        {
            SourceRoot = gameObject,
            AbilityId = ability.Id,
            AbilityDisplayName = ability.DisplayName
        });
        eventBus?.Publish(new HudInvalidatedEvent());
        PublishStatus(ability.ActivationStatus);
        return true;
    }

    public string BuildHudSummary(params string[] slotLabels)
    {
        var unlocked = BuildEntries().Where(entry => entry.Unlocked).ToList();
        if (unlocked.Count == 0)
        {
            return "Abilities offline";
        }

        var parts = new List<string>();
        for (int index = 0; index < unlocked.Count; index++)
        {
            AbilityEntryViewData entry = unlocked[index];
            string label = slotLabels != null && index < slotLabels.Length && !string.IsNullOrWhiteSpace(slotLabels[index]) ? slotLabels[index] : (index + 1).ToString();
            string state = entry.CooldownRemaining > 0f ? $"{entry.CooldownRemaining:0.0}s" : "READY";
            parts.Add($"{label} {entry.DisplayName} {state}");
        }

        return string.Join(" | ", parts);
    }

    private void ApplyEffect(AbilityData ability, AbilityEffectData effect)
    {
        Vector3 origin = EffectOrigin.position + EffectOrigin.forward * effect.ForwardOffset;
        switch (effect.EffectType)
        {
            case AbilityEffectType.Heal:
                resourcePool?.Heal(Mathf.Max(0f, effect.Value));
                break;
            case AbilityEffectType.RestoreStamina:
                resourcePool?.RestoreStamina(Mathf.Max(0f, effect.Value));
                break;
            case AbilityEffectType.AreaDamage:
                ApplyAreaDamage(origin, effect);
                break;
        }

        eventBus?.Publish(new AbilityEffectAppliedEvent
        {
            SourceRoot = gameObject,
            AbilityId = ability.Id,
            EffectId = effect.Id,
            EffectType = effect.EffectType,
            Value = effect.Value,
            Origin = origin
        });
    }

    private void ApplyAreaDamage(Vector3 origin, AbilityEffectData effect)
    {
        var seenRoots = new HashSet<GameObject>();
        foreach (Collider collider in Physics.OverlapSphere(origin, Mathf.Max(0.25f, effect.Radius), damageLayers, QueryTriggerInteraction.Collide))
        {
            IDamageable damageable = collider.GetComponentInParent<IDamageable>();
            if (damageable is not Component component)
            {
                continue;
            }

            GameObject targetRoot = component.gameObject;
            if (targetRoot == gameObject || !seenRoots.Add(targetRoot))
            {
                continue;
            }

            Vector3 hitDirection = (targetRoot.transform.position - transform.position).normalized;
            eventBus?.Publish(new DamageEvent
            {
                SourceRoot = gameObject,
                TargetRoot = targetRoot,
                Amount = Mathf.Max(0f, effect.Value),
                HitPoint = targetRoot.transform.position,
                HitDirection = hitDirection.sqrMagnitude > 0.001f ? hitDirection : transform.forward
            });
        }
    }

    private void RebuildLookup()
    {
        abilityLookup.Clear();
        foreach (AbilityData ability in configuredAbilities.Where(ability => ability != null && !string.IsNullOrWhiteSpace(ability.Id)))
        {
            abilityLookup[ability.Id] = ability;
        }

        RefreshUnlockedAbilityIds();
    }

    private void RefreshUnlockedAbilityIds()
    {
        unlockedAbilityIds.Clear();
        foreach (string abilityId in requestedUnlockedAbilityIds)
        {
            if (abilityLookup.ContainsKey(abilityId))
            {
                unlockedAbilityIds.Add(abilityId);
            }
        }
    }

    private float GetCooldownRemaining(string abilityId)
    {
        if (string.IsNullOrWhiteSpace(abilityId) || !nextReadyTimes.TryGetValue(abilityId, out float readyAt))
        {
            return 0f;
        }

        return Mathf.Max(0f, readyAt - Time.time);
    }

    private void PublishStatus(string message)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            return;
        }

        eventBus?.Publish(new StatusMessageEvent { Message = message });
    }

    private void BindEventBus(IGameEventBus bus)
    {
        eventBus = bus;
    }
}
