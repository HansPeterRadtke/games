using UnityEngine;

namespace HPR
{
    [DisallowMultipleComponent]
    public class SaveDemoEntity : MonoBehaviour, ISaveableEntity
    {
        [SerializeField] private string saveId = "save_demo_entity";
        [SerializeField] private int runtimeValue = 3;
        [SerializeField] private float runtimeHealth = 15f;

        public string SaveId => saveId;
        public int RuntimeValue => runtimeValue;
        public float RuntimeHealth => runtimeHealth;

        public void ConfigureState(int value, float health, bool active)
        {
            runtimeValue = value;
            runtimeHealth = health;
            gameObject.SetActive(active);
        }

        public SaveEntityData CaptureState()
        {
            return new SaveEntityData
            {
                id = saveId,
                active = gameObject.activeSelf,
                intValue = runtimeValue,
                health = runtimeHealth,
                position = new SerializableVector3(transform.position),
                rotation = new SerializableQuaternion(transform.rotation)
            };
        }

        public void RestoreState(SaveEntityData data)
        {
            if (data == null)
            {
                return;
            }

            runtimeValue = data.intValue;
            runtimeHealth = data.health;
            transform.position = data.position.ToVector3();
            transform.rotation = data.rotation.ToQuaternion();
            gameObject.SetActive(data.active);
        }
    }
}
