using System.Linq;
using UnityEngine;

namespace HPR
{
    [RequireComponent(typeof(PlayerActorContext))]
    [RequireComponent(typeof(PlayerController))]
    public class PlayerGameplayController : MonoBehaviour
    {
        [SerializeField] private float interactRange = 3.5f;
        [SerializeField] private float aimZoomFovDelta = 12f;
        [SerializeField] private float aimFovLerp = 12f;
        [SerializeField] private MonoBehaviour servicesBehaviour;
        [SerializeField] private MonoBehaviour inputSourceBehaviour;

        private PlayerActorContext actor;
        private PlayerController movement;
        private MapCameraFollow mapFollow;
        private IInteractable currentInteractable;
        private IGameplayStateSource gameplayState;
        private IInputBindingsSource inputBindings;
        private IInputSource inputSource;
        private IStatusMessageSink statusSink;
        private IInteractionPromptSink promptSink;
        private IHudRefreshSink hudRefreshSink;
        private IGameplayFlowCommands flowCommands;

        public bool IsAiming { get; private set; }

        private void Awake()
        {
            actor = GetComponent<PlayerActorContext>();
            movement = GetComponent<PlayerController>();
            servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : FindBehaviourImplementing<IGameplayStateSource>();
            inputSourceBehaviour = inputSourceBehaviour != null ? inputSourceBehaviour : GetComponents<MonoBehaviour>().FirstOrDefault(component => component is IInputSource);
            gameplayState = ResolveInterface<IGameplayStateSource>(servicesBehaviour);
            inputBindings = ResolveInterface<IInputBindingsSource>(servicesBehaviour);
            inputSource = ResolveInterface<IInputSource>(inputSourceBehaviour);
            statusSink = ResolveInterface<IStatusMessageSink>(servicesBehaviour);
            promptSink = ResolveInterface<IInteractionPromptSink>(servicesBehaviour);
            hudRefreshSink = ResolveInterface<IHudRefreshSink>(servicesBehaviour);
            flowCommands = ResolveInterface<IGameplayFlowCommands>(servicesBehaviour);
        }

        public void BindMapCamera(MapCameraFollow follow)
        {
            mapFollow = follow;
        }

        public void BindRuntimeServices(MonoBehaviour services, MonoBehaviour inputBehaviour)
        {
            servicesBehaviour = services;
            inputSourceBehaviour = inputBehaviour;
            gameplayState = ResolveInterface<IGameplayStateSource>(servicesBehaviour);
            inputBindings = ResolveInterface<IInputBindingsSource>(servicesBehaviour);
            inputSource = ResolveInterface<IInputSource>(inputSourceBehaviour);
            statusSink = ResolveInterface<IStatusMessageSink>(servicesBehaviour);
            promptSink = ResolveInterface<IInteractionPromptSink>(servicesBehaviour);
            hudRefreshSink = ResolveInterface<IHudRefreshSink>(servicesBehaviour);
            flowCommands = ResolveInterface<IGameplayFlowCommands>(servicesBehaviour);
        }

        private void Update()
        {
            if (actor == null || movement == null || gameplayState == null || inputBindings == null || inputSource == null)
            {
                return;
            }

            UpdateGlobalActions();

            if (gameplayState.IsMapVisible)
            {
                HandleMapInput();
                SetAiming(false);
                UpdateAimingFov();
                actor.WeaponSystem.TickPresentation(0f, false, false);
                UpdateInteractionPrompt(null);
                hudRefreshSink?.RefreshHud();
                return;
            }

            if (!gameplayState.AllowsGameplayInput)
            {
                SetAiming(false);
                UpdateAimingFov();
                actor.WeaponSystem.TickPresentation(0f, false, false);
                UpdateInteractionPrompt(null);
                hudRefreshSink?.RefreshHud();
                return;
            }

            if (HasCombatActivationInput())
            {
                flowCommands?.MarkCombatReady();
            }

            UpdateInteraction();
            UpdateWeapons();
            actor.WeaponSystem.TickPresentation(movement.LastMoveMagnitude, IsAiming, movement.IsRunning);
            hudRefreshSink?.RefreshHud();
        }

        private void UpdateGlobalActions()
        {
            var options = inputBindings.CurrentOptions;
            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Pause)) && !gameplayState.IsRebindingKey)
            {
                if (gameplayState.IsDialogueVisible)
                {
                    flowCommands?.CloseDialogue();
                }
                else if (gameplayState.IsOptionsVisible)
                {
                    flowCommands?.ShowOptionsMenu(false);
                }
                else if (gameplayState.IsMapVisible)
                {
                    flowCommands?.ToggleMap();
                }
                else if (gameplayState.IsInventoryVisible)
                {
                    flowCommands?.ToggleInventory();
                }
                else if (gameplayState.IsJournalVisible)
                {
                    flowCommands?.ToggleJournal();
                }
                else if (gameplayState.IsSkillsVisible)
                {
                    flowCommands?.ToggleSkills();
                }
                else
                {
                    flowCommands?.TogglePauseMenu();
                }
            }

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Inventory)))
            {
                flowCommands?.ToggleInventory();
            }

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Journal)))
            {
                flowCommands?.ToggleJournal();
            }

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Skills)))
            {
                flowCommands?.ToggleSkills();
            }

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Map)))
            {
                flowCommands?.ToggleMap();
                if (gameplayState.IsMapVisible)
                {
                    mapFollow?.ResetView();
                }
            }

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Flashlight)) && movement.Flashlight != null)
            {
                movement.Flashlight.enabled = !movement.Flashlight.enabled;
                statusSink?.NotifyStatus($"Flashlight {(movement.Flashlight.enabled ? "on" : "off")}");
            }
        }

        private void HandleMapInput()
        {
            if (mapFollow == null)
            {
                return;
            }

            if (inputSource.GetMouseButton(1))
            {
                mapFollow.Pan(new Vector2(inputSource.GetAxisRaw("Mouse X"), inputSource.GetAxisRaw("Mouse Y")));
            }

            if (Mathf.Abs(inputSource.MouseScrollDelta.y) > 0.01f)
            {
                mapFollow.Zoom(inputSource.MouseScrollDelta.y);
            }
        }

        private void UpdateInteraction()
        {
            currentInteractable = null;
            if (Physics.Raycast(actor.ViewCamera.transform.position, actor.ViewCamera.transform.forward, out RaycastHit hit, interactRange, ~0, QueryTriggerInteraction.Collide))
            {
                currentInteractable = hit.collider.GetComponentsInParent<MonoBehaviour>(true).OfType<IInteractable>().FirstOrDefault();
            }

            if (currentInteractable != null)
            {
                UpdateInteractionPrompt(currentInteractable.GetPrompt(actor));
                if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(inputBindings.CurrentOptions, GameAction.Interact)))
                {
                    currentInteractable.Interact(actor);
                }
            }
            else
            {
                UpdateInteractionPrompt(null);
            }
        }

        private void UpdateWeapons()
        {
            SetAiming(inputSource.GetMouseButton(1));
            UpdateAimingFov();

            if (inputSource.GetMouseButton(0))
            {
                actor.WeaponSystem.TriggerCurrent(actor);
            }

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(inputBindings.CurrentOptions, GameAction.Reload)))
            {
                actor.WeaponSystem.Reload();
            }

            if (actor.AbilityLoadout != null)
            {
                if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(inputBindings.CurrentOptions, GameAction.AbilityPrimary)))
                {
                    actor.AbilityLoadout.TryActivateBySlot(0);
                }

                if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(inputBindings.CurrentOptions, GameAction.AbilitySecondary)))
                {
                    actor.AbilityLoadout.TryActivateBySlot(1);
                }
            }

            if (Mathf.Abs(inputSource.MouseScrollDelta.y) > 0.01f)
            {
                int direction = inputSource.MouseScrollDelta.y > 0f ? 1 : -1;
                int nextIndex = (actor.WeaponSystem.CurrentIndex + direction + actor.WeaponSystem.SlotCount) % actor.WeaponSystem.SlotCount;
                actor.WeaponSystem.SelectSlot(nextIndex);
            }

            KeyCode[] weaponKeys =
            {
                KeyCode.Alpha1, KeyCode.Alpha2, KeyCode.Alpha3, KeyCode.Alpha4, KeyCode.Alpha5,
                KeyCode.Alpha6, KeyCode.Alpha7, KeyCode.Alpha8, KeyCode.Alpha9
            };
            for (int i = 0; i < weaponKeys.Length && i < actor.WeaponSystem.SlotCount; i++)
            {
                if (inputSource.GetKeyDown(weaponKeys[i]))
                {
                    actor.WeaponSystem.SelectSlot(i);
                }
            }
        }

        private void SetAiming(bool aiming)
        {
            IsAiming = aiming;
            movement.SetAiming(aiming);
        }

        private void UpdateAimingFov()
        {
            if (actor.ViewCamera == null)
            {
                return;
            }

            float targetFov = IsAiming ? movement.BaseFieldOfView - aimZoomFovDelta : movement.BaseFieldOfView;
            actor.ViewCamera.fieldOfView = Mathf.Lerp(actor.ViewCamera.fieldOfView, targetFov, aimFovLerp * Time.unscaledDeltaTime);
        }

        private void UpdateInteractionPrompt(string prompt)
        {
            promptSink?.SetInteractionPrompt(prompt);
        }

        private bool HasCombatActivationInput()
        {
            var options = inputBindings.CurrentOptions;
            if (inputSource.GetMouseButtonDown(0) || inputSource.GetMouseButtonDown(1) || Mathf.Abs(inputSource.MouseScrollDelta.y) > 0.01f)
            {
                return true;
            }

            foreach (var action in new[]
                     {
                         GameAction.MoveForward, GameAction.MoveBackward, GameAction.MoveLeft, GameAction.MoveRight,
                         GameAction.Jump, GameAction.Run, GameAction.Interact, GameAction.Reload,
                         GameAction.AbilityPrimary, GameAction.AbilitySecondary
                     })
            {
                if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, action)))
                {
                    return true;
                }
            }

            for (int i = 1; i <= 9; i++)
            {
                if (inputSource.GetKeyDown((KeyCode)((int)KeyCode.Alpha0 + i)))
                {
                    return true;
                }
            }

            return false;
        }

        private static T ResolveInterface<T>(MonoBehaviour behaviour) where T : class
        {
            return behaviour as T;
        }

        private MonoBehaviour FindBehaviourImplementing<T>() where T : class
        {
            return GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is T);
        }
    }
}
