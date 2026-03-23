using UnityEngine;

[CreateAssetMenu(menuName = "FPS Demo/Data/Enemy", fileName = "EnemyData")]
public class EnemyData : ScriptableObject
{
    public string Id;
    public string DisplayName;
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
}
