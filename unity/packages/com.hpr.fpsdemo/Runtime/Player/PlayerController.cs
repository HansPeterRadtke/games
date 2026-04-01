using System.Linq;
using UnityEngine;

namespace HPR
{
    [RequireComponent(typeof(CharacterController))]
    public class PlayerController : MonoBehaviour, IImpactReceiver
    {
        [SerializeField] private float walkSpeed = 5.5f;
        [SerializeField] private float runMultiplier = 1.8f;
        [SerializeField] private float gravity = -24f;
        [SerializeField] private float jumpHeight = 1.25f;
        [SerializeField] private float staminaDrainPerSecond = 24f;
        [SerializeField] private float staminaRecoverPerSecond = 18f;
        [SerializeField] private float coyoteTime = 0.14f;
        [SerializeField] private float jumpBufferTime = 0.16f;
        [SerializeField] private float groundedStickVelocity = 4f;
        [SerializeField] private float impactDamping = 8f;
        [SerializeField] private MonoBehaviour servicesBehaviour;
        [SerializeField] private MonoBehaviour inputSourceBehaviour;

        private CharacterController characterController;
        private Camera playerCamera;
        private Light flashlight;
        private IPlayerStats stats;
        private Vector3 verticalVelocity;
        private Vector3 impactVelocity;
        private float yaw;
        private float pitch;
        private float baseFieldOfView;
        private float lastGroundedTime = -99f;
        private float lastJumpPressedTime = -99f;
        private IEventBus eventBus;
        private IGameplayStateSource gameplayState;
        private IInputBindingsSource inputBindings;
        private IEventBusSource eventBusSource;
        private IInputSource inputSource;
        private float externalMoveSpeedMultiplier = 1f;

        public Camera PlayerCamera => playerCamera;
        public Light Flashlight => flashlight;
        public float Pitch => pitch;
        public float Yaw => yaw;
        public float BaseFieldOfView => baseFieldOfView;
        public float LastMoveMagnitude { get; private set; }
        public bool IsRunning { get; private set; }
        public bool IsAiming { get; private set; }

        private void Awake()
        {
            characterController = GetComponent<CharacterController>();
            stats = GetComponent<PlayerStats>();
            playerCamera = GetComponentInChildren<Camera>();
            flashlight = GetComponentInChildren<Light>(true);
            servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : FindBehaviourImplementing<IGameplayStateSource>();
            inputSourceBehaviour = inputSourceBehaviour != null ? inputSourceBehaviour : GetComponents<MonoBehaviour>().FirstOrDefault(component => component is IInputSource);
            gameplayState = ResolveInterface<IGameplayStateSource>(servicesBehaviour);
            inputBindings = ResolveInterface<IInputBindingsSource>(servicesBehaviour);
            eventBusSource = ResolveInterface<IEventBusSource>(servicesBehaviour);
            inputSource = ResolveInterface<IInputSource>(inputSourceBehaviour);
            yaw = transform.eulerAngles.y;
            pitch = playerCamera.transform.localEulerAngles.x;
            if (pitch > 180f)
            {
                pitch -= 360f;
            }
        }

        private void Start()
        {
            if (inputBindings != null)
            {
                ApplyOptions(inputBindings.CurrentOptions);
            }

            if (eventBusSource != null)
            {
                BindEventBus(eventBusSource.EventBus);
            }
        }

        private void OnDestroy()
        {
            BindEventBus(null);
        }

        private void Update()
        {
            if (gameplayState == null || inputBindings == null || inputSource == null)
            {
                return;
            }

            if (gameplayState.IsMapVisible || !gameplayState.AllowsGameplayInput)
            {
                LastMoveMagnitude = 0f;
                IsRunning = false;
                return;
            }

            UpdateLook();
            UpdateMovement();
        }

        public void SetAiming(bool aiming)
        {
            IsAiming = aiming;
        }

        public void BindRuntimeServices(MonoBehaviour services, MonoBehaviour inputBehaviour)
        {
            servicesBehaviour = services;
            inputSourceBehaviour = inputBehaviour;
            gameplayState = ResolveInterface<IGameplayStateSource>(servicesBehaviour);
            inputBindings = ResolveInterface<IInputBindingsSource>(servicesBehaviour);
            eventBusSource = ResolveInterface<IEventBusSource>(servicesBehaviour);
            inputSource = ResolveInterface<IInputSource>(inputSourceBehaviour);
            if (inputBindings != null)
            {
                ApplyOptions(inputBindings.CurrentOptions);
            }
            BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
        }

        public void ApplyOptions(GameOptionsData options)
        {
            GameOptionsStore.Apply(options, playerCamera);
            baseFieldOfView = options.fieldOfView;
        }

        public PlayerSaveData CaptureTransformSaveData()
        {
            return new PlayerSaveData
            {
                position = new SerializableVector3(transform.position),
                yaw = yaw,
                pitch = pitch
            };
        }

        public void RestoreTransformFromSave(PlayerSaveData saveData)
        {
            characterController.enabled = false;
            transform.position = saveData.position.ToVector3();
            yaw = saveData.yaw;
            pitch = saveData.pitch;
            transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            playerCamera.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
            characterController.enabled = true;

            verticalVelocity = Vector3.zero;
            impactVelocity = Vector3.zero;
            lastGroundedTime = Time.time;
        }

        public void ApplyImpact(Vector3 impulse, Vector3 point)
        {
            impactVelocity += impulse;
        }

        public void SetExternalMoveSpeedMultiplier(float multiplier)
        {
            externalMoveSpeedMultiplier = Mathf.Max(0.25f, multiplier);
        }

        private void UpdateLook()
        {
            var options = inputBindings.CurrentOptions;
            float mouseX = inputSource.GetAxisRaw("Mouse X") * options.lookSensitivity;
            float mouseY = inputSource.GetAxisRaw("Mouse Y") * options.lookSensitivity * (options.invertY ? 1f : -1f);

            yaw += mouseX;
            pitch = Mathf.Clamp(pitch + mouseY, -85f, 85f);

            transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            playerCamera.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
        }

        private void UpdateMovement()
        {
            var options = inputBindings.CurrentOptions;
            Vector3 moveDirection = Vector3.zero;
            if (inputSource.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveForward))) moveDirection += transform.forward;
            if (inputSource.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveBackward))) moveDirection -= transform.forward;
            if (inputSource.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveRight))) moveDirection += transform.right;
            if (inputSource.GetKey(GameOptionsStore.GetBinding(options, GameAction.MoveLeft))) moveDirection -= transform.right;
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

            if (inputSource.GetKeyDown(GameOptionsStore.GetBinding(options, GameAction.Jump)))
            {
                lastJumpPressedTime = Time.time;
            }

            bool wantsToRun = inputSource.GetKey(GameOptionsStore.GetBinding(options, GameAction.Run)) && moveDirection.sqrMagnitude > 0.01f && !IsAiming;
            bool canConsumeStamina = stats != null && stats.ConsumeStamina(staminaDrainPerSecond * Time.deltaTime);
            IsRunning = wantsToRun && canConsumeStamina;
            if (!IsRunning)
            {
                stats?.RegenerateStamina(staminaRecoverPerSecond * Time.deltaTime);
            }

            if (Time.time - lastGroundedTime <= coyoteTime && Time.time - lastJumpPressedTime <= jumpBufferTime)
            {
                verticalVelocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);
                lastJumpPressedTime = -99f;
                lastGroundedTime = -99f;
            }

            float speed = walkSpeed * externalMoveSpeedMultiplier * (IsRunning ? runMultiplier : 1f) * (IsAiming ? 0.78f : 1f);
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
            LastMoveMagnitude = moveDirection.magnitude * (IsRunning ? 1.3f : 1f);
        }

        private void BindEventBus(IEventBus bus)
        {
            if (eventBus == bus)
            {
                return;
            }

            if (eventBus != null)
            {
                eventBus.Unsubscribe<ImpactEvent>(HandleImpactEvent);
            }

            eventBus = bus;
            if (eventBus != null)
            {
                eventBus.Subscribe<ImpactEvent>(HandleImpactEvent);
            }
        }

        private void HandleImpactEvent(ImpactEvent gameEvent)
        {
            if (gameEvent == null || gameEvent.TargetRoot != gameObject)
            {
                return;
            }

            ApplyImpact(gameEvent.Impulse, gameEvent.HitPoint);
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
