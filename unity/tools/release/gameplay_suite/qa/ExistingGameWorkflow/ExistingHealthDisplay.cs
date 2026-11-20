// Representative existing HUD data binding; visual appearance is not certified by headless QA.
using UnityEngine;
namespace ExistingGameWorkflow
{
    public sealed class ExistingHealthDisplay : MonoBehaviour
    {
        [SerializeField] private ExistingGameVitals source;
        public float DisplayedHealth { get; private set; }
        public void Configure(ExistingGameVitals value) { Unsubscribe(); source = value; Subscribe(); }
        private void OnEnable() { Subscribe(); }
        private void OnDisable() { Unsubscribe(); }
        private void Subscribe() { if (source != null) { source.Changed -= Refresh; source.Changed += Refresh; Refresh(); } }
        private void Unsubscribe() { if (source != null) source.Changed -= Refresh; }
        private void Refresh() { DisplayedHealth = source.Health; }
        private void OnGUI() { GUI.Label(new Rect(10, 10, 240, 30), "Existing health: " + DisplayedHealth); }
    }
}
