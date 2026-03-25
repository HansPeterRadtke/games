using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class EnemyAgent : MonoBehaviour, IDamageable, IImpactReceiver, ISaveableEntity
{
    private const string AutoVisualName = "__AutoVisual";
    private const float GravityPull = 4f;
    private const float RotationLerpSpeed = 8f;
    private const float ImpactDamping = 7f;
    private const float PatrolArrivalDistance = 0.5f;

    [SerializeField] private string saveId;
    [SerializeField] private EnemyData enemyData;
    [SerializeField] private Transform patrolA;
    [SerializeField] private Transform patrolB;
    [SerializeField] private Transform muzzle;

    private CharacterController controller;
    private float health;
    private float lastAttackTime;
    private bool patrolToA;
    private Vector3 impactVelocity;
    private IEnemyBehavior behavior;
    private IGameEventBus eventBus;

    public string SaveId => saveId;
    public bool IsAlive => health > 0f;
    public float Health => health;
    public EnemyData Data => enemyData;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
        health = enemyData != null ? enemyData.MaxHealth : 0f;
        behavior = EnemyBehaviorFactory.Create(enemyData != null ? enemyData.AIType : EnemyAIType.PatrolChase);
        RefreshPresentation();
    }

    private void Start()
    {
        BindEventBus(GameManager.Instance != null ? GameManager.Instance.EventBus : null);
    }

    private void OnEnable()
    {
        GameManager.Instance?.RegisterEnemy(this);
    }

    private void OnDisable()
    {
        GameManager.Instance?.UnregisterEnemy(this);
        BindEventBus(null);
    }

    private void Update()
    {
        if (!IsAlive || enemyData == null || GameManager.Instance == null || !GameManager.Instance.IsGameplayRunning)
        {
            return;
        }

        IPlayerActor player = GameManager.Instance.Player;
        if (player == null)
        {
            return;
        }

        float distanceToPlayer = Vector3.Distance(transform.position, player.ActorTransform.position);
        bool canSeePlayer = HasLineOfSight(player);
        behavior?.Tick(this, player, canSeePlayer, distanceToPlayer);
    }

    public void Configure(string id, EnemyData data, Transform waypointA, Transform waypointB, Transform projectileMuzzle)
    {
        saveId = id;
        enemyData = data;
        patrolA = waypointA;
        patrolB = waypointB;
        muzzle = projectileMuzzle;
        health = enemyData != null ? enemyData.MaxHealth : 0f;
        behavior = EnemyBehaviorFactory.Create(enemyData != null ? enemyData.AIType : EnemyAIType.PatrolChase);
        RefreshPresentation();
    }

    public void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        if (!IsAlive)
        {
            return;
        }

        health = Mathf.Max(0f, health - amount);
        GameManager.Instance?.NotifyStatus($"{(enemyData != null ? enemyData.DisplayName : saveId)} hp {health:0}");
        if (health > 0f)
        {
            return;
        }

        GameManager.Instance?.EventBus?.Publish(new EnemyKilledEvent
        {
            SourceRoot = null,
            EnemyRoot = gameObject,
            EnemyId = saveId,
            EnemyData = enemyData
        });
        gameObject.SetActive(false);
    }

    public void ApplyImpact(Vector3 impulse, Vector3 point)
    {
        impactVelocity += impulse;
    }

    public SaveEntityData CaptureState()
    {
        return new SaveEntityData
        {
            id = saveId,
            active = gameObject.activeSelf,
            health = health,
            position = new SerializableVector3(transform.position),
            rotation = new SerializableQuaternion(transform.rotation),
            boolValue = patrolToA
        };
    }

    public void RestoreState(SaveEntityData data)
    {
        gameObject.SetActive(data.active);
        health = data.health;
        patrolToA = data.boolValue;
        impactVelocity = Vector3.zero;
        controller.enabled = false;
        transform.position = data.position.ToVector3();
        transform.rotation = data.rotation.ToQuaternion();
        controller.enabled = true;
    }

    public Transform GetCurrentPatrolTarget()
    {
        return patrolToA ? patrolA : patrolB;
    }

    public void AdvancePatrolIfNeeded(Vector3 patrolTargetPosition)
    {
        if (Vector3.Distance(transform.position, patrolTargetPosition) <= PatrolArrivalDistance)
        {
            patrolToA = !patrolToA;
        }
    }

    public void Face(Vector3 position)
    {
        Vector3 direction = position - transform.position;
        direction.y = 0f;
        if (direction.sqrMagnitude <= 0.001f)
        {
            return;
        }

        transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction.normalized), RotationLerpSpeed * Time.deltaTime);
    }

    public void MoveTowards(Vector3 destination, float speed)
    {
        Vector3 move = destination - transform.position;
        move.y = 0f;
        Vector3 planarImpact = new Vector3(impactVelocity.x, 0f, impactVelocity.z);
        if (move.sqrMagnitude > 0.05f || planarImpact.sqrMagnitude > 0.02f)
        {
            Vector3 direction = move.sqrMagnitude > 0.05f ? move.normalized : planarImpact.normalized;
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), RotationLerpSpeed * Time.deltaTime);
            controller.Move((direction * speed + impactVelocity + Vector3.down * GravityPull) * Time.deltaTime);
        }
        else
        {
            controller.Move((impactVelocity + Vector3.down * GravityPull) * Time.deltaTime);
        }

        impactVelocity = Vector3.Lerp(impactVelocity, Vector3.zero, ImpactDamping * Time.deltaTime);
    }

    public void TryAttack(IPlayerActor player, float distanceToPlayer)
    {
        if (player == null || enemyData == null || GameManager.Instance == null || !GameManager.Instance.IsCombatLive)
        {
            return;
        }

        if (Time.time < lastAttackTime + enemyData.AttackCooldown)
        {
            return;
        }

        lastAttackTime = Time.time;
        if (distanceToPlayer <= enemyData.AttackRange)
        {
            Vector3 direction = (player.ActorTransform.position - transform.position).normalized;
            GameManager.Instance.EventBus?.Publish(new DamageEvent
            {
                SourceRoot = gameObject,
                TargetRoot = player.ActorTransform.gameObject,
                Amount = enemyData.AttackDamage,
                HitPoint = player.ActorTransform.position,
                HitDirection = direction
            });
            GameManager.Instance.EventBus?.Publish(new ImpactEvent
            {
                SourceRoot = gameObject,
                TargetRoot = player.ActorTransform.gameObject,
                Impulse = direction * Mathf.Clamp(enemyData.AttackDamage * 0.18f, 1.2f, 6.5f),
                HitPoint = player.ActorTransform.position
            });
            return;
        }

        if (enemyData.AttackStyle == EnemyAttackStyle.Ranged)
        {
            FireProjectile(player);
        }
    }

    private bool HasLineOfSight(IPlayerActor player)
    {
        Vector3 origin = transform.position + Vector3.up * 1.15f;
        Vector3 target = player.ActorTransform.position + Vector3.up * 0.9f;
        if (!Physics.Linecast(origin, target, out RaycastHit hit, ~0, QueryTriggerInteraction.Ignore))
        {
            return true;
        }

        return hit.transform.root == player.ActorTransform;
    }

    private void FireProjectile(IPlayerActor player)
    {
        Vector3 origin = muzzle != null ? muzzle.position : transform.position + Vector3.up * 1.15f;
        Vector3 direction = ((player.ActorTransform.position + Vector3.up * 0.8f) - origin).normalized;

        GameObject projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        projectile.name = saveId + "_Projectile";
        projectile.transform.position = origin;
        projectile.transform.localScale = Vector3.one * 0.12f;
        Renderer renderer = projectile.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.sharedMaterial = new Material(Shader.Find("Standard"))
            {
                color = enemyData.AttackStyle == EnemyAttackStyle.Ranged ? new Color(0.95f, 0.42f, 0.22f) : new Color(0.9f, 0.9f, 0.2f)
            };
        }

        Rigidbody rigidbody = projectile.AddComponent<Rigidbody>();
        rigidbody.useGravity = false;
        rigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        rigidbody.mass = 0.08f;

        PhysicsProjectile behaviour = projectile.AddComponent<PhysicsProjectile>();
        behaviour.Configure(transform, direction, enemyData.AttackDamage, enemyData.ProjectileSpeed, enemyData.ProjectileImpact, 4f, 0f, renderer != null ? renderer.sharedMaterial.color : Color.red);
    }

    private void RefreshPresentation()
    {
        Transform autoVisual = transform.Find(AutoVisualName);
        if (autoVisual != null)
        {
            DestroyUnityObject(autoVisual.gameObject);
        }

        GameObject customVisual = enemyData != null ? enemyData.VisualPrefab : null;
        foreach (Renderer renderer in GetComponentsInChildren<Renderer>(true))
        {
            if (renderer.transform != autoVisual)
            {
                renderer.enabled = customVisual == null || renderer.transform == transform.Find("Muzzle");
            }
        }

        if (customVisual == null)
        {
            return;
        }

        GameObject visual = Instantiate(customVisual, transform);
        visual.name = AutoVisualName;
        visual.transform.localPosition = enemyData.VisualLocalPosition;
        visual.transform.localEulerAngles = enemyData.VisualLocalEuler;
        visual.transform.localScale = enemyData.VisualLocalScale;

        foreach (MonoBehaviour behaviourComponent in visual.GetComponentsInChildren<MonoBehaviour>(true))
        {
            DestroyUnityObject(behaviourComponent);
        }

        foreach (Rigidbody rigidbody in visual.GetComponentsInChildren<Rigidbody>(true))
        {
            DestroyUnityObject(rigidbody);
        }

        foreach (Collider collider in visual.GetComponentsInChildren<Collider>(true))
        {
            DestroyUnityObject(collider);
        }
    }

    private void BindEventBus(IGameEventBus bus)
    {
        if (eventBus == bus)
        {
            return;
        }

        if (eventBus != null)
        {
            eventBus.Unsubscribe<DamageEvent>(HandleDamageEvent);
            eventBus.Unsubscribe<ImpactEvent>(HandleImpactEvent);
        }

        eventBus = bus;
        if (eventBus != null)
        {
            eventBus.Subscribe<DamageEvent>(HandleDamageEvent);
            eventBus.Subscribe<ImpactEvent>(HandleImpactEvent);
        }
    }

    private void HandleDamageEvent(DamageEvent gameEvent)
    {
        if (gameEvent == null || gameEvent.TargetRoot != gameObject)
        {
            return;
        }

        ApplyDamage(gameEvent.Amount, gameEvent.HitPoint, gameEvent.HitDirection);
    }

    private void HandleImpactEvent(ImpactEvent gameEvent)
    {
        if (gameEvent == null || gameEvent.TargetRoot != gameObject)
        {
            return;
        }

        ApplyImpact(gameEvent.Impulse, gameEvent.HitPoint);
    }

    private static void DestroyUnityObject(Object target)
    {
        if (target == null)
        {
            return;
        }

        if (Application.isPlaying)
        {
            Destroy(target);
        }
        else
        {
            DestroyImmediate(target);
        }
    }
}
