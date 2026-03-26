using UnityEngine;

[CreateAssetMenu(menuName = "HPR/AI/Enemy", fileName = "EnemyData")]
public class EnemyData : ScriptableObject
{
    public string Id;
    public string DisplayName;
    public EnemyAIType AIType = EnemyAIType.PatrolChase;
    public float MaxHealth;
    public float MoveSpeed;
    public float ChaseRange;
    public float AttackRange;
    public float AttackDamage;
    public float AttackCooldown;
    public EnemyAttackStyle AttackStyle = EnemyAttackStyle.Melee;
    public float ChaseSpeed;
    public float ProjectileSpeed = 28f;
    public float ProjectileImpact = 7f;
    public float PreferredRange = 7.5f;
    public GameObject VisualPrefab;
    public Vector3 VisualLocalPosition;
    public Vector3 VisualLocalEuler;
    public Vector3 VisualLocalScale = Vector3.one;
}
