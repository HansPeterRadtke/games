// Private customer integration glue; the original action remains game-owned.
#if ENABLE_INPUT_SYSTEM
using System;
using UnityEngine;
using HPR;
namespace ExistingGameWorkflow
{
    public sealed class HprExistingInputBinding : MonoBehaviour
    {
        [SerializeField] private ExistingHealInput input;
        [SerializeField] private AbilityRunnerComponent runner;
        [SerializeField] private string abilityId;
        private ExistingHealInput subscribedInput;
        public int RequestCount { get; private set; }
        public int SuccessCount { get; private set; }
        public void Configure(ExistingHealInput value, AbilityRunnerComponent target, string id)
        {
            if (value == null || target == null || value.gameObject != gameObject || target.gameObject != gameObject || string.IsNullOrWhiteSpace(id))
                throw new ArgumentException("Assign the existing action and runner on this actor");
            Detach(); input = value; runner = target; abilityId = id;
            if (isActiveAndEnabled) Attach();
        }
        private void OnEnable() { Attach(); }
        private void OnDisable() { Detach(); }
        private void OnDestroy() { Detach(); }
        private void Attach()
        {
            if (input == null || runner == null || string.IsNullOrWhiteSpace(abilityId) || subscribedInput == input) return;
            Detach(); subscribedInput = input; subscribedInput.HealRequested += Activate;
        }
        private void Detach()
        {
            if (subscribedInput != null) subscribedInput.HealRequested -= Activate;
            subscribedInput = null;
        }
        private void Activate()
        {
            RequestCount++;
            if (runner != null && runner.TryActivate(abilityId)) SuccessCount++;
        }
    }
}
#endif
