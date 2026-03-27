using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

public class AbilitiesDemoController : MonoBehaviour
{
    [SerializeField] private AbilityRunnerComponent runner;
    [SerializeField] private AbilityDemoStats actorStats;
    [SerializeField] private AbilityDemoStats targetStats;
    [SerializeField] private Text readout;

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1))
        {
            runner?.TryActivateBySlot(0);
        }
        if (Input.GetKeyDown(KeyCode.Alpha2))
        {
            runner?.TryActivateBySlot(1);
        }
        if (Input.GetKeyDown(KeyCode.R))
        {
            actorStats?.ResetVitals();
            targetStats?.ResetVitals();
        }

        if (readout != null && runner != null && actorStats != null && targetStats != null)
        {
            List<AbilityEntryViewData> entries = runner.BuildEntries().Where(entry => entry.Unlocked).ToList();
            string abilities = string.Join("\n", entries.Select((entry, index) => $"{index + 1}. {entry.DisplayName} | Cost {entry.Cost:0} | {(entry.CooldownRemaining > 0f ? $"CD {entry.CooldownRemaining:0.0}s" : "READY")}"));
            readout.text = $"Actor HP {actorStats.Health:0}/{actorStats.MaxHealth:0} | Stamina {actorStats.Stamina:0}/{actorStats.MaxStamina:0}\n" +
                           $"Dummy HP {targetStats.Health:0}/{targetStats.MaxHealth:0}\n\n" +
                           abilities + "\n\n1 Repair Pulse\n2 Shock Pulse\nR Reset";
        }
    }
}

public class AbilityDemoStats : ActorStatsComponent, IAbilityResourcePool
{
    public bool SpendAbilityCost(float amount)
    {
        return ConsumeStamina(amount);
    }

    public void RestoreStamina(float amount)
    {
        RegenerateStamina(amount);
    }

    public void ResetVitals()
    {
        ResetStats();
    }
}
