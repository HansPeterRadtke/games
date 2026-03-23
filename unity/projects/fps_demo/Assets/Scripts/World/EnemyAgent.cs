using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class EnemyAgent : MonoBehaviour, IDamageable, ISaveableEntity
{
    [SerializeField] private string saveId;
    [SerializeField] private float maxHealth = 65f;
    [SerializeField] private float moveSpeed = 2.7f;
    [SerializeField] private float chaseSpeed = 3.7f;
    [SerializeField] private float detectionRange = 12f;
    [SerializeField] private float attackRange = 1.9f;
    [SerializeField] private float attackDamage = 10f;
    [SerializeField] private float attackCooldown = 1.2f;
    [SerializeField] private Transform patrolA;
    [SerializeField] private Transform patrolB;

    private CharacterController controller;
    private float health;
    private float lastAttackTime;
    private bool patrolToA;

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
        if (distanceToPlayer <= detectionRange)
        {
            destination = player.transform.position;
            speed = chaseSpeed;
            if (distanceToPlayer <= attackRange && Time.time >= lastAttackTime + attackCooldown)
            {
                lastAttackTime = Time.time;
                player.Stats.ApplyDamage(attackDamage, player.transform.position, (player.transform.position - transform.position).normalized);
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
        if (move.sqrMagnitude > 0.05f)
        {
            Vector3 direction = move.normalized;
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), 8f * Time.deltaTime);
            controller.Move(direction * speed * Time.deltaTime + Vector3.down * 4f * Time.deltaTime);
        }
    }

    public void Configure(string id, Transform waypointA, Transform waypointB)
    {
        saveId = id;
        patrolA = waypointA;
        patrolB = waypointB;
    }

    public void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        if (!IsAlive)
        {
            return;
        }

        health = Mathf.Max(0f, health - amount);
        GameManager.Instance?.NotifyStatus($"Enemy {saveId} hp {health:0}");
        if (health <= 0f)
        {
            gameObject.SetActive(false);
        }
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
        controller.enabled = false;
        transform.position = data.position.ToVector3();
        transform.rotation = data.rotation.ToQuaternion();
        controller.enabled = true;
    }
}
