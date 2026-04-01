using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace HPR
{
    public class AbilitiesDemoController : MonoBehaviour
    {
        [SerializeField] private AbilityRunnerComponent runner;
        [SerializeField] private GameObject actorRoot;
        [SerializeField] private GameObject targetRoot;
        [SerializeField] private Text readout;

        private AbilityDemoStats ActorStats => actorRoot != null ? actorRoot.GetComponent<AbilityDemoStats>() : null;
        private AbilityDemoStats TargetStats => targetRoot != null ? targetRoot.GetComponent<AbilityDemoStats>() : null;

        public void ValidateDemo()
        {
            AbilityDemoStats actorStats = ActorStats;
            AbilityDemoStats targetStats = TargetStats;
            if (runner == null || actorStats == null || targetStats == null)
            {
                throw new System.InvalidOperationException(
                    $"Abilities demo references => runner:{runner != null} actorRoot:{actorRoot != null} targetRoot:{targetRoot != null} actorStats:{actorStats != null} targetStats:{targetStats != null}");
            }

            actorStats.RefreshRuntimeBindings();
            targetStats.RefreshRuntimeBindings();
            runner.RefreshRuntimeBindings();
            actorStats.ResetVitals();
            targetStats.ResetVitals();

            float actorHealthBefore = actorStats.Health;
            float actorStaminaBefore = actorStats.Stamina;
            float targetHealthBefore = targetStats.Health;

            if (!runner.TryActivateBySlot(0))
            {
                string entries = string.Join(", ", runner.BuildEntries().Select(entry => $"{entry.Id}:{entry.Unlocked}:{entry.Ready}:{entry.CooldownRemaining:0.0}"));
                throw new System.InvalidOperationException($"Abilities demo failed to activate the heal ability. status='{runner.LastStatusMessage}' entries=[{entries}] actorStamina={actorStats.Stamina:0.0}");
            }

            if (actorStats.Health < actorHealthBefore || actorStats.Stamina >= actorStaminaBefore)
            {
                throw new System.InvalidOperationException("Abilities demo heal ability did not change vitals as expected.");
            }

            float targetHealthAfterHeal = targetStats.Health;
            if (!runner.TryActivateBySlot(1))
            {
                throw new System.InvalidOperationException("Abilities demo failed to activate the damage ability.");
            }

            if (targetStats.Health >= targetHealthAfterHeal || targetStats.Health >= targetHealthBefore)
            {
                throw new System.InvalidOperationException("Abilities demo damage ability did not reduce the dummy health.");
            }
        }

        private void Update()
        {
            AbilityDemoStats actorStats = ActorStats;
            AbilityDemoStats targetStats = TargetStats;
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
}
