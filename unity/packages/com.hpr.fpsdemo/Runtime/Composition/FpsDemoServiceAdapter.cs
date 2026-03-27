using System.Collections.Generic;
using UnityEngine;

public sealed class FpsDemoServiceAdapter : MonoBehaviour, IInputBindingsSource, IOptionsController, IEventBusSource, IGameplayStateSource, IStatusMessageSink, IInteractionPromptSink, IHudRefreshSink, IThreatScanner, IGameplayFlowCommands, IGameMenuCommands, IPlayerDeathHandler, IPlayerActorSource, IEnemyRegistry, ISkillTreeCommands, IQuestJournalSource, IDialogueFlowCommands, ISkillPointRewardSink, IQuestStateQuery, IInventoryItemUseCommands
{
    private IServiceResolver services;

    public GameOptionsData CurrentOptions => services.ResolveOptional<IInputBindingsSource>()?.CurrentOptions ?? GameOptionsData.CreateDefault();
    public IEventBus EventBus => services.ResolveOptional<IEventBus>();
    public bool AllowsGameplayInput => services.ResolveOptional<IGameplayStateSource>()?.AllowsGameplayInput ?? false;
    public bool IsGameplayRunning => services.ResolveOptional<IGameplayStateSource>()?.IsGameplayRunning ?? false;
    public bool IsMapVisible => services.ResolveOptional<IGameplayStateSource>()?.IsMapVisible ?? false;
    public bool IsInventoryVisible => services.ResolveOptional<IGameplayStateSource>()?.IsInventoryVisible ?? false;
    public bool IsJournalVisible => services.ResolveOptional<IGameplayStateSource>()?.IsJournalVisible ?? false;
    public bool IsSkillsVisible => services.ResolveOptional<IGameplayStateSource>()?.IsSkillsVisible ?? false;
    public bool IsDialogueVisible => services.ResolveOptional<IGameplayStateSource>()?.IsDialogueVisible ?? false;
    public bool IsPauseVisible => services.ResolveOptional<IGameplayStateSource>()?.IsPauseVisible ?? false;
    public bool IsOptionsVisible => services.ResolveOptional<IGameplayStateSource>()?.IsOptionsVisible ?? false;
    public bool IsRebindingKey => services.ResolveOptional<IGameplayStateSource>()?.IsRebindingKey ?? false;
    public bool IsCombatLive => services.ResolveOptional<IGameplayStateSource>()?.IsCombatLive ?? false;
    public bool HasSaveGame => services.ResolveOptional<IGameMenuCommands>()?.HasSaveGame ?? false;
    public IPlayerActor Player => services.ResolveOptional<IPlayerActorSource>()?.Player;

    public void Configure(IServiceResolver serviceResolver)
    {
        services = serviceResolver;
    }

    public void ApplyOptions(GameOptionsData updatedOptions)
    {
        services.ResolveOptional<IOptionsController>()?.ApplyOptions(updatedOptions);
    }

    public void RebindAction(GameAction action, KeyCode key)
    {
        services.ResolveOptional<IOptionsController>()?.RebindAction(action, key);
    }

    public void NotifyStatus(string message)
    {
        services.ResolveOptional<IStatusMessageSink>()?.NotifyStatus(message);
    }

    public void SetInteractionPrompt(string prompt)
    {
        services.ResolveOptional<IInteractionPromptSink>()?.SetInteractionPrompt(prompt);
    }

    public void RefreshHud()
    {
        services.ResolveOptional<IHudRefreshSink>()?.RefreshHud();
    }

    public string DescribeNearbyThreats(Vector3 position)
    {
        return services.ResolveOptional<IThreatScanner>()?.DescribeNearbyThreats(position) ?? string.Empty;
    }

    public void MarkCombatReady()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.MarkCombatReady();
    }

    public void TogglePauseMenu()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.TogglePauseMenu();
    }

    public void ToggleInventory()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.ToggleInventory();
    }

    public void ToggleJournal()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.ToggleJournal();
    }

    public void ToggleSkills()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.ToggleSkills();
    }

    public void ToggleMap()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.ToggleMap();
    }

    public void ShowOptionsMenu(bool visible)
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.ShowOptionsMenu(visible);
    }

    public void CloseDialogue()
    {
        services.ResolveOptional<IGameplayFlowCommands>()?.CloseDialogue();
    }

    public void ActivatePrimaryMenuAction()
    {
        services.ResolveOptional<IGameMenuCommands>()?.ActivatePrimaryMenuAction();
    }

    public void ResumeSession()
    {
        services.ResolveOptional<IGameMenuCommands>()?.ResumeSession();
    }

    public void SaveGame()
    {
        services.ResolveOptional<IGameMenuCommands>()?.SaveGame();
    }

    public void LoadGame()
    {
        services.ResolveOptional<IGameMenuCommands>()?.LoadGame();
    }

    public void StartNewGame()
    {
        services.ResolveOptional<IGameMenuCommands>()?.StartNewGame();
    }

    public void ExitGame()
    {
        services.ResolveOptional<IGameMenuCommands>()?.ExitGame();
    }

    public void HandlePlayerDeath()
    {
        services.ResolveOptional<IPlayerDeathHandler>()?.HandlePlayerDeath();
    }

    public void RegisterEnemy(EnemyAgent enemy)
    {
        services.ResolveOptional<IEnemyRegistry>()?.RegisterEnemy(enemy);
    }

    public void UnregisterEnemy(EnemyAgent enemy)
    {
        services.ResolveOptional<IEnemyRegistry>()?.UnregisterEnemy(enemy);
    }

    public bool TryUnlockSkill(string skillId)
    {
        return services.ResolveOptional<ISkillTreeCommands>()?.TryUnlockSkill(skillId) ?? false;
    }

    public void AwardSkillPoints(int amount, string reason)
    {
        services.ResolveOptional<ISkillPointRewardSink>()?.AwardSkillPoints(amount, reason);
    }

    public bool IsQuestActive(string questId)
    {
        return services.ResolveOptional<IQuestStateQuery>()?.IsQuestActive(questId) ?? false;
    }

    public bool IsQuestCompleted(string questId)
    {
        return services.ResolveOptional<IQuestStateQuery>()?.IsQuestCompleted(questId) ?? false;
    }

    public bool IsObjectiveComplete(string questId, string objectiveId)
    {
        return services.ResolveOptional<IQuestStateQuery>()?.IsObjectiveComplete(questId, objectiveId) ?? false;
    }

    public List<QuestJournalEntryViewData> BuildJournalEntries()
    {
        return services.ResolveOptional<IQuestJournalSource>()?.BuildJournalEntries() ?? new List<QuestJournalEntryViewData>();
    }

    public bool TryUseInventoryItem(string itemId)
    {
        return services.ResolveOptional<IInventoryItemUseCommands>()?.TryUseInventoryItem(itemId) ?? false;
    }

    public bool StartDialogue(string npcId, string speakerName, DialogueData dialogueData)
    {
        return services.ResolveOptional<IDialogueFlowCommands>()?.StartDialogue(npcId, speakerName, dialogueData) ?? false;
    }

    public void SelectDialogueChoice(string choiceId)
    {
        services.ResolveOptional<IDialogueFlowCommands>()?.SelectDialogueChoice(choiceId);
    }
}
