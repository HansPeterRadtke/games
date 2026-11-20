// Private customer-owned action. Works without any HPR component.
#if ENABLE_INPUT_SYSTEM
using System;
using UnityEngine;
using UnityEngine.InputSystem;
namespace ExistingGameWorkflow
{
    public sealed class ExistingHealInput : MonoBehaviour
    {
        [SerializeField] private string binding = "<Keyboard>/h";
        private InputAction action;
        public int PerformedCount { get; private set; }
        public bool ActionEnabled => action != null && action.enabled;
        public event Action HealRequested;
        private void OnEnable()
        {
            if (action == null) action = new InputAction("ExistingCustomerHeal", InputActionType.Button, binding);
            action.performed += OnPerformed; action.Enable();
        }
        private void OnDisable()
        {
            if (action == null) return;
            action.performed -= OnPerformed; action.Disable();
        }
        private void OnDestroy() { action?.Dispose(); action = null; }
        private void OnPerformed(InputAction.CallbackContext context)
        {
            PerformedCount++; HealRequested?.Invoke();
        }
    }
}
#endif
