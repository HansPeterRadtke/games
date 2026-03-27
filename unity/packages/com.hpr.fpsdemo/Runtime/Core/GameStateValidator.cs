using UnityEngine;

public class GameStateValidator : MonoBehaviour
{
    private int damageEventCount;
    private int itemPickedEventCount;
    private int weaponFiredEventCount;
    private int enemyKilledEventCount;
    private int dialogueCompletedEventCount;
    private int questCompletedEventCount;

    private IGameEventBus eventBus;

    public void Bind(IGameEventBus bus)
    {
        if (eventBus == bus)
        {
            return;
        }

        Unsubscribe();
        eventBus = bus;
        Subscribe();
    }

    public void ResetCounters()
    {
        damageEventCount = 0;
        itemPickedEventCount = 0;
        weaponFiredEventCount = 0;
        enemyKilledEventCount = 0;
        dialogueCompletedEventCount = 0;
        questCompletedEventCount = 0;
    }

    public void ValidatePlayerDamage(IPlayerStats stats, float previousHealth)
    {
        AssertCondition(damageEventCount > 0, "Expected at least one DamageEvent");
        AssertCondition(stats.Health < previousHealth, "Expected player health to decrease");
    }

    public void ValidateWeaponFire(WeaponRuntimeState runtimeState, int previousMagazineAmmo)
    {
        AssertCondition(weaponFiredEventCount > 0, "Expected WeaponFiredEvent");
        if (runtimeState.Data.UsesAmmo)
        {
            AssertCondition(runtimeState.MagazineAmmo < previousMagazineAmmo, "Expected weapon ammo to decrease");
        }
    }

    public void ValidateInventoryPickup(IInventoryService inventory, string itemId, int previousQuantity)
    {
        AssertCondition(itemPickedEventCount > 0, "Expected ItemPickedEvent");
        AssertCondition(inventory.GetQuantity(itemId) > previousQuantity, "Expected inventory quantity to increase");
    }

    public void ValidateEnemyDeath(EnemyAgent enemy)
    {
        AssertCondition(enemyKilledEventCount > 0, "Expected EnemyKilledEvent");
        AssertCondition(enemy == null || !enemy.gameObject.activeSelf || !enemy.IsAlive, "Expected enemy to be dead");
    }

    public void ValidateSkillPointGain(SkillTreeComponent skillTree, int previousPoints)
    {
        AssertCondition(enemyKilledEventCount > 0, "Expected EnemyKilledEvent before awarding skill points");
        AssertCondition(skillTree != null && skillTree.SkillPoints > previousPoints, "Expected skill points to increase");
    }

    public void ValidateDialogueCompletion()
    {
        AssertCondition(dialogueCompletedEventCount > 0, "Expected DialogueCompletedEvent");
    }

    public void ValidateQuestCompletion(QuestManager questManager, string questId)
    {
        AssertCondition(questCompletedEventCount > 0, "Expected QuestCompletedEvent");
        AssertCondition(questManager != null && questManager.IsQuestCompleted(questId), $"Expected quest '{questId}' to be completed");
    }

    private void OnDestroy()
    {
        Unsubscribe();
    }

    private void Subscribe()
    {
        if (eventBus == null)
        {
            return;
        }

        eventBus.Subscribe<DamageEvent>(HandleDamageEvent);
        eventBus.Subscribe<ItemPickedEvent>(HandleItemPickedEvent);
        eventBus.Subscribe<WeaponFiredEvent>(HandleWeaponFiredEvent);
        eventBus.Subscribe<EnemyKilledEvent>(HandleEnemyKilledEvent);
        eventBus.Subscribe<DialogueCompletedEvent>(HandleDialogueCompletedEvent);
        eventBus.Subscribe<QuestCompletedEvent>(HandleQuestCompletedEvent);
    }

    private void Unsubscribe()
    {
        if (eventBus == null)
        {
            return;
        }

        eventBus.Unsubscribe<DamageEvent>(HandleDamageEvent);
        eventBus.Unsubscribe<ItemPickedEvent>(HandleItemPickedEvent);
        eventBus.Unsubscribe<WeaponFiredEvent>(HandleWeaponFiredEvent);
        eventBus.Unsubscribe<EnemyKilledEvent>(HandleEnemyKilledEvent);
        eventBus.Unsubscribe<DialogueCompletedEvent>(HandleDialogueCompletedEvent);
        eventBus.Unsubscribe<QuestCompletedEvent>(HandleQuestCompletedEvent);
    }

    private void HandleDamageEvent(DamageEvent gameEvent)
    {
        damageEventCount++;
    }

    private void HandleItemPickedEvent(ItemPickedEvent gameEvent)
    {
        itemPickedEventCount++;
    }

    private void HandleWeaponFiredEvent(WeaponFiredEvent gameEvent)
    {
        weaponFiredEventCount++;
    }

    private void HandleEnemyKilledEvent(EnemyKilledEvent gameEvent)
    {
        enemyKilledEventCount++;
    }

    private void HandleDialogueCompletedEvent(DialogueCompletedEvent gameEvent)
    {
        dialogueCompletedEventCount++;
    }

    private void HandleQuestCompletedEvent(QuestCompletedEvent gameEvent)
    {
        questCompletedEventCount++;
    }

    private static void AssertCondition(bool condition, string message)
    {
        if (!condition)
        {
            throw new System.InvalidOperationException(message);
        }
    }
}
