using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

[Serializable]
public class SkillEntryViewData
{
    public string Id;
    public string DisplayName;
    public string Description;
    public int Cost;
    public bool Unlocked;
    public bool Available;
    public Color ThemeColor;
}

public class SkillTreeComponent : MonoBehaviour, ICombatModifierSource
{
    [SerializeField] private List<SkillNodeData> skillNodes = new();
    [SerializeField] private int startingSkillPoints = 1;
    [SerializeField] private int pointsPerEnemyKill = 1;
    [SerializeField] private MonoBehaviour servicesBehaviour;

    private readonly HashSet<string> unlockedSkillIds = new(StringComparer.Ordinal);
    private readonly Dictionary<string, SkillNodeData> nodeLookup = new(StringComparer.Ordinal);
    private IEventBus eventBus;
    private IEventBusSource eventBusSource;
    private IStatusMessageSink statusSink;
    private IHudRefreshSink hudRefreshSink;
    private PlayerStats playerStats;
    private PlayerController playerController;
    private bool restoredFromSave;

    public int SkillPoints { get; private set; }
    public float DamageMultiplier { get; private set; } = 1f;
    public float MovementSpeedMultiplier { get; private set; } = 1f;

    private void Awake()
    {
        playerStats = GetComponent<PlayerStats>();
        playerController = GetComponent<PlayerController>();
        servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IEventBusSource || component is IStatusMessageSink || component is IHudRefreshSink);
        statusSink = servicesBehaviour as IStatusMessageSink;
        hudRefreshSink = servicesBehaviour as IHudRefreshSink;
        eventBusSource = servicesBehaviour as IEventBusSource;
        RebuildLookup();
        EnsureInitialState();
        ApplyBonuses();
    }

    private void Start()
    {
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    private void OnDestroy()
    {
        BindEventBus(null);
    }

    public void BindRuntimeServices(MonoBehaviour services)
    {
        servicesBehaviour = services;
        statusSink = servicesBehaviour as IStatusMessageSink;
        hudRefreshSink = servicesBehaviour as IHudRefreshSink;
        eventBusSource = servicesBehaviour as IEventBusSource;
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
        ApplyBonuses();
    }

    public void ConfigureSkills(IEnumerable<SkillNodeData> skills)
    {
        skillNodes = skills?.Where(skill => skill != null).Distinct().ToList() ?? new List<SkillNodeData>();
        RebuildLookup();
        EnsureInitialState();
        ApplyBonuses();
    }

    public void RestoreState(IEnumerable<string> unlockedIds, int skillPoints)
    {
        restoredFromSave = true;
        unlockedSkillIds.Clear();
        if (unlockedIds != null)
        {
            foreach (string id in unlockedIds)
            {
                if (!string.IsNullOrWhiteSpace(id) && nodeLookup.ContainsKey(id))
                {
                    unlockedSkillIds.Add(id);
                }
            }
        }

        foreach (SkillNodeData node in skillNodes.Where(node => node != null && node.StartingUnlocked))
        {
            unlockedSkillIds.Add(node.Id);
        }

        SkillPoints = Mathf.Max(0, skillPoints);
        ApplyBonuses();
    }

    public List<string> CaptureUnlockedSkillIds()
    {
        return unlockedSkillIds.OrderBy(id => id, StringComparer.Ordinal).ToList();
    }

    public List<string> BuildUnlockedAbilityIds()
    {
        return skillNodes
            .Where(node => node != null && unlockedSkillIds.Contains(node.Id))
            .SelectMany(node => node.GrantedAbilities ?? new List<AbilityData>())
            .Where(ability => ability != null && !string.IsNullOrWhiteSpace(ability.Id))
            .Select(ability => ability.Id)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(id => id, StringComparer.Ordinal)
            .ToList();
    }

    public List<SkillEntryViewData> BuildEntries()
    {
        return skillNodes
            .Where(skill => skill != null && !string.IsNullOrWhiteSpace(skill.Id))
            .OrderBy(skill => skill.Cost)
            .ThenBy(skill => skill.DisplayName)
            .Select(skill => new SkillEntryViewData
            {
                Id = skill.Id,
                DisplayName = skill.DisplayName,
                Description = skill.Description,
                Cost = skill.Cost,
                Unlocked = unlockedSkillIds.Contains(skill.Id),
                Available = CanUnlock(skill.Id),
                ThemeColor = skill.ThemeColor
            })
            .ToList();
    }

    public bool CanUnlock(string skillId)
    {
        if (string.IsNullOrWhiteSpace(skillId) || !nodeLookup.TryGetValue(skillId, out SkillNodeData node) || unlockedSkillIds.Contains(skillId))
        {
            return false;
        }

        if (SkillPoints < Mathf.Max(1, node.Cost))
        {
            return false;
        }

        return node.Prerequisites == null || node.Prerequisites.All(requirement => requirement == null || unlockedSkillIds.Contains(requirement.Id));
    }

    public bool TryUnlock(string skillId)
    {
        if (!CanUnlock(skillId) || !nodeLookup.TryGetValue(skillId, out SkillNodeData node))
        {
            return false;
        }

        SkillPoints -= Mathf.Max(1, node.Cost);
        unlockedSkillIds.Add(skillId);
        ApplyBonuses();
        statusSink?.NotifyStatus($"Unlocked {node.DisplayName}");
        return true;
    }

    public void AwardPoints(int amount)
    {
        if (amount <= 0)
        {
            return;
        }

        SkillPoints += amount;
        hudRefreshSink?.RefreshHud();
        statusSink?.NotifyStatus($"Skill point +{amount}");
    }

    private void EnsureInitialState()
    {
        if (restoredFromSave)
        {
            return;
        }

        if (SkillPoints <= 0)
        {
            SkillPoints = Mathf.Max(0, startingSkillPoints);
        }

        foreach (SkillNodeData node in skillNodes.Where(node => node != null && node.StartingUnlocked))
        {
            if (!string.IsNullOrWhiteSpace(node.Id))
            {
                unlockedSkillIds.Add(node.Id);
            }
        }
    }

    private void RebuildLookup()
    {
        nodeLookup.Clear();
        foreach (SkillNodeData node in skillNodes.Where(node => node != null && !string.IsNullOrWhiteSpace(node.Id)))
        {
            nodeLookup[node.Id] = node;
        }
    }

    private void ApplyBonuses()
    {
        float healthBonus = 0f;
        float staminaBonus = 0f;
        float damageBonus = 0f;
        float moveSpeedBonus = 0f;

        foreach (string unlockedId in unlockedSkillIds)
        {
            if (!nodeLookup.TryGetValue(unlockedId, out SkillNodeData node) || node == null)
            {
                continue;
            }

            healthBonus += Mathf.Max(0f, node.MaxHealthBonus);
            staminaBonus += Mathf.Max(0f, node.MaxStaminaBonus);
            damageBonus += Mathf.Max(0f, node.DamageMultiplierBonus);
            moveSpeedBonus += Mathf.Max(0f, node.MoveSpeedMultiplierBonus);
        }

        DamageMultiplier = 1f + damageBonus;
        MovementSpeedMultiplier = 1f + moveSpeedBonus;
        playerStats?.SetRuntimeBonuses(healthBonus, staminaBonus);
        playerController?.SetExternalMoveSpeedMultiplier(MovementSpeedMultiplier);
        hudRefreshSink?.RefreshHud();
    }

    private void BindEventBus(IEventBus bus)
    {
        if (eventBus == bus)
        {
            return;
        }

        if (eventBus != null)
        {
            eventBus.Unsubscribe<EnemyKilledEvent>(HandleEnemyKilledEvent);
        }

        eventBus = bus;
        if (eventBus != null)
        {
            eventBus.Subscribe<EnemyKilledEvent>(HandleEnemyKilledEvent);
        }
    }

    private void HandleEnemyKilledEvent(EnemyKilledEvent gameEvent)
    {
        if (gameEvent == null || pointsPerEnemyKill <= 0)
        {
            return;
        }

        if (gameEvent.SourceRoot == null || gameEvent.SourceRoot != gameObject)
        {
            return;
        }

        AwardPoints(pointsPerEnemyKill);
    }
}
