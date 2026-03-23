using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class EnemyAgent : MonoBehaviour, IDamageable, IImpactReceiver, ISaveableEntity
{
    [SerializeField] private string saveId;
    [SerializeField] private float maxHealth = 65f;
    [SerializeField] private float moveSpeed = 2.7f;
    [SerializeField] private float chaseSpeed = 3.7f;
    [SerializeField] private float detectionRange = 15f;
    [SerializeField] private float attackRange = 1.9f;
    [SerializeField] private float attackDamage = 12f;
    [SerializeField] private float attackCooldown = 1.2f;
    [SerializeField] private float projectileDamage = 8f;
    [SerializeField] private float projectileSpeed = 28f;
    [SerializeField] private float projectileImpact = 7f;
    [SerializeField] private float preferredRange = 7.5f;
    [SerializeField] private bool rangedAttacker = true;
    [SerializeField] private Transform patrolA;
    [SerializeField] private Transform patrolB;
    [SerializeField] private Transform muzzle;

    private CharacterController controller;
    private float health;
    private float lastAttackTime;
    private bool patrolToA;
    private Vector3 impactVelocity;

    public string SaveId => saveId;
    public bool IsAlive => health > 0f;
    public float Health => health;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
        health = maxHealth;
    }

    private void Update()
    {
        if (!IsAlive || GameManager.Instance == null || !GameManager.Instance.IsGameplayRunning)
        {
            return;
        }

        var player = GameManager.Instance.Player;
        if (player == null)
        {
            return;
        }

        Vector3 destination;
        float speed;
        float distanceToPlayer = Vector3.Distance(transform.position, player.transform.position);
        bool canSeePlayer = HasLineOfSight(player);

        if (distanceToPlayer <= detectionRange && canSeePlayer)
        {
            speed = chaseSpeed;
            destination = player.transform.position;

            if (rangedAttacker && distanceToPlayer > attackRange * 1.15f)
            {
                float rangeDelta = distanceToPlayer - preferredRange;
                Vector3 toPlayer = (player.transform.position - transform.position).normalized;
                Vector3 strafe = Vector3.Cross(Vector3.up, toPlayer) * Mathf.Sin(Time.time * 1.8f + transform.position.x);
                destination = transform.position + toPlayer * Mathf.Clamp(rangeDelta, -2f, 2f) + strafe * 1.6f;
            }

            if (GameManager.Instance.IsCombatLive && Time.time >= lastAttackTime + attackCooldown)
            {
                lastAttackTime = Time.time;
                if (distanceToPlayer <= attackRange)
                {
                    Vector3 direction = (player.transform.position - transform.position).normalized;
                    player.Stats.ApplyDamage(attackDamage, player.transform.position, direction);
                }
                else if (rangedAttacker)
                {
                    FireProjectile(player);
                }
            }
        }
        else
        {
            var patrolTarget = patrolToA ? patrolA : patrolB;
            if (patrolTarget == null)
            {
                return;
            }

            destination = patrolTarget.position;
            speed = moveSpeed;
            if (Vector3.Distance(transform.position, patrolTarget.position) <= 0.5f)
            {
                patrolToA = !patrolToA;
            }
        }

        Vector3 move = destination - transform.position;
        move.y = 0f;
        Vector3 planarImpact = new Vector3(impactVelocity.x, 0f, impactVelocity.z);
        if (move.sqrMagnitude > 0.05f || planarImpact.sqrMagnitude > 0.02f)
        {
            Vector3 direction = move.sqrMagnitude > 0.05f ? move.normalized : planarImpact.normalized;
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 8f * Time.deltaTime);
            controller.Move((direction * speed + impactVelocity + Vector3.down * 4f) * Time.deltaTime);
        }
        else
        {
            controller.Move((impactVelocity + Vector3.down * 4f) * Time.deltaTime);
        }

        impactVelocity = Vector3.Lerp(impactVelocity, Vector3.zero, 7f * Time.deltaTime);
    }

    public void Configure(string id, Transform waypointA, Transform waypointB, Transform projectileMuzzle, bool useRanged)
    {
        saveId = id;
        patrolA = waypointA;
        patrolB = waypointB;
        muzzle = projectileMuzzle;
        rangedAttacker = useRanged;
    }

    public void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        if (!IsAlive)
        {
            return;
        }

        health = Mathf.Max(0f, health - amount);
        ApplyImpact(hitDirection.normalized * Mathf.Clamp(amount * 0.22f, 1f, 5.5f), hitPoint);
        GameManager.Instance?.NotifyStatus($"Enemy {saveId} hp {health:0}");
        if (health <= 0f)
        {
            gameObject.SetActive(false);
        }
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

    private bool HasLineOfSight(PlayerController player)
    {
        Vector3 origin = transform.position + Vector3.up * 1.15f;
        Vector3 target = player.transform.position + Vector3.up * 0.9f;
        if (!Physics.Linecast(origin, target, out RaycastHit hit, ~0, QueryTriggerInteraction.Ignore))
        {
            return true;
        }

        return hit.transform.root == player.transform;
    }

    private void FireProjectile(PlayerController player)
    {
        Vector3 origin = muzzle != null ? muzzle.position : transform.position + Vector3.up * 1.15f;
        Vector3 direction = ((player.transform.position + Vector3.up * 0.8f) - origin).normalized;

        var projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        projectile.name = $"{saveId}_Projectile";
        projectile.transform.position = origin;
        projectile.transform.localScale = Vector3.one * 0.12f;
        var renderer = projectile.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.sharedMaterial = new Material(Shader.Find("Standard"))
            {
                color = rangedAttacker ? new Color(0.95f, 0.42f, 0.22f) : new Color(0.9f, 0.9f, 0.2f)
            };
        }

        var rigidbody = projectile.AddComponent<Rigidbody>();
        rigidbody.useGravity = false;
        rigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        rigidbody.mass = 0.08f;

        var behaviour = projectile.AddComponent<PhysicsProjectile>();
        behaviour.Configure(transform, direction, projectileDamage, projectileSpeed, projectileImpact, 4f, 0f, renderer != null ? renderer.sharedMaterial.color : Color.red);
    }
}
