using UnityEngine;

// First-party PRIVATE native test fixture: shipped only inside disposable QA archives.
namespace HPR.NestedCustomFixture
{
    public sealed class HprNestedCustomSample : MonoBehaviour
    {
        [SerializeField] private float authoredThreshold=1.25f;
        [SerializeField] private string privateSafetyLabel="original private field";
        public float speedLimit=2.5f;
        public int retries=3;

        public float AuthoredThreshold => authoredThreshold;
        public string PrivateSafetyLabel => privateSafetyLabel;
        public void SetForVariant(float weight, string label)
        {
            authoredThreshold=weight;
            privateSafetyLabel=label;
        }
    }
}
