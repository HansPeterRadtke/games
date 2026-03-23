using UnityEngine;

public class MapCameraFollow : MonoBehaviour
{
    [SerializeField] private Transform target;
    [SerializeField] private float height = 48f;

    public void SetTarget(Transform followTarget)
    {
        target = followTarget;
    }

    private void LateUpdate()
    {
        if (target == null)
        {
            return;
        }

        transform.position = new Vector3(target.position.x, height, target.position.z);
        transform.rotation = Quaternion.Euler(90f, 0f, 0f);
    }
}
