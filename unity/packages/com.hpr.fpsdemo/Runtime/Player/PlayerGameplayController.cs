using UnityEngine;

[RequireComponent(typeof(PlayerActorContext))]
[RequireComponent(typeof(PlayerController))]
public class PlayerGameplayController : MonoBehaviour
{
    [SerializeField] private float interactRange = 3.5f;
    [SerializeField] private float aimZoomFovDelta = 12f;
    [SerializeField] private float aimFovLerp = 12f;

    private PlayerActorContext actor;
    private PlayerController movement;
    private MapCameraFollow mapFollow;
    private IInteractable currentInteractable;

    public bool IsAiming { get; private set; }

    private void Awake()
    {
        actor = GetComponent<PlayerActorContext>();
        movement = GetComponent<PlayerController>();
    }

    public void BindMapCamera(MapCameraFollow follow)
    {
        mapFollow = follow;
    }

    private void Update()
    {
        if (GameManager.Instance == null || actor == null || movement == null)
        {
            return;
        }

        UpdateGlobalActions();

        if (GameManager.Instance.IsMapVisible)
        {
            HandleMapInput();
            SetAiming(false);
            UpdateAimingFov();
            actor.WeaponSystem.TickPresentation(0f, false, false);
            UpdateInteractionPrompt(null);
            GameManager.Instance.RefreshHud();
            return;
        }

        if (!GameManager.Instance.AllowsGameplayInput)
        {
            SetAiming(false);
            UpdateAimingFov();
            actor.WeaponSystem.TickPresentation(0f, false, false);
            UpdateInteractionPrompt(null);
            GameManager.Instance.RefreshHud();
            return;
        }

        if (HasCombatActivationInput())
        {
            GameManager.Instance.MarkCombatReady();
        }

        UpdateInteraction();
        UpdateWeapons();
        actor.WeaponSystem.TickPresentation(movement.LastMoveMagnitude, IsAiming, movement.IsRunning);
        GameManager.Instance.RefreshHud();
    }

    private void UpdateGlobalActions()
    {
        var options = GameManager.Instance.CurrentOptions;
        if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Pause)))
        {
            GameManager.Instance.TogglePauseMenu();
        }

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Inventory)))
        {
            GameManager.Instance.ToggleInventory();
        }

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Map)))
        {
            GameManager.Instance.ToggleMap();
            if (GameManager.Instance.IsMapVisible)
            {
                mapFollow?.ResetView();
            }
        }

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Flashlight)) && movement.Flashlight != null)
        {
            movement.Flashlight.enabled = !movement.Flashlight.enabled;
            GameManager.Instance.NotifyStatus($"Flashlight {(movement.Flashlight.enabled ? "on" : "off")}");
        }
    }

    private void HandleMapInput()
    {
        if (mapFollow == null)
        {
            return;
        }

        if (Input.GetMouseButton(1))
        {
            mapFollow.Pan(new Vector2(Input.GetAxisRaw("Mouse X"), Input.GetAxisRaw("Mouse Y")));
        }

        if (Mathf.Abs(Input.mouseScrollDelta.y) > 0.01f)
        {
            mapFollow.Zoom(Input.mouseScrollDelta.y);
        }
    }

    private void UpdateInteraction()
    {
        currentInteractable = null;
        if (Physics.Raycast(actor.ViewCamera.transform.position, actor.ViewCamera.transform.forward, out RaycastHit hit, interactRange, ~0, QueryTriggerInteraction.Collide))
        {
            currentInteractable = hit.collider.GetComponentInParent<IInteractable>();
        }

        if (currentInteractable != null)
        {
            UpdateInteractionPrompt(currentInteractable.GetPrompt(actor));
            if (Input.GetKeyDown(GameOptionsStore.GetBinding(GameManager.Instance.CurrentOptions, GameAction.Interact)))
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
        SetAiming(Input.GetMouseButton(1));
        UpdateAimingFov();

        if (Input.GetMouseButton(0))
        {
            actor.WeaponSystem.TriggerCurrent(actor);
        }

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(GameManager.Instance.CurrentOptions, GameAction.Reload)))
        {
            actor.WeaponSystem.Reload();
        }

        if (Mathf.Abs(Input.mouseScrollDelta.y) > 0.01f)
        {
            int direction = Input.mouseScrollDelta.y > 0f ? 1 : -1;
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
            if (Input.GetKeyDown(weaponKeys[i]))
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
        GameManager.Instance.SetInteractionPrompt(prompt);
    }

    private bool HasCombatActivationInput()
    {
        var options = GameManager.Instance.CurrentOptions;
        if (Input.GetMouseButtonDown(0) || Input.GetMouseButtonDown(1) || Mathf.Abs(Input.mouseScrollDelta.y) > 0.01f)
        {
            return true;
        }

        foreach (var action in new[]
                 {
                     GameAction.MoveForward, GameAction.MoveBackward, GameAction.MoveLeft, GameAction.MoveRight,
                     GameAction.Jump, GameAction.Run, GameAction.Interact, GameAction.Reload
                 })
        {
            if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, action)))
            {
                return true;
            }
        }

        for (int i = 1; i <= 9; i++)
        {
            if (Input.GetKeyDown((KeyCode)((int)KeyCode.Alpha0 + i)))
            {
                return true;
            }
        }

        return false;
    }
}
