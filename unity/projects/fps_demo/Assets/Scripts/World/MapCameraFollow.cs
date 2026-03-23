using UnityEngine;

public class MapCameraFollow : MonoBehaviour
{
    [SerializeField] private Transform target;
    [SerializeField] private float height = 48f;
    [SerializeField] private float minZoom = 14f;
    [SerializeField] private float maxZoom = 36f;
    [SerializeField] private float panSpeed = 0.9f;
    [SerializeField] private float zoomStep = 2.6f;

    private Vector2 panOffset;
    private Camera mapCamera;

    private void Awake()
    {
        mapCamera = GetComponent<Camera>();
    }

    public void SetTarget(Transform followTarget)
    {
        target = followTarget;
    }

    public void ResetView()
    {
        panOffset = Vector2.zero;
        if (mapCamera != null)
        {
            mapCamera.orthographicSize = 26f;
        }
    }

    public void Pan(Vector2 mouseDelta)
    {
        if (mapCamera == null)
        {
            return;
        }

        float scale = mapCamera.orthographicSize / 22f;
        panOffset += new Vector2(-mouseDelta.x, -mouseDelta.y) * panSpeed * scale;
    }

    public void Zoom(float mouseWheel)
    {
        if (mapCamera == null)
        {
            return;
        }

        mapCamera.orthographicSize = Mathf.Clamp(mapCamera.orthographicSize - mouseWheel * zoomStep, minZoom, maxZoom);
    }

    private void LateUpdate()
    {
        if (target == null)
        {
            return;
        }

        transform.position = new Vector3(target.position.x + panOffset.x, height, target.position.z + panOffset.y);
        transform.rotation = Quaternion.Euler(90f, 0f, 0f);
    }
}
