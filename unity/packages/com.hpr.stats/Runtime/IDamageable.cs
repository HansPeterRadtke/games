using UnityEngine;

public interface IDamageable
{
    bool IsAlive { get; }
    void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection);
}
