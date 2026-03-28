using UnityEngine;

public class SaveDemoController : MonoBehaviour
{
    [SerializeField] private SaveDemoEntity entity;

    public void ValidateDemo()
    {
        if (entity == null)
        {
            throw new System.InvalidOperationException("Save demo is missing its test entity.");
        }

        entity.ConfigureState(7, 42f, true);
        entity.transform.position = new Vector3(1f, 2f, 3f);
        entity.transform.rotation = Quaternion.Euler(0f, 45f, 0f);

        SaveEntityData saved = entity.CaptureState();

        entity.ConfigureState(99, 0f, false);
        entity.transform.position = new Vector3(-4f, 1f, 8f);
        entity.transform.rotation = Quaternion.identity;

        entity.RestoreState(saved);

        if (entity.RuntimeValue != 7 || Mathf.Abs(entity.RuntimeHealth - 42f) > 0.01f)
        {
            throw new System.InvalidOperationException("Save demo restore did not recover value data.");
        }

        if ((entity.transform.position - new Vector3(1f, 2f, 3f)).sqrMagnitude > 0.0001f)
        {
            throw new System.InvalidOperationException("Save demo restore did not recover transform position.");
        }

        if (!entity.gameObject.activeSelf)
        {
            throw new System.InvalidOperationException("Save demo restore did not recover active state.");
        }
    }

    private void OnGUI()
    {
        if (entity == null)
        {
            GUI.Label(new Rect(20f, 20f, 420f, 24f), "Save demo is missing references.");
            return;
        }

        GUI.Label(new Rect(20f, 20f, 420f, 24f), $"Position: {entity.transform.position}");
        GUI.Label(new Rect(20f, 48f, 420f, 24f), $"Value: {entity.RuntimeValue}");
        GUI.Label(new Rect(20f, 76f, 420f, 24f), $"Health: {entity.RuntimeHealth:0.0}");
    }
}
