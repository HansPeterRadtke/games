using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class QuestManager : MonoBehaviour, IQuestJournalSource, IQuestStateQuery
{
    [SerializeField] private List<QuestData> questDefinitions = new();
    [SerializeField] private MonoBehaviour servicesBehaviour;

    private readonly Dictionary<string, QuestData> questLookup = new(StringComparer.Ordinal);
    private readonly Dictionary<string, QuestRuntimeState> questStates = new(StringComparer.Ordinal);

    private IEventBus eventBus;
    private IEventBusSource eventBusSource;
    private IStatusMessageSink statusSink;
    private IHudRefreshSink hudRefreshSink;
    private IPlayerActorSource playerSource;
    private ISkillPointRewardSink skillRewardSink;
    private bool restoredFromSave;

    public bool HasActiveQuests => questStates.Values.Any(state => state.Started && !state.Completed);

    private void Awake()
    {
        servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component =>
            component is IEventBusSource || component is IStatusMessageSink || component is IHudRefreshSink || component is IPlayerActorSource || component is ISkillPointRewardSink);
        ResolveServices();
        RebuildLookup();
        EnsureStateInitialized();
    }

    private void Start()
    {
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    private void OnDestroy()
    {
        BindEventBus(null);
    }

    public void ConfigureQuests(IEnumerable<QuestData> quests)
    {
        questDefinitions = quests?.Where(quest => quest != null && !string.IsNullOrWhiteSpace(quest.Id)).Distinct().ToList() ?? new List<QuestData>();
        RebuildLookup();
        EnsureStateInitialized();
    }

    public void BindRuntimeServices(MonoBehaviour services)
    {
        servicesBehaviour = services;
        ResolveServices();
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    public void ResetQuestState()
    {
        restoredFromSave = false;
        questStates.Clear();
        EnsureStateInitialized();
        hudRefreshSink?.RefreshHud();
    }

    public bool TryStartQuest(string questId)
    {
        if (!questLookup.TryGetValue(questId, out QuestData quest) || quest == null)
        {
            return false;
        }

        QuestRuntimeState state = GetOrCreateState(quest);
        if (state.Completed)
        {
            statusSink?.NotifyStatus($"{quest.Title} already completed");
            return false;
        }

        if (state.Started)
        {
            statusSink?.NotifyStatus($"{quest.Title} already active");
            return false;
        }

        state.Started = true;
        statusSink?.NotifyStatus($"Quest accepted: {quest.Title}");
        hudRefreshSink?.RefreshHud();
        return true;
    }

    public bool IsQuestActive(string questId)
    {
        return !string.IsNullOrWhiteSpace(questId) && questStates.TryGetValue(questId, out QuestRuntimeState state) && state.Started && !state.Completed;
    }

    public bool IsQuestCompleted(string questId)
    {
        return !string.IsNullOrWhiteSpace(questId) && questStates.TryGetValue(questId, out QuestRuntimeState state) && state.Completed;
    }

    public bool IsObjectiveComplete(string questId, string objectiveId)
    {
        if (string.IsNullOrWhiteSpace(questId) || string.IsNullOrWhiteSpace(objectiveId) || !questStates.TryGetValue(questId, out QuestRuntimeState state))
        {
            return false;
        }

        return state.IsObjectiveComplete(objectiveId);
    }

    public List<QuestStateSaveData> CaptureState()
    {
        return questStates.Values
            .Where(state => state.Started || state.Completed)
            .OrderBy(state => state.Data.Title, StringComparer.Ordinal)
            .Select(state => new QuestStateSaveData
            {
                questId = state.Data.Id,
                started = state.Started,
                completed = state.Completed,
                objectiveCounts = state.ObjectiveCounts.ToList()
            })
            .ToList();
    }

    public void RestoreState(IEnumerable<QuestStateSaveData> savedStates)
    {
        restoredFromSave = true;
        questStates.Clear();
        RebuildLookup();
        foreach (QuestData quest in questDefinitions)
        {
            GetOrCreateState(quest);
        }

        if (savedStates != null)
        {
            foreach (QuestStateSaveData saved in savedStates)
            {
                if (saved == null || string.IsNullOrWhiteSpace(saved.questId) || !questStates.TryGetValue(saved.questId, out QuestRuntimeState state))
                {
                    continue;
                }

                state.Started = saved.started || saved.completed;
                state.Completed = saved.completed;
                for (int index = 0; index < state.ObjectiveCounts.Count && index < saved.objectiveCounts.Count; index++)
                {
                    int required = state.RequiredCountAt(index);
                    state.ObjectiveCounts[index] = Mathf.Clamp(saved.objectiveCounts[index], 0, required);
                }
            }
        }

        foreach (QuestData quest in questDefinitions.Where(quest => quest != null && quest.StartOnSession))
        {
            GetOrCreateState(quest).Started = true;
        }

        hudRefreshSink?.RefreshHud();
    }

    public List<QuestJournalEntryViewData> BuildJournalEntries()
    {
        return questStates.Values
            .Where(state => state.Started || state.Completed)
            .OrderBy(state => state.Completed)
            .ThenBy(state => state.Data.Title, StringComparer.Ordinal)
            .Select(state => new QuestJournalEntryViewData
            {
                Id = state.Data.Id,
                Title = state.Data.Title,
                Description = state.Data.Description,
                Active = state.Started && !state.Completed,
                Completed = state.Completed,
                ThemeColor = state.Data.ThemeColor,
                Objectives = state.BuildObjectiveView()
            })
            .ToList();
    }

    private void ResolveServices()
    {
        eventBusSource = servicesBehaviour as IEventBusSource;
        statusSink = servicesBehaviour as IStatusMessageSink;
        hudRefreshSink = servicesBehaviour as IHudRefreshSink;
        playerSource = servicesBehaviour as IPlayerActorSource;
        skillRewardSink = servicesBehaviour as ISkillPointRewardSink;
    }

    private void EnsureStateInitialized()
    {
        foreach (QuestData quest in questDefinitions)
        {
            GetOrCreateState(quest);
        }

        if (restoredFromSave)
        {
            return;
        }

        foreach (QuestData quest in questDefinitions.Where(quest => quest != null && quest.StartOnSession))
        {
            GetOrCreateState(quest).Started = true;
        }
    }

    private void RebuildLookup()
    {
        questLookup.Clear();
        foreach (QuestData quest in questDefinitions.Where(quest => quest != null && !string.IsNullOrWhiteSpace(quest.Id)))
        {
            questLookup[quest.Id] = quest;
        }
    }

    private QuestRuntimeState GetOrCreateState(QuestData quest)
    {
        if (questStates.TryGetValue(quest.Id, out QuestRuntimeState state))
        {
            return state;
        }

        state = new QuestRuntimeState(quest);
        questStates[quest.Id] = state;
        return state;
    }

    private void BindEventBus(IEventBus bus)
    {
        if (eventBus == bus)
        {
            return;
        }

        if (eventBus != null)
        {
            eventBus.Unsubscribe<ItemPickedEvent>(HandleItemPickedEvent);
            eventBus.Unsubscribe<EnemyKilledEvent>(HandleEnemyKilledEvent);
            eventBus.Unsubscribe<DialogueCompletedEvent>(HandleDialogueCompletedEvent);
        }

        eventBus = bus;
        if (eventBus != null)
        {
            eventBus.Subscribe<ItemPickedEvent>(HandleItemPickedEvent);
            eventBus.Subscribe<EnemyKilledEvent>(HandleEnemyKilledEvent);
            eventBus.Subscribe<DialogueCompletedEvent>(HandleDialogueCompletedEvent);
        }
    }

    private void HandleItemPickedEvent(ItemPickedEvent gameEvent)
    {
        AdvanceMatchingObjectives(QuestObjectiveType.CollectItem, gameEvent?.ItemId, Mathf.Max(1, gameEvent?.Amount ?? 1));
    }

    private void HandleEnemyKilledEvent(EnemyKilledEvent gameEvent)
    {
        AdvanceMatchingObjectives(QuestObjectiveType.KillEnemy, gameEvent?.EnemyId, 1);
    }

    private void HandleDialogueCompletedEvent(DialogueCompletedEvent gameEvent)
    {
        if (gameEvent == null)
        {
            return;
        }

        AdvanceMatchingObjectives(QuestObjectiveType.TalkToNpc, gameEvent.NpcId, 1);
        if (!string.IsNullOrWhiteSpace(gameEvent.NpcId) && !string.IsNullOrWhiteSpace(gameEvent.FinalNodeId))
        {
            AdvanceMatchingObjectives(QuestObjectiveType.TalkToNpc, $"{gameEvent.NpcId}:{gameEvent.FinalNodeId}", 1);
        }
    }

    private void AdvanceMatchingObjectives(QuestObjectiveType objectiveType, string targetId, int amount)
    {
        if (string.IsNullOrWhiteSpace(targetId) || amount <= 0)
        {
            return;
        }

        bool changed = false;
        foreach (QuestRuntimeState state in questStates.Values)
        {
            if (!state.Started || state.Completed)
            {
                continue;
            }

            changed |= state.Advance(objectiveType, targetId, amount);
            if (state.Started && !state.Completed && state.IsComplete)
            {
                CompleteQuest(state);
                changed = true;
            }
        }

        if (changed)
        {
            hudRefreshSink?.RefreshHud();
        }
    }

    private void CompleteQuest(QuestRuntimeState state)
    {
        state.Completed = true;
        statusSink?.NotifyStatus($"Quest complete: {state.Data.Title}");

        if (state.Data.RewardItem != null && state.Data.RewardItemAmount > 0)
        {
            playerSource?.Player?.InventoryService?.AddItem(state.Data.RewardItem, state.Data.RewardItemAmount);
        }

        if (state.Data.RewardSkillPoints > 0)
        {
            skillRewardSink?.AwardSkillPoints(state.Data.RewardSkillPoints, state.Data.Title);
        }

        eventBus?.Publish(new QuestCompletedEvent
        {
            QuestId = state.Data.Id,
            QuestTitle = state.Data.Title,
            RewardSkillPoints = Mathf.Max(0, state.Data.RewardSkillPoints)
        });
    }

    private sealed class QuestRuntimeState
    {
        public QuestRuntimeState(QuestData data)
        {
            Data = data;
            ObjectiveCounts = data?.Objectives?.Select(_ => 0).ToList() ?? new List<int>();
        }

        public QuestData Data { get; }
        public bool Started { get; set; }
        public bool Completed { get; set; }
        public List<int> ObjectiveCounts { get; }
        public bool IsComplete
        {
            get
            {
                if (Data == null || Data.Objectives == null || Data.Objectives.Count == 0)
                {
                    return false;
                }

                for (int index = 0; index < Data.Objectives.Count; index++)
                {
                    if (ObjectiveCounts[index] < Mathf.Max(1, Data.Objectives[index].RequiredCount))
                    {
                        return false;
                    }
                }

                return true;
            }
        }

        public int RequiredCountAt(int index)
        {
            if (Data == null || Data.Objectives == null || index < 0 || index >= Data.Objectives.Count)
            {
                return 0;
            }

            return Mathf.Max(1, Data.Objectives[index].RequiredCount);
        }

        public bool Advance(QuestObjectiveType objectiveType, string targetId, int amount)
        {
            if (Data == null || Data.Objectives == null)
            {
                return false;
            }

            bool changed = false;
            for (int index = 0; index < Data.Objectives.Count; index++)
            {
                QuestObjectiveData objective = Data.Objectives[index];
                if (objective == null || objective.ObjectiveType != objectiveType || !string.Equals(objective.TargetId, targetId, StringComparison.Ordinal))
                {
                    continue;
                }

                int required = Mathf.Max(1, objective.RequiredCount);
                int previous = ObjectiveCounts[index];
                ObjectiveCounts[index] = Mathf.Clamp(previous + amount, 0, required);
                changed |= ObjectiveCounts[index] != previous;
            }

            return changed;
        }

        public bool IsObjectiveComplete(string objectiveId)
        {
            if (string.IsNullOrWhiteSpace(objectiveId) || Data == null || Data.Objectives == null)
            {
                return false;
            }

            for (int index = 0; index < Data.Objectives.Count; index++)
            {
                QuestObjectiveData objective = Data.Objectives[index];
                if (objective == null || !string.Equals(objective.Id, objectiveId, StringComparison.Ordinal))
                {
                    continue;
                }

                return ObjectiveCounts[index] >= Mathf.Max(1, objective.RequiredCount);
            }

            return false;
        }

        public List<QuestObjectiveProgressViewData> BuildObjectiveView()
        {
            var result = new List<QuestObjectiveProgressViewData>();
            if (Data == null || Data.Objectives == null)
            {
                return result;
            }

            for (int index = 0; index < Data.Objectives.Count; index++)
            {
                QuestObjectiveData objective = Data.Objectives[index];
                int required = Mathf.Max(1, objective.RequiredCount);
                int current = index < ObjectiveCounts.Count ? ObjectiveCounts[index] : 0;
                result.Add(new QuestObjectiveProgressViewData
                {
                    Description = string.IsNullOrWhiteSpace(objective.Description) ? objective.TargetId : objective.Description,
                    CurrentCount = current,
                    RequiredCount = required,
                    Completed = current >= required
                });
            }

            return result;
        }
    }
}
