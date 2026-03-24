using UnityEngine;

public interface IEnemyBehavior
{
    void Tick(EnemyAgent agent, IPlayerActor player, bool canSeePlayer, float distanceToPlayer);
}

public static class EnemyBehaviorFactory
{
    public static IEnemyBehavior Create(EnemyAIType aiType)
    {
        switch (aiType)
        {
            case EnemyAIType.StationaryAttack:
                return new StationaryAttackBehavior();
            case EnemyAIType.AggressiveChase:
                return new AggressiveChaseBehavior();
            default:
                return new PatrolChaseBehavior();
        }
    }
}

public sealed class PatrolChaseBehavior : IEnemyBehavior
{
    public void Tick(EnemyAgent agent, IPlayerActor player, bool canSeePlayer, float distanceToPlayer)
    {
        EnemyData data = agent.Data;
        if (player == null || data == null)
        {
            return;
        }

        if (distanceToPlayer <= data.ChaseRange && canSeePlayer)
        {
            float speed = Mathf.Max(data.MoveSpeed, data.ChaseSpeed);
            Vector3 destination = player.ActorTransform.position;

            if (data.AttackStyle == EnemyAttackStyle.Ranged && distanceToPlayer > data.AttackRange * 1.15f)
            {
                float rangeDelta = distanceToPlayer - data.PreferredRange;
                Vector3 toPlayer = (player.ActorTransform.position - agent.transform.position).normalized;
                Vector3 strafe = Vector3.Cross(Vector3.up, toPlayer) * Mathf.Sin(Time.time * 1.8f + agent.transform.position.x);
                destination = agent.transform.position + toPlayer * Mathf.Clamp(rangeDelta, -2f, 2f) + strafe * 1.6f;
            }

            agent.MoveTowards(destination, speed);
            agent.TryAttack(player, distanceToPlayer);
            return;
        }

        Transform patrolTarget = agent.GetCurrentPatrolTarget();
        if (patrolTarget == null)
        {
            return;
        }

        agent.MoveTowards(patrolTarget.position, data.MoveSpeed);
        agent.AdvancePatrolIfNeeded(patrolTarget.position);
    }
}

public sealed class StationaryAttackBehavior : IEnemyBehavior
{
    public void Tick(EnemyAgent agent, IPlayerActor player, bool canSeePlayer, float distanceToPlayer)
    {
        if (player == null || agent.Data == null)
        {
            return;
        }

        if (!canSeePlayer || distanceToPlayer > agent.Data.ChaseRange)
        {
            agent.MoveTowards(agent.transform.position, 0f);
            return;
        }

        agent.Face(player.ActorTransform.position);
        agent.TryAttack(player, distanceToPlayer);
    }
}

public sealed class AggressiveChaseBehavior : IEnemyBehavior
{
    private const float OrbitDistance = 1.35f;

    public void Tick(EnemyAgent agent, IPlayerActor player, bool canSeePlayer, float distanceToPlayer)
    {
        EnemyData data = agent.Data;
        if (player == null || data == null)
        {
            return;
        }

        if (!canSeePlayer)
        {
            Transform patrolTarget = agent.GetCurrentPatrolTarget();
            if (patrolTarget != null)
            {
                agent.MoveTowards(patrolTarget.position, data.MoveSpeed);
                agent.AdvancePatrolIfNeeded(patrolTarget.position);
            }
            return;
        }

        Vector3 toPlayer = (player.ActorTransform.position - agent.transform.position);
        Vector3 chasePoint = player.ActorTransform.position;
        if (data.AttackStyle == EnemyAttackStyle.Ranged && distanceToPlayer < data.PreferredRange)
        {
            Vector3 fallback = agent.transform.position - toPlayer.normalized * OrbitDistance;
            Vector3 orbit = Vector3.Cross(Vector3.up, toPlayer.normalized) * Mathf.Sin(Time.time * 2.4f + agent.transform.position.z) * OrbitDistance;
            chasePoint = fallback + orbit;
        }

        agent.MoveTowards(chasePoint, Mathf.Max(data.MoveSpeed, data.ChaseSpeed));
        agent.TryAttack(player, distanceToPlayer);
    }
}
