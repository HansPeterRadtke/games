using UnityEngine;

[RequireComponent(typeof(CharacterController))]
[RequireComponent(typeof(PlayerStats))]
[RequireComponent(typeof(PlayerInventory))]
[RequireComponent(typeof(WeaponSystem))]
public class PlayerController : MonoBehaviour, IImpactReceiver
{
    [SerializeField] private float walkSpeed = 5.5f;
    [SerializeField] private float runMultiplier = 1.8f;
    [SerializeField] private float gravity = -24f;
    [SerializeField] private float jumpHeight = 1.25f;
    [SerializeField] private float interactRange = 3.5f;
    [SerializeField] private float staminaDrainPerSecond = 24f;
    [SerializeField] private float staminaRecoverPerSecond = 18f;
    [SerializeField] private float coyoteTime = 0.14f;
    [SerializeField] private float jumpBufferTime = 0.16f;
    [SerializeField] private float groundedStickVelocity = 4f;
    [SerializeField] private float impactDamping = 8f;
    [SerializeField] private float aimZoomFovDelta = 12f;
    [SerializeField] private float aimFovLerp = 12f;

    private CharacterController characterController;
    private Camera playerCamera;
    private Light flashlight;
    private MapCameraFollow mapFollow;
    private Vector3 verticalVelocity;
    private Vector3 impactVelocity;
    private float yaw;
    private float pitch;
    private float baseFieldOfView;
    private float lastGroundedTime = -99f;
    private float lastJumpPressedTime = -99f;
    private float lastMoveMagnitude;
    private bool lastRunning;
    private bool aiming;
    private IInteractable currentInteractable;

    public PlayerStats Stats { get; private set; }
    public PlayerInventory Inventory { get; private set; }
    public WeaponSystem WeaponSystem { get; private set; }
    public Camera PlayerCamera => playerCamera;
    public float Pitch => pitch;
    public float Yaw => yaw;
    public bool IsAiming => aiming;

    private void Awake()
    {
        characterController = GetComponent<CharacterController>();
        Stats = GetComponent<PlayerStats>();
        Inventory = GetComponent<PlayerInventory>();
        WeaponSystem = GetComponent<WeaponSystem>();
        playerCamera = GetComponentInChildren<Camera>();
        flashlight = GetComponentInChildren<Light>(true);
        WeaponSystem.Initialize(playerCamera);
        yaw = transform.eulerAngles.y;
        pitch = playerCamera.transform.localEulerAngles.x;
        if (pitch > 180f)
        {
            pitch -= 360f;
        }
    }

    private void Start()
    {
        mapFollow = FindAnyObjectByType<MapCameraFollow>();
        ApplyOptions(GameManager.Instance.CurrentOptions);
    }

    private void Update()
    {
        if (GameManager.Instance == null)
        {
            return;
        }

        UpdateGlobalActions();

        if (GameManager.Instance.IsMapVisible)
        {
            HandleMapInput();
            aiming = false;
            UpdateAimingFov();
            WeaponSystem.TickPresentation(0f, false, false);
            UpdateInteractionPrompt(null);
            return;
        }

        if (!GameManager.Instance.AllowsGameplayInput)
        {
            aiming = false;
            UpdateAimingFov();
            WeaponSystem.TickPresentation(0f, false, false);
            UpdateInteractionPrompt(null);
            return;
        }

        if (HasCombatActivationInput())
        {
            GameManager.Instance.MarkCombatReady();
        }

        UpdateLook();
        UpdateMovement();
        UpdateInteraction();
        UpdateWeapons();
        WeaponSystem.TickPresentation(lastMoveMagnitude, aiming, lastRunning);
        UpdateHud();
    }

    public void ApplyOptions(GameOptionsData options)
    {
        GameOptionsStore.Apply(options, playerCamera);
        baseFieldOfView = options.fieldOfView;
    }

    public void RestoreFromSave(PlayerSaveData saveData)
    {
        characterController.enabled = false;
        transform.position = saveData.position.ToVector3();
        yaw = saveData.yaw;
        pitch = saveData.pitch;
        transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        playerCamera.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
        characterController.enabled = true;

        Stats.SetHealth(saveData.health);
        Stats.SetStamina(saveData.stamina);
        Inventory.ClearInventory();
        for (int i = 0; i < saveData.medkits; i++) Inventory.AddMedkit();
        for (int i = 0; i < saveData.armorPatches; i++) Inventory.AddArmorPatch();
        if (saveData.hasRedKey) Inventory.AddRedKey();
        if (saveData.hasBlueKey) Inventory.AddBlueKey();
        WeaponSystem.SetAmmoState(saveData.magazineAmmo, saveData.reserveAmmo, saveData.currentSlot);
        verticalVelocity = Vector3.zero;
        impactVelocity = Vector3.zero;
        lastGroundedTime = Time.time;
    }

    public PlayerSaveData CaptureSaveData()
    {
        var data = new PlayerSaveData
        {
            position = new SerializableVector3(transform.position),
            yaw = yaw,
            pitch = pitch,
            health = Stats.Health,
            stamina = Stats.Stamina,
            currentSlot = WeaponSystem.CurrentIndex,
            medkits = Inventory.Medkits,
            armorPatches = Inventory.ArmorPatches,
            hasRedKey = Inventory.HasRedKey,
            hasBlueKey = Inventory.HasBlueKey
        };
        WeaponSystem.CopyAmmoState(data.magazineAmmo, data.reserveAmmo);
        return data;
    }

    public void ApplyImpact(Vector3 impulse, Vector3 point)
    {
        impactVelocity += impulse;
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

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Flashlight)) && flashlight != null)
        {
            flashlight.enabled = !flashlight.enabled;
            GameManager.Instance.NotifyStatus($"Flashlight {(flashlight.enabled ? "on" : "off")}");
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

    private void UpdateLook()
    {
        var options = GameManager.Instance.CurrentOptions;
        float mouseX = Input.GetAxisRaw("Mouse X") * options.lookSensitivity;
        float mouseY = Input.GetAxisRaw("Mouse Y") * options.lookSensitivity * (options.invertY ? 1f : -1f);

        yaw += mouseX;
        pitch = Mathf.Clamp(pitch + mouseY, -85f, 85f);

        transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        playerCamera.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
    }

    private void UpdateMovement()
    {
        var options = GameManager.Instance.CurrentOptions;
        Vector3 moveDirection = Vector3.zero;
        if (Input.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveForward))) moveDirection += transform.forward;
        if (Input.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveBackward))) moveDirection -= transform.forward;
        if (Input.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveRight))) moveDirection += transform.right;
        if (Input.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveLeft))) moveDirection -= transform.right;
        moveDirection = moveDirection.normalized;

        bool groundedBeforeMove = characterController.isGrounded;
        if (groundedBeforeMove)
        {
            lastGroundedTime = Time.time;
            if (verticalVelocity.y < 0f)
            {
                verticalVelocity.y = -groundedStickVelocity;
            }
        }

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Jump)))
        {
            lastJumpPressedTime = Time.time;
        }

        bool wantsToRun = Input.GetKey(GameOptionsStore.GetBinding(options, GameAction.Run)) && moveDirection.sqrMagnitude > 0.01f && !aiming;
        bool isRunning = wantsToRun && Stats.ConsumeStamina(staminaDrainPerSecond * Time.deltaTime);
        if (!isRunning)
        {
            Stats.RegenerateStamina(staminaRecoverPerSecond * Time.deltaTime);
        }

        if (Time.time - lastGroundedTime <= coyoteTime && Time.time - lastJumpPressedTime <= jumpBufferTime)
        {
            verticalVelocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);
            lastJumpPressedTime = -99f;
            lastGroundedTime = -99f;
        }

        float speed = walkSpeed * (isRunning ? runMultiplier : 1f) * (aiming ? 0.78f : 1f);
        verticalVelocity.y += gravity * Time.deltaTime;

        Vector3 desiredVelocity = moveDirection * speed + impactVelocity + Vector3.up * verticalVelocity.y;
        CollisionFlags collisionFlags = characterController.Move(desiredVelocity * Time.deltaTime);

        if ((collisionFlags & CollisionFlags.Below) != 0)
        {
            lastGroundedTime = Time.time;
            if (verticalVelocity.y < 0f)
            {
                verticalVelocity.y = -groundedStickVelocity;
            }
        }

        impactVelocity = Vector3.Lerp(impactVelocity, Vector3.zero, impactDamping * Time.deltaTime);
        lastMoveMagnitude = moveDirection.magnitude * (isRunning ? 1.3f : 1f);
        lastRunning = isRunning;
    }

    private void UpdateInteraction()
    {
        currentInteractable = null;
        if (Physics.Raycast(playerCamera.transform.position, playerCamera.transform.forward, out RaycastHit hit, interactRange, ~0, QueryTriggerInteraction.Collide))
        {
            currentInteractable = hit.collider.GetComponentInParent<IInteractable>();
        }

        if (currentInteractable != null)
        {
            UpdateInteractionPrompt(currentInteractable.GetPrompt(this));
            if (Input.GetKeyDown(GameOptionsStore.GetBinding(GameManager.Instance.CurrentOptions, GameAction.Interact)))
            {
                currentInteractable.Interact(this);
            }
        }
        else
        {
            UpdateInteractionPrompt(null);
        }
    }

    private void UpdateWeapons()
    {
        aiming = Input.GetMouseButton(1);
        UpdateAimingFov();

        if (Input.GetMouseButton(0))
        {
            WeaponSystem.TriggerCurrent(this);
        }

        if (Input.GetKeyDown(GameOptionsStore.GetBinding(GameManager.Instance.CurrentOptions, GameAction.Reload)))
        {
            WeaponSystem.Reload();
        }

        if (Mathf.Abs(Input.mouseScrollDelta.y) > 0.01f)
        {
            int direction = Input.mouseScrollDelta.y > 0f ? 1 : -1;
            int nextIndex = (WeaponSystem.CurrentIndex + direction + WeaponSystem.SlotCount) % WeaponSystem.SlotCount;
            WeaponSystem.SelectSlot(nextIndex);
        }

        KeyCode[] weaponKeys =
        {
            KeyCode.Alpha1, KeyCode.Alpha2, KeyCode.Alpha3, KeyCode.Alpha4, KeyCode.Alpha5,
            KeyCode.Alpha6, KeyCode.Alpha7, KeyCode.Alpha8, KeyCode.Alpha9
        };
        for (int i = 0; i < weaponKeys.Length; i++)
        {
            if (Input.GetKeyDown(weaponKeys[i]))
            {
                WeaponSystem.SelectSlot(i);
            }
        }
    }

    private void UpdateAimingFov()
    {
        if (playerCamera == null)
        {
            return;
        }

        float targetFov = aiming ? baseFieldOfView - aimZoomFovDelta : baseFieldOfView;
        playerCamera.fieldOfView = Mathf.Lerp(playerCamera.fieldOfView, targetFov, aimFovLerp * Time.unscaledDeltaTime);
    }

    private void UpdateInteractionPrompt(string prompt)
    {
        GameManager.Instance.SetInteractionPrompt(prompt);
    }

    private void UpdateHud()
    {
        GameManager.Instance.RefreshHud();
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
