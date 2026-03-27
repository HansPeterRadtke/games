using System.Collections.Generic;
using UnityEngine;

public interface IImpactReceiver
{
    void ApplyImpact(Vector3 impulse, Vector3 point);
}

public interface IPlayerStats : ICharacterStats
{
}

public interface ICombatModifierSource
{
    float DamageMultiplier { get; }
    float MovementSpeedMultiplier { get; }
}

public interface IWeaponLoadout
{
    IReadOnlyList<WeaponRuntimeState> RuntimeSlots { get; }
    int SlotCount { get; }
    int CurrentIndex { get; }
    WeaponRuntimeState CurrentState { get; }
    void SelectSlot(int index);
    bool TrySelectWeapon(string weaponId);
    void AddAmmo(string weaponId, int amount);
    List<WeaponRuntimeSaveData> CaptureRuntimeState();
    void RestoreRuntimeState(IEnumerable<WeaponRuntimeSaveData> savedState, string selectedWeaponId);
    void Reload();
    void TriggerCurrent(IPlayerActor owner);
    void TickPresentation(float movementAmount, bool isAiming, bool isRunning);
}

public interface IPlayerActor : IInteractionActor
{
    Camera ViewCamera { get; }
    IPlayerStats Stats { get; }
    IWeaponLoadout WeaponSystem { get; }
    IAbilityLoadout AbilityLoadout { get; }
    bool IsAiming { get; }
}

public interface IPlayerActorSource
{
    IPlayerActor Player { get; }
}

public interface IEnemyRegistry
{
    void RegisterEnemy(EnemyAgent enemy);
    void UnregisterEnemy(EnemyAgent enemy);
}

public interface ISkillTreeCommands
{
    bool TryUnlockSkill(string skillId);
}

public interface ISkillPointRewardSink
{
    void AwardSkillPoints(int amount, string reason);
}

public interface IQuestStateQuery
{
    bool IsQuestActive(string questId);
    bool IsQuestCompleted(string questId);
    bool IsObjectiveComplete(string questId, string objectiveId);
}

public interface IQuestJournalSource
{
    List<QuestJournalEntryViewData> BuildJournalEntries();
}

public interface IInventoryItemUseCommands
{
    bool TryUseInventoryItem(string itemId);
}

public interface IDialogueFlowCommands
{
    bool StartDialogue(string npcId, string speakerName, DialogueData dialogueData);
    void SelectDialogueChoice(string choiceId);
    void CloseDialogue();
}
