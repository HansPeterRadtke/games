using UnityEngine;

public interface IInteractable
{
    string GetPrompt(PlayerController player);
    void Interact(PlayerController player);
}

public interface IDamageable
{
    bool IsAlive { get; }
    void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection);
}

public interface IImpactReceiver
{
    void ApplyImpact(Vector3 impulse, Vector3 point);
}

public interface ISaveableEntity
{
    string SaveId { get; }
    SaveEntityData CaptureState();
    void RestoreState(SaveEntityData data);
}
