using UnityEngine;

public class StatsDemoController : MonoBehaviour
{
    [SerializeField] private ActorStatsComponent targetStats;
    [SerializeField] private EventManager eventManager;

    private const float DamageAmount = 10f;
    private const float HealAmount = 10f;
    private const float StaminaSpendAmount = 15f;
    private const float StaminaRecoverAmount = 12f;

    private void OnGUI()
    {
        if (targetStats == null || eventManager == null)
        {
            GUI.Label(new Rect(20f, 20f, 420f, 24f), "Stats demo is missing references.");
            return;
        }

        GUI.Label(new Rect(20f, 20f, 420f, 24f), $"Health: {targetStats.Health:0}/{targetStats.MaxHealth:0}");
        GUI.Label(new Rect(20f, 48f, 420f, 24f), $"Stamina: {targetStats.Stamina:0}/{targetStats.MaxStamina:0}");

        if (GUI.Button(new Rect(20f, 88f, 150f, 32f), "Publish Damage 10"))
        {
            eventManager.Publish(new DamageEvent
            {
                TargetRoot = targetStats.gameObject,
                Amount = DamageAmount,
                HitPoint = targetStats.transform.position,
                HitDirection = Vector3.forward
            });
        }

        if (GUI.Button(new Rect(180f, 88f, 150f, 32f), "Heal 10"))
        {
            targetStats.Heal(HealAmount);
        }

        if (GUI.Button(new Rect(20f, 128f, 150f, 32f), "Spend Stamina"))
        {
            targetStats.ConsumeStamina(StaminaSpendAmount);
        }

        if (GUI.Button(new Rect(180f, 128f, 150f, 32f), "Recover Stamina"))
        {
            targetStats.RegenerateStamina(StaminaRecoverAmount);
        }

        if (GUI.Button(new Rect(20f, 168f, 310f, 32f), "Reset Stats"))
        {
            targetStats.ResetStats();
        }
    }
}
