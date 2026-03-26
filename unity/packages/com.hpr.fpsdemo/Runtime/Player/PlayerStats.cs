using System.Linq;
using UnityEngine;

public class PlayerStats : ActorStatsComponent, IPlayerStats
{
    [SerializeField] private MonoBehaviour servicesBehaviour;

    private IStatusMessageSink statusSink;
    private IPlayerDeathHandler playerDeathHandler;

    protected override void Awake()
    {
        servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IEventBusSource || component is IStatusMessageSink || component is IPlayerDeathHandler);
        statusSink = servicesBehaviour as IStatusMessageSink;
        playerDeathHandler = servicesBehaviour as IPlayerDeathHandler;
        BindRuntimeEventBusSource(servicesBehaviour);
    }

    public void BindRuntimeServices(MonoBehaviour services)
    {
        servicesBehaviour = services;
        statusSink = servicesBehaviour as IStatusMessageSink;
        playerDeathHandler = servicesBehaviour as IPlayerDeathHandler;
        BindRuntimeEventBusSource(servicesBehaviour);
    }

    protected override void OnDamageApplied(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        statusSink?.NotifyStatus($"Player hit: -{amount:0}");
    }

    protected override void OnDied(Vector3 hitPoint, Vector3 hitDirection)
    {
        playerDeathHandler?.HandlePlayerDeath();
    }
}
