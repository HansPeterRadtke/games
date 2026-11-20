using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace HPR
{
    [Serializable]
    public sealed class AbilityCooldownSnapshot
    {
        public string AbilityId;
        public float Remaining;
    }

    [Serializable]
    public sealed class AbilityRuntimeSnapshot
    {
        public List<string> UnlockedIds = new();
        public List<AbilityCooldownSnapshot> Cooldowns = new();
    }

    public class AbilityRunnerComponent : MonoBehaviour, IAbilityLoadout
    {
        [SerializeField] private List<AbilityData> configuredAbilities = new();
        [SerializeField] private bool unlockAllConfiguredAbilities;
        [SerializeField] private Transform effectOrigin;
        [SerializeField] private LayerMask damageLayers = ~0;
        [SerializeField] private MonoBehaviour eventBusSourceBehaviour;
        [SerializeField] private MonoBehaviour resourcePoolBehaviour;
        // Persist an explicit buyer choice independently of the Unity object reference.
        // A deleted component becomes null after scene reload; never silently rebind
        // the ability to a different resource provider on that same actor.
        [SerializeField, HideInInspector] private bool explicitResourcePoolSelection;

        private readonly Dictionary<string, AbilityData> abilityLookup = new(StringComparer.Ordinal);
        private readonly HashSet<string> conflictingAbilityIds = new(StringComparer.Ordinal);
        private readonly Dictionary<string, float> nextReadyTimes = new(StringComparer.Ordinal);
        private readonly HashSet<string> unlockedAbilityIds = new(StringComparer.Ordinal);
        private readonly HashSet<string> requestedUnlockedAbilityIds = new(StringComparer.Ordinal);

        private IEventBus eventBus;
        private IEventBusSource eventBusSource;
        private IAbilityResourcePool resourcePool;

        public Transform EffectOrigin => effectOrigin != null ? effectOrigin : transform;
        public string LastStatusMessage { get; private set; } = string.Empty;

        private void Awake()
        {
            RefreshRuntimeBindings();
        }

        private void Start()
        {
            RefreshRuntimeBindings();
        }

        private void OnDestroy()
        {
            BindEventBus(null);
        }

        public void BindRuntimeServices(MonoBehaviour eventBusSourceMono, MonoBehaviour resourcePoolMono)
        {
            eventBusSourceBehaviour = eventBusSourceMono;
            resourcePoolBehaviour = resourcePoolMono;
            if (resourcePoolMono != null)
                explicitResourcePoolSelection = true;
            RefreshRuntimeBindings();
        }

        public void ConfigureAbilities(IEnumerable<AbilityData> abilities)
        {
            configuredAbilities = abilities?.Where(ability => ability != null).Distinct().ToList() ?? new List<AbilityData>();
            RebuildLookup();
            if (unlockAllConfiguredAbilities)
            {
                SetUnlockedAbilityIds(configuredAbilities.Select(ability => ability.Id));
            }
            else
            {
                PublishStateChanged();
            }
        }

        public void RefreshRuntimeBindings()
        {
            effectOrigin = effectOrigin != null ? effectOrigin : transform;
            eventBusSource = eventBusSourceBehaviour as IEventBusSource;
            if (resourcePoolBehaviour != null)
            {
                // Directly configured Inspector/API references are explicit even if
                // authored before this field was added to the serialized component.
                explicitResourcePoolSelection = true;
                resourcePool = resourcePoolBehaviour as IAbilityResourcePool;
            }
            else if (explicitResourcePoolSelection)
            {
                // A missing/deleted explicit reference must never fall through to
                // another provider, even when that provider is the sole survivor.
                resourcePool = null;
            }
            else
            {
                // Only an unconfigured runner may discover a local provider, and
                // only when there is exactly one unambiguous candidate.
                var candidates = GetComponents<MonoBehaviour>()
                    .OfType<IAbilityResourcePool>().ToArray();
                resourcePool = candidates.Length == 1 ? candidates[0] : null;
            }
            RebuildLookup();
            if (unlockAllConfiguredAbilities)
            {
                SetUnlockedAbilityIds(configuredAbilities.Where(ability => ability != null).Select(ability => ability.Id));
            }
            BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
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
            PublishStateChanged();
        }

        /// <summary>Capture relative cooldowns so saved states work across sessions.</summary>
        public AbilityRuntimeSnapshot CaptureSnapshot()
        {
            return new AbilityRuntimeSnapshot
            {
                UnlockedIds = unlockedAbilityIds.OrderBy(id => id, StringComparer.Ordinal).ToList(),
                Cooldowns = nextReadyTimes
                    .Where(pair => abilityLookup.ContainsKey(pair.Key) && pair.Value > Time.time)
                    .OrderBy(pair => pair.Key, StringComparer.Ordinal)
                    .Select(pair => new AbilityCooldownSnapshot
                    {
                        AbilityId = pair.Key,
                        Remaining = Mathf.Max(0f, pair.Value - Time.time)
                    }).ToList()
            };
        }

        /// <summary>
        /// Validate all externally supplied save data without changing current
        /// unlocks, timers, resources or events. Unknown or duplicate ability IDs
        /// are errors, not silently ignored entries.
        /// </summary>
        public bool TryValidateSnapshot(AbilityRuntimeSnapshot snapshot, out string reason)
        {
            if (snapshot == null || snapshot.UnlockedIds == null || snapshot.Cooldowns == null)
            {
                reason = "Snapshot is missing ability unlocks or cooldowns.";
                return false;
            }
            var knownUnlocks = new HashSet<string>(StringComparer.Ordinal);
            foreach (string id in snapshot.UnlockedIds)
            {
                if (string.IsNullOrWhiteSpace(id) || !abilityLookup.ContainsKey(id) ||
                    !knownUnlocks.Add(id))
                {
                    reason = "Snapshot contains an unknown, empty or duplicate unlocked ability ID.";
                    return false;
                }
            }

            var cooldownIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (AbilityCooldownSnapshot entry in snapshot.Cooldowns)
            {
                if (entry == null || string.IsNullOrWhiteSpace(entry.AbilityId) ||
                    !abilityLookup.ContainsKey(entry.AbilityId) ||
                    !cooldownIds.Add(entry.AbilityId) ||
                    float.IsNaN(entry.Remaining) || float.IsInfinity(entry.Remaining) ||
                    entry.Remaining < 0f || entry.Remaining > AbilityData.MaximumCooldownSeconds)
                {
                    reason = "Snapshot contains an invalid, unknown or duplicate cooldown.";
                    return false;
                }
            }
            reason = string.Empty;
            return true;
        }

        /// <summary>
        /// Restore a fully validated snapshot and emit one final change event.
        /// Relative cooldowns are anchored to the current engine clock.
        /// </summary>
        public void RestoreSnapshot(AbilityRuntimeSnapshot snapshot)
        {
            if (!TryValidateSnapshot(snapshot, out string error))
                throw new ArgumentException(error, nameof(snapshot));

            var cooldowns = new Dictionary<string, float>(StringComparer.Ordinal);
            float restoreTime = Time.time;
            foreach (AbilityCooldownSnapshot entry in snapshot.Cooldowns)
                cooldowns.Add(entry.AbilityId, restoreTime + entry.Remaining);

            requestedUnlockedAbilityIds.Clear();
            foreach (string id in snapshot.UnlockedIds)
                requestedUnlockedAbilityIds.Add(id);
            RefreshUnlockedAbilityIds();
            nextReadyTimes.Clear();
            foreach (KeyValuePair<string, float> entry in cooldowns)
                nextReadyTimes.Add(entry.Key, entry.Value);
            PublishStateChanged();
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
                    Ready = unlockedAbilityIds.Contains(ability.Id) && !conflictingAbilityIds.Contains(ability.Id) &&
                        GetCooldownRemaining(ability.Id) <= 0f,
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

            if (conflictingAbilityIds.Contains(abilityId))
            {
                PublishStatus($"Duplicate ability ID '{abilityId}'. Give each ability on this runner a unique ID.");
                return false;
            }

            if (!unlockedAbilityIds.Contains(abilityId))
            {
                PublishStatus(ability.FailureStatus);
                return false;
            }

            if (!ability.TryValidateRuntimeSettings(out string configurationError))
            {
                PublishStatus(configurationError);
                return false;
            }

            float cooldownRemaining = GetCooldownRemaining(abilityId);
            if (cooldownRemaining > 0f)
            {
                PublishStatus($"{ability.DisplayName} cooling down {cooldownRemaining:0.0}s");
                return false;
            }

            // An interface reference outlives Unity's destroyed native component.
            // Check Unity object lifetime before invoking any customer callback.
            if (resourcePool == null || (resourcePool is UnityEngine.Object provider && provider == null))
            {
                PublishStatus("Ability resource provider is missing or has been removed.");
                return false;
            }

            if (!resourcePool.SpendAbilityCost(ability.Cost))
            {
                PublishStatus($"{ability.DisplayName} requires {ability.Cost:0} stamina.");
                return false;
            }

            foreach (AbilityEffectData effect in ability.Effects.Where(effect => effect != null))
            {
                ApplyEffect(ability, effect);
            }

            nextReadyTimes[ability.Id] = Time.time + ability.Cooldown;
            eventBus?.Publish(new AbilityUsedEvent
            {
                SourceRoot = gameObject,
                AbilityId = ability.Id,
                AbilityDisplayName = ability.DisplayName
            });
            PublishStateChanged();
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
                if (conflictingAbilityIds.Contains(entry.Id))
                    state = "DUPLICATE ID";
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
                IDamageable damageable = ResolveDamageable(collider);
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

        private static IDamageable ResolveDamageable(Collider collider)
        {
            if (collider == null)
            {
                return null;
            }

            IDamageable directTarget = collider.GetComponents<MonoBehaviour>().OfType<IDamageable>().FirstOrDefault();
            if (directTarget != null)
            {
                return directTarget;
            }

            DamageableTargetProxy proxy = collider.GetComponent<DamageableTargetProxy>();
            return proxy != null ? proxy.Resolve() : null;
        }

        private void RebuildLookup()
        {
            abilityLookup.Clear();
            conflictingAbilityIds.Clear();
            foreach (AbilityData ability in configuredAbilities.Where(ability => ability != null && !string.IsNullOrWhiteSpace(ability.Id)))
            {
                if (!abilityLookup.TryAdd(ability.Id, ability) && abilityLookup[ability.Id] != ability)
                    conflictingAbilityIds.Add(ability.Id);
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

            LastStatusMessage = message;
            eventBus?.Publish(new AbilityStatusEvent { Message = message });
        }

        private void BindEventBus(IEventBus bus)
        {
            eventBus = bus;
        }

        private void PublishStateChanged()
        {
            eventBus?.Publish(new AbilityStateChangedEvent
            {
                SourceRoot = gameObject
            });
        }
    }
}
