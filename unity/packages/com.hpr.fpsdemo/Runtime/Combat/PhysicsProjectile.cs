using UnityEngine;

public class PhysicsProjectile : MonoBehaviour
{
    [SerializeField] private float damage = 10f;
    [SerializeField] private float impactForce = 16f;
    [SerializeField] private float speed = 40f;
    [SerializeField] private float lifetime = 4f;
    [SerializeField] private float explosiveRadius;
    [SerializeField] private LayerMask damageMask = ~0;

    private Transform ownerRoot;
    private Rigidbody body;
    private Collider projectileCollider;
    private bool armed;

    public void Configure(
        Transform owner,
        Vector3 direction,
        float damageAmount,
        float projectileSpeed,
        float projectileImpactForce,
        float timeToLive,
        float radius,
        Color color)
    {
        ownerRoot = owner;
        damage = damageAmount;
        speed = projectileSpeed;
        impactForce = projectileImpactForce;
        lifetime = timeToLive;
        explosiveRadius = radius;

        var renderer = GetComponentInChildren<Renderer>();
        if (renderer != null)
        {
            renderer.sharedMaterial = new Material(Shader.Find("Standard"))
            {
                color = color
            };
        }

        body = GetComponent<Rigidbody>();
        projectileCollider = GetComponent<Collider>();
        if (body != null)
        {
            body.linearVelocity = direction.normalized * speed;
        }

        if (ownerRoot != null && projectileCollider != null)
        {
            foreach (var ownerCollider in ownerRoot.GetComponentsInChildren<Collider>())
            {
                Physics.IgnoreCollision(projectileCollider, ownerCollider, true);
            }
        }

        armed = true;
        Destroy(gameObject, lifetime);
    }

    private void OnCollisionEnter(Collision collision)
    {
        if (!armed)
        {
            return;
        }

        if (collision.collider != null && ownerRoot != null && collision.collider.transform.root == ownerRoot)
        {
            return;
        }

        Vector3 hitPoint = collision.contactCount > 0 ? collision.GetContact(0).point : transform.position;
        Vector3 hitDirection = body != null && body.linearVelocity.sqrMagnitude > 0.01f
            ? body.linearVelocity.normalized
            : transform.forward;

        if (explosiveRadius > 0.01f)
        {
            ApplyExplosion(hitPoint);
        }
        else
        {
            ApplySingleHit(collision.collider, hitPoint, hitDirection, damage, impactForce);
        }

        armed = false;
        Destroy(gameObject);
    }

    private void ApplyExplosion(Vector3 center)
    {
        foreach (var collider in Physics.OverlapSphere(center, explosiveRadius, damageMask, QueryTriggerInteraction.Ignore))
        {
            if (ownerRoot != null && collider.transform.root == ownerRoot)
            {
                continue;
            }

            Vector3 offset = collider.bounds.ClosestPoint(center) - center;
            Vector3 direction = offset.sqrMagnitude > 0.001f ? offset.normalized : Vector3.up;
            float distance = Mathf.Max(0.1f, offset.magnitude);
            float falloff = 1f - Mathf.Clamp01(distance / explosiveRadius);
            ApplySingleHit(collider, center, direction, damage * falloff, impactForce * falloff * 1.4f);
        }
    }

    private static void ApplySingleHit(Collider targetCollider, Vector3 point, Vector3 direction, float damageAmount, float impact)
    {
        if (targetCollider == null)
        {
            return;
        }

        if (targetCollider.attachedRigidbody != null && !targetCollider.attachedRigidbody.isKinematic)
        {
            targetCollider.attachedRigidbody.AddForceAtPosition(direction * impact, point, ForceMode.Impulse);
        }

        if (targetCollider.GetComponentInParent<IImpactReceiver>() is { } impactReceiver)
        {
            impactReceiver.ApplyImpact(direction * impact, point);
        }

        if (targetCollider.GetComponentInParent<IDamageable>() is { } damageable)
        {
            damageable.ApplyDamage(damageAmount, point, direction);
        }
    }
}
